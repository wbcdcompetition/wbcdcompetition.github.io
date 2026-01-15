#!/usr/bin/env python3
"""
Custom MCAP to RRD converter for UMI robotics data.
Extracts supported data types and logs them to Rerun format.

The standard `rerun mcap convert` fails on these files because:
- foxglove.RobotInfo has a custom `inputs` field (list of structs) that 
  Rerun's generic protobuf converter can't decode properly.

This script manually extracts:
- CompressedImage (camera feeds)
- PoseInFrame (end-effector poses)
- IMUMeasurement (IMU data)

And skips problematic channels like RobotInfo and SystemInfo.
"""
import sys
import os
from pathlib import Path
from mcap.reader import make_reader
from mcap_protobuf.decoder import DecoderFactory
import rerun as rr
import numpy as np

# Channels to skip (these cause the conversion to fail)
SKIP_CHANNELS = [
    "/robot0/sim/robot_info",
    "/robot1/sim/robot_info", 
    "/robot0/system_info",
    "/robot1/system_info",
]

def convert_mcap_to_rrd(mcap_path: str, output_path: str = None):
    """Convert an MCAP file to RRD format, skipping problematic channels."""
    
    mcap_path = Path(mcap_path)
    if output_path is None:
        output_path = mcap_path.with_suffix('.rrd')
    else:
        output_path = Path(output_path)
    
    print(f"Converting: {mcap_path}")
    print(f"Output: {output_path}")
    
    # Initialize Rerun recording
    rr.init(mcap_path.stem, spawn=False)
    rr.save(str(output_path))
    
    with open(mcap_path, "rb") as f:
        reader = make_reader(f, decoder_factories=[DecoderFactory()])
        
        msg_count = 0
        skipped_count = 0
        logged_by_type = {}
        
        for schema, channel, message, decoded_msg in reader.iter_decoded_messages():
            # Skip problematic channels
            if channel.topic in SKIP_CHANNELS:
                skipped_count += 1
                continue
            
            # Convert timestamp (nanoseconds to seconds)
            time_ns = message.log_time
            time_s = time_ns / 1e9
            rr.set_time_seconds("timestamp", time_s)
            
            schema_name = schema.name if schema else "unknown"
            
            try:
                if "CompressedImage" in schema_name:
                    # Log compressed image
                    log_compressed_image(channel.topic, decoded_msg)
                    logged_by_type["CompressedImage"] = logged_by_type.get("CompressedImage", 0) + 1
                    
                elif "PoseInFrame" in schema_name:
                    # Log pose
                    log_pose(channel.topic, decoded_msg)
                    logged_by_type["PoseInFrame"] = logged_by_type.get("PoseInFrame", 0) + 1
                    
                elif "IMUMeasurement" in schema_name:
                    # Log IMU data
                    log_imu(channel.topic, decoded_msg)
                    logged_by_type["IMUMeasurement"] = logged_by_type.get("IMUMeasurement", 0) + 1
                    
                elif "CameraCalibration" in schema_name:
                    # Log camera info (just once typically)
                    log_camera_calibration(channel.topic, decoded_msg)
                    logged_by_type["CameraCalibration"] = logged_by_type.get("CameraCalibration", 0) + 1
                    
                elif "MagneticEncoderMeasurement" in schema_name:
                    # Log encoder as scalar
                    log_encoder(channel.topic, decoded_msg)
                    logged_by_type["MagneticEncoderMeasurement"] = logged_by_type.get("MagneticEncoderMeasurement", 0) + 1
                    
                else:
                    # Skip unknown types silently
                    pass
                    
                msg_count += 1
                
                if msg_count % 5000 == 0:
                    print(f"  Processed {msg_count} messages...")
                    
            except Exception as e:
                # Silently skip errors to avoid spam
                continue
    
    print(f"\nConversion complete!")
    print(f"  Total logged: {msg_count}")
    print(f"  Skipped (problematic): {skipped_count}")
    print(f"  By type: {logged_by_type}")
    print(f"  Output: {output_path}")
    
    return str(output_path)
# Track which entities have been initialized with VideoStream codec
VIDEO_STREAM_INITIALIZED = set()

def log_compressed_image(topic: str, msg):
    """Log a compressed image/video to Rerun.
    
    Handles both:
    - JPEG/PNG images (using EncodedImage)
    - H.264 video frames (using VideoStream)
    """
    # Extract image data
    data = bytes(msg.data)
    format_str = msg.format if hasattr(msg, 'format') else ""
    
    # Convert topic to entity path
    entity_path = topic.replace("/", "/").lstrip("/")
    
    # Check if it's H.264 video
    if format_str == 'h264' or data[:4] == b'\x00\x00\x00\x01':
        # H.264 NAL unit - use VideoStream
        global VIDEO_STREAM_INITIALIZED
        
        if entity_path not in VIDEO_STREAM_INITIALIZED:
            # First frame: initialize with codec, no sample yet
            rr.log(entity_path, rr.VideoStream(codec=rr.VideoCodec.H264))
            VIDEO_STREAM_INITIALIZED.add(entity_path)
        
        # Log the H.264 frame data as a sample
        rr.log(entity_path, rr.VideoStream(codec=rr.VideoCodec.H264, sample=data))
        
    elif data[:2] == b'\xff\xd8':
        # JPEG magic bytes
        rr.log(entity_path, rr.EncodedImage(contents=data, media_type="image/jpeg"))
        
    elif data[:8] == b'\x89PNG\r\n\x1a\n':
        # PNG magic bytes
        rr.log(entity_path, rr.EncodedImage(contents=data, media_type="image/png"))
        
    else:
        # Try as JPEG by default (some formats don't have proper magic)
        rr.log(entity_path, rr.EncodedImage(contents=data, media_type="image/jpeg"))


def log_pose(topic: str, msg):
    """Log a pose to Rerun as a transform and 3D trajectory point."""
    entity_path = topic.replace("/", "/").lstrip("/")
    
    # Extract position and orientation from the pose
    if hasattr(msg, 'pose'):
        pose = msg.pose
        if hasattr(pose, 'position') and hasattr(pose, 'orientation'):
            pos = pose.position
            rot = pose.orientation
            
            position = [pos.x, pos.y, pos.z]
            quaternion = [rot.x, rot.y, rot.z, rot.w]  # xyzw format
            
            # Log the transform (invisible, but sets coordinate system)
            rr.log(entity_path, rr.Transform3D(
                translation=position,
                rotation=rr.Quaternion(xyzw=quaternion)
            ))
            
            # Also log as a 3D point for trajectory visualization
            # Use a different path so it shows as a separate entity
            # Prefix with 'z' to make it appear last in the panel order
            trajectory_path = entity_path.replace("vio/eef_pose", "z_trajectory")
            rr.log(trajectory_path, rr.Points3D(
                positions=[position],
                radii=[0.005],  # 5mm radius
                colors=[[100, 200, 255]]  # Light blue
            ))


def log_imu(topic: str, msg):
    """Log IMU measurements to Rerun."""
    entity_path = topic.replace("/", "/").lstrip("/")
    
    # Log angular velocity and linear acceleration as scalar arrays
    if hasattr(msg, 'angular_velocity'):
        av = msg.angular_velocity
        magnitude = float(np.linalg.norm([av.x, av.y, av.z]))
        rr.log(f"{entity_path}/angular_velocity", rr.Scalars([magnitude]))
    
    if hasattr(msg, 'linear_acceleration'):
        la = msg.linear_acceleration
        magnitude = float(np.linalg.norm([la.x, la.y, la.z]))
        rr.log(f"{entity_path}/linear_acceleration", rr.Scalars([magnitude]))


def log_camera_calibration(topic: str, msg):
    """Log camera calibration info."""
    entity_path = topic.replace("/", "/").lstrip("/")
    
    # Just log as text annotation for now
    if hasattr(msg, 'width') and hasattr(msg, 'height'):
        rr.log(entity_path, rr.TextLog(f"Camera: {msg.width}x{msg.height}"))


def log_encoder(topic: str, msg):
    """Log magnetic encoder reading."""
    entity_path = topic.replace("/", "/").lstrip("/")
    
    if hasattr(msg, 'value'):
        rr.log(entity_path, rr.Scalars([float(msg.value)]))


def convert_all_mcap_files(input_dir: str, output_dir: str):
    """Convert all MCAP files in a directory."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    mcap_files = list(input_dir.glob("*.mcap"))
    print(f"Found {len(mcap_files)} MCAP files to convert\n")
    
    for mcap_file in mcap_files:
        output_file = output_dir / mcap_file.with_suffix('.rrd').name
        try:
            convert_mcap_to_rrd(str(mcap_file), str(output_file))
            print()
        except Exception as e:
            print(f"ERROR converting {mcap_file}: {e}")
            continue


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Default: convert all files in public/mcap to public/rrd
        convert_all_mcap_files("public/mcap", "public/rrd")
    elif len(sys.argv) == 2:
        # Single file
        convert_mcap_to_rrd(sys.argv[1])
    else:
        # Input and output specified
        convert_mcap_to_rrd(sys.argv[1], sys.argv[2])
