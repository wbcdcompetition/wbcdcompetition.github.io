#!/usr/bin/env python3
"""
LeRobot to RRD converter for DM Robotics data.
Converts LeRobot v2.1 format (parquet + MP4) to Rerun RRD files.

Features:
- JPEG compression for smaller RRD files
- Multiple camera streams (top, wrist, tactile)
- Joint state/action plots

Usage:
    python convert_lerobot_to_rrd.py ../dm_insert
    python convert_lerobot_to_rrd.py ../dm_insert --episode 0
"""
import sys
import json
import argparse
from pathlib import Path
import numpy as np

try:
    import rerun as rr
    import pyarrow.parquet as pq
    import cv2
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install rerun-sdk pyarrow opencv-python pandas")
    sys.exit(1)


def load_dataset_info(dataset_path: Path) -> dict:
    """Load dataset metadata from info.json"""
    info_path = dataset_path / "meta" / "info.json"
    with open(info_path, "r") as f:
        return json.load(f)


def load_episodes(dataset_path: Path) -> list:
    """Load episode info from episodes.jsonl"""
    episodes_path = dataset_path / "meta" / "episodes.jsonl"
    episodes = []
    with open(episodes_path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                episodes.append(json.loads(line))
    return episodes


def load_parquet_data(parquet_path: Path) -> dict:
    """Load parquet file and extract key columns."""
    table = pq.read_table(parquet_path)
    df = table.to_pandas()
    
    result = {
        "frame_index": df["frame_index"].values if "frame_index" in df.columns else None,
        "timestamp": df["timestamp"].values if "timestamp" in df.columns else None,
    }
    
    # Extract action and state (8-DOF each)
    if "action" in df.columns:
        actions = np.stack(df["action"].values)
        result["action"] = actions
    
    if "observation.state" in df.columns:
        states = np.stack(df["observation.state"].values)
        result["observation.state"] = states
    
    return result


def log_joint_data(data: dict, joint_names: list):
    """Log joint state and action data as scalar timelines."""
    
    # Log observation.state (8 joints)
    if "observation.state" in data and data["observation.state"] is not None:
        states = data["observation.state"]
        for i, name in enumerate(joint_names):
            entity_path = f"observation/state/{name}"
            for frame_idx in range(len(states)):
                if data["timestamp"] is not None:
                    time_s = float(data["timestamp"][frame_idx])
                else:
                    time_s = frame_idx / 30.0
                
                rr.set_time("timestamp", timestamp=time_s)
                rr.set_time("frame", sequence=frame_idx)
                rr.log(entity_path, rr.Scalars(float(states[frame_idx, i])))
    
    # Log action (8 joints)
    if "action" in data and data["action"] is not None:
        actions = data["action"]
        for i, name in enumerate(joint_names):
            entity_path = f"action/{name}"
            for frame_idx in range(len(actions)):
                if data["timestamp"] is not None:
                    time_s = float(data["timestamp"][frame_idx])
                else:
                    time_s = frame_idx / 30.0
                
                rr.set_time("timestamp", timestamp=time_s)
                rr.set_time("frame", sequence=frame_idx)
                rr.log(entity_path, rr.Scalars(float(actions[frame_idx, i])))


def log_video_frames(video_path: Path, entity_path: str, fps: float = 30.0, jpeg_quality: int = 80):
    """Log video frames from MP4 to Rerun as JPEG-encoded images for smaller file size."""
    if not video_path.exists():
        print(f"  Warning: Video not found: {video_path}")
        return 0
    
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"  Warning: Could not open video: {video_path}")
        return 0
    
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        time_s = frame_idx / fps
        rr.set_time("timestamp", timestamp=time_s)
        rr.set_time("frame", sequence=frame_idx)
        
        # Encode as JPEG for compression (much smaller than raw)
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
        _, jpeg_data = cv2.imencode('.jpg', frame, encode_params)
        
        # Log as encoded image with media type
        rr.log(entity_path, rr.EncodedImage(contents=jpeg_data.tobytes(), media_type="image/jpeg"))
        
        frame_idx += 1
        
        if frame_idx % 200 == 0:
            print(f"    Logged {frame_idx} frames from {video_path.name}")
    
    cap.release()
    return frame_idx


def extract_thumbnail(video_path: Path, output_path: Path, frame_num: int = 30):
    """Extract a single frame from video as thumbnail."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"Warning: Could not open video for thumbnail: {video_path}")
        return False
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    ret, frame = cap.read()
    cap.release()
    
    if ret:
        cv2.imwrite(str(output_path), frame)
        print(f"  Saved thumbnail: {output_path}")
        return True
    return False


def convert_episode(dataset_path: Path, episode_idx: int, output_dir: Path, info: dict, jpeg_quality: int = 80):
    """Convert a single episode to RRD format."""
    
    # Paths
    chunk_idx = episode_idx // info.get("chunks_size", 1000)
    parquet_path = dataset_path / f"data/chunk-{chunk_idx:03d}/episode_{episode_idx:06d}.parquet"
    
    video_base = dataset_path / f"videos/chunk-{chunk_idx:03d}"
    
    # Camera video paths
    cam_top_video = video_base / "observation.images.cam_top" / f"episode_{episode_idx:06d}.mp4"
    cam_wrist_video = video_base / "observation.images.cam_right_wrist" / f"episode_{episode_idx:06d}.mp4"
    cam_tactile_video = video_base / "observation.images.cam_right_gripper_left_tactile" / f"episode_{episode_idx:06d}.mp4"
    
    output_path = output_dir / f"dm_insert_episode_{episode_idx}.rrd"
    
    print(f"\nConverting episode {episode_idx}")
    print(f"  Parquet: {parquet_path}")
    print(f"  Output: {output_path}")
    print(f"  JPEG quality: {jpeg_quality}")
    
    # Initialize Rerun
    rr.init(f"dm_insert_episode_{episode_idx}", spawn=False)
    rr.save(str(output_path))
    
    # Extract joint names from info
    joint_names = info.get("features", {}).get("action", {}).get("names", [
        "joint1", "joint2", "joint3", "joint4", "joint5", "joint6", "joint7", "gripper"
    ])
    
    fps = info.get("fps", 30)
    
    # Load and log parquet data (joint states/actions)
    if parquet_path.exists():
        print(f"  Loading parquet data...")
        data = load_parquet_data(parquet_path)
        print(f"  Logging joint data ({len(data.get('action', []))} frames)...")
        log_joint_data(data, joint_names)
    else:
        print(f"  Warning: Parquet not found: {parquet_path}")
    
    # Log camera videos
    print(f"  Processing cam_top video...")
    frames_top = log_video_frames(cam_top_video, "cameras/top", fps, jpeg_quality)
    print(f"    Total: {frames_top} frames")
    
    print(f"  Processing cam_wrist video...")
    frames_wrist = log_video_frames(cam_wrist_video, "cameras/wrist", fps, jpeg_quality)
    print(f"    Total: {frames_wrist} frames")
    
    print(f"  Processing cam_tactile video...")
    frames_tactile = log_video_frames(cam_tactile_video, "cameras/tactile", fps, jpeg_quality)
    print(f"    Total: {frames_tactile} frames")
    
    print(f"\n  Conversion complete: {output_path}")
    print(f"  File size: {output_path.stat().st_size / (1024*1024):.1f} MB")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Convert LeRobot data to Rerun RRD format")
    parser.add_argument("dataset_path", type=str, help="Path to LeRobot dataset directory")
    parser.add_argument("--episode", type=int, default=0, help="Episode index to convert (default: 0)")
    parser.add_argument("--output-dir", type=str, default="public/rrd", help="Output directory for RRD files")
    parser.add_argument("--thumbnail", action="store_true", help="Also extract thumbnail image")
    parser.add_argument("--jpeg-quality", type=int, default=75, help="JPEG quality 1-100 (default: 75)")
    args = parser.parse_args()
    
    dataset_path = Path(args.dataset_path).resolve()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Dataset: {dataset_path}")
    
    # Load metadata
    info = load_dataset_info(dataset_path)
    episodes = load_episodes(dataset_path)
    
    print(f"Robot: {info.get('robot_type', 'unknown')}")
    print(f"Total episodes: {info.get('total_episodes', len(episodes))}")
    print(f"Total frames: {info.get('total_frames', 'N/A')}")
    print(f"FPS: {info.get('fps', 30)}")
    
    # Convert specified episode
    rrd_path = convert_episode(dataset_path, args.episode, output_dir, info, args.jpeg_quality)
    
    # Extract thumbnail if requested
    if args.thumbnail:
        chunk_idx = args.episode // info.get("chunks_size", 1000)
        video_path = dataset_path / f"videos/chunk-{chunk_idx:03d}/observation.images.cam_top/episode_{args.episode:06d}.mp4"
        thumb_path = Path("public/thumbnails") / f"dm_insert_episode_{args.episode}.jpg"
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        extract_thumbnail(video_path, thumb_path)
    
    print(f"\nDone! RRD file: {rrd_path}")


if __name__ == "__main__":
    main()
