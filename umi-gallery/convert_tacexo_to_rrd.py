#!/usr/bin/env python3
"""
TacExo LeRobot to RRD converter for bimanual glove data.
Converts LeRobot v2.1 format to Rerun RRD files.

Features:
- JPEG compression for smaller RRD files
- Third-person camera view
- Left/right thumb tactile deformation visualization
- Finger joint state plots

Usage:
    python convert_tacexo_to_rrd.py source-data/tacexo_fold_towels
    python convert_tacexo_to_rrd.py source-data/tacexo_fold_towels --episode 0
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


def load_parquet_data(parquet_path: Path) -> dict:
    """Load parquet file and extract key columns."""
    table = pq.read_table(parquet_path)
    df = table.to_pandas()
    
    result = {
        "frame_index": df["frame_index"].values if "frame_index" in df.columns else None,
        "timestamp": df["timestamp"].values if "timestamp" in df.columns else None,
    }
    
    # Extract action and state (78-DOF for tacexo)
    if "action" in df.columns:
        actions = np.stack(df["action"].values)
        result["action"] = actions
    
    if "observation.state" in df.columns:
        states = np.stack(df["observation.state"].values)
        result["observation.state"] = states
    
    return result


def log_finger_data(data: dict, info: dict):
    """Log finger joint data as scalar timelines (subset of 78-DOF)."""
    
    # Get joint names from info
    all_names = info.get("features", {}).get("action", {}).get("names", [])
    
    # Filter to just finger joints (main_finger0 through main_finger35)
    finger_indices = []
    finger_names = []
    for i, name in enumerate(all_names):
        if name.startswith("main_finger"):
            finger_indices.append(i)
            finger_names.append(name)
    
    # Log a subset of finger joints (every 6th = 6 joints total, for cleaner plot)
    selected_indices = finger_indices[::6]  # finger0, 6, 12, 18, 24, 30
    selected_names = finger_names[::6]
    
    if "observation.state" in data and data["observation.state"] is not None:
        states = data["observation.state"]
        for idx, name in zip(selected_indices, selected_names):
            entity_path = f"fingers/{name.replace('main_', '')}"
            for frame_idx in range(len(states)):
                if data["timestamp"] is not None:
                    time_s = float(data["timestamp"][frame_idx])
                else:
                    time_s = frame_idx / 20.0  # TacExo uses 20fps
                
                rr.set_time("timestamp", timestamp=time_s)
                rr.set_time("frame", sequence=frame_idx)
                rr.log(entity_path, rr.Scalars(float(states[frame_idx, idx])))


def log_video_frames(video_path: Path, entity_path: str, fps: float = 20.0, jpeg_quality: int = 75):
    """Log video frames from MP4/MOV to Rerun as JPEG-encoded images."""
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
        
        # Encode as JPEG for compression
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
        _, jpeg_data = cv2.imencode('.jpg', frame, encode_params)
        
        # Log as encoded image with media type
        rr.log(entity_path, rr.EncodedImage(contents=jpeg_data.tobytes(), media_type="image/jpeg"))
        
        frame_idx += 1
        
        if frame_idx % 100 == 0:
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


def convert_episode(dataset_path: Path, episode_idx: int, output_dir: Path, info: dict, jpeg_quality: int = 75):
    """Convert a single episode to RRD format."""
    
    # Paths
    chunk_idx = episode_idx // info.get("chunks_size", 1000)
    parquet_path = dataset_path / f"data/chunk-{chunk_idx:03d}/episode_{episode_idx:06d}.parquet"
    
    video_base = dataset_path / f"videos/chunk-{chunk_idx:03d}"
    
    # Camera videos - third view is mp4, tactile deformation is mov
    cam_third_video = video_base / "observation.images.cam_third_view" / f"episode_{episode_idx:06d}.mp4"
    tactile_left_video = video_base / "observation.deformation.cam_left_hand_thumb_tactile" / f"episode_{episode_idx:06d}.mov"
    tactile_right_video = video_base / "observation.deformation.cam_right_hand_thumb_tactile" / f"episode_{episode_idx:06d}.mov"
    
    output_path = output_dir / f"tacexo_fold_towels_episode_{episode_idx}.rrd"
    
    print(f"\nConverting episode {episode_idx}")
    print(f"  Parquet: {parquet_path}")
    print(f"  Output: {output_path}")
    print(f"  JPEG quality: {jpeg_quality}")
    
    # Initialize Rerun
    rr.init(f"tacexo_fold_towels_episode_{episode_idx}", spawn=False)
    rr.save(str(output_path))
    
    fps = info.get("fps", 20)
    
    # Load and log parquet data (finger joints)
    if parquet_path.exists():
        print(f"  Loading parquet data...")
        data = load_parquet_data(parquet_path)
        num_frames = len(data.get("action", []))
        print(f"  Logging finger joint data ({num_frames} frames)...")
        log_finger_data(data, info)
    else:
        print(f"  Warning: Parquet not found: {parquet_path}")
    
    # Log camera videos
    print(f"  Processing cam_third_view video...")
    frames_third = log_video_frames(cam_third_video, "cameras/third_view", fps, jpeg_quality)
    print(f"    Total: {frames_third} frames")
    
    print(f"  Processing left_thumb_tactile video...")
    frames_left = log_video_frames(tactile_left_video, "tactile/left_thumb", fps, jpeg_quality)
    print(f"    Total: {frames_left} frames")
    
    print(f"  Processing right_thumb_tactile video...")
    frames_right = log_video_frames(tactile_right_video, "tactile/right_thumb", fps, jpeg_quality)
    print(f"    Total: {frames_right} frames")
    
    print(f"\n  Conversion complete: {output_path}")
    print(f"  File size: {output_path.stat().st_size / (1024*1024):.1f} MB")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Convert TacExo LeRobot data to Rerun RRD format")
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
    
    print(f"Robot: {info.get('robot_type', 'unknown')}")
    print(f"Total episodes: {info.get('total_episodes', 'N/A')}")
    print(f"Total frames: {info.get('total_frames', 'N/A')}")
    print(f"FPS: {info.get('fps', 20)}")
    
    # Convert specified episode
    rrd_path = convert_episode(dataset_path, args.episode, output_dir, info, args.jpeg_quality)
    
    # Extract thumbnail if requested
    if args.thumbnail:
        chunk_idx = args.episode // info.get("chunks_size", 1000)
        video_path = dataset_path / f"videos/chunk-{chunk_idx:03d}/observation.images.cam_third_view/episode_{args.episode:06d}.mp4"
        thumb_path = Path("public/thumbnails") / f"tacexo_fold_towels_episode_{args.episode}.jpg"
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        extract_thumbnail(video_path, thumb_path)
    
    print(f"\nDone! RRD file: {rrd_path}")


if __name__ == "__main__":
    main()
