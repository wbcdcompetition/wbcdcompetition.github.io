#!/usr/bin/env python3
import cv2
import sys
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
    base_path = Path("/Users/xiaohan/wbcdcompetition.github.io/umi-gallery-dist/WBCD DataDemo")
    
    tasks = [
        ("task1/session_001/left_hand_250801DR48FP25005932/RGB_Images/video.mp4", "public/thumbnails/lumos_task1.jpg"),
        ("task2/session_001/left_hand_250801DR48FP25005932/RGB_Images/video.mp4", "public/thumbnails/lumos_task2.jpg")
    ]
    
    for relative_video_path, relative_output_path in tasks:
        video_path = base_path / relative_video_path
        output_path = Path("/Users/xiaohan/wbcdcompetition.github.io/umi-gallery") / relative_output_path
        extract_thumbnail(video_path, output_path)
