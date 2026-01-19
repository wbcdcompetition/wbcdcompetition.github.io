#!/usr/bin/env python3
import cv2
import sys
import argparse
from pathlib import Path

def extract_thumbnail(video_path, output_path):
    print(f"Extracting thumbnail from {video_path} to {output_path}")
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return
    
    ret, frame = cap.read()
    if ret:
        # Create parent directory if not exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), frame)
        print("Success")
    else:
        print("Error: Could not read frame")
    cap.release()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract thumbnails from Lumos session videos.")
    parser.add_argument("input_dir", type=Path, help="Directory containing session folders (e.g. WBCD DataDemo)")
    parser.add_argument("output_dir", type=Path, help="Directory to save extracted thumbnails")
    args = parser.parse_args()

    base_path = args.input_dir
    
    tasks = [
        ("task1/session_001/left_hand_250801DR48FP25005932/RGB_Images/video.mp4", "lumos_task1.jpg"),
        ("task2/session_001/left_hand_250801DR48FP25005932/RGB_Images/video.mp4", "lumos_task2.jpg")
    ]
    
    if not base_path.exists():
        print(f"Error: Input directory {base_path} does not exist.")
        sys.exit(1)

    for relative_video_path, relative_output_name in tasks:
        # Try to find the file somewhat flexibly or strictly? Keeping strict for now based on known structure
        video_path = base_path / relative_video_path
        output_path = args.output_dir / relative_output_name
        
        if not video_path.exists():
             print(f"Warning: Video not found at {video_path}")
             continue
             
        extract_thumbnail(video_path, output_path)
