#!/usr/bin/env python3
"""
Convert Lumos data to Rerun (.rrd) format.
Usage: python3 convert_lumos_to_rrd.py <session_path> <output_path>
"""

import sys
import os
import argparse
import pandas as pd
import numpy as np
import cv2
import rerun as rr
import rerun.blueprint as rrb
from pathlib import Path

def convert_lumos_to_rrd(session_path: Path, output_path: Path):
    print(f"Converting session: {session_path}")
    print(f"Output to: {output_path}")

    # Initialize Rerun
    rr.init(session_path.name, spawn=False)
    rr.save(str(output_path))
    
    # Define and send Blueprint
    blueprint = rrb.Blueprint(
        rrb.Vertical(
            rrb.Spatial3DView(name="3D Trajectory", origin="world"),
            rrb.Horizontal(
                rrb.Spatial2DView(name="Left Camera", origin="world/left_hand/camera"),
                rrb.Spatial2DView(name="Right Camera", origin="world/right_hand/camera"),
            ),
            row_shares=[2, 1]
        )
    )
    rr.send_blueprint(blueprint)

    # Define paths
    # Find the hand directory (assuming 'left_hand_*' or similar)
    hand_dirs = list(session_path.glob("*_hand_*"))
    if not hand_dirs:
        print(f"Error: No hand directory found in {session_path}")
        return
    
    for hand_dir in hand_dirs:
        # Determine hand name for namespacing (e.g., 'left_hand', 'right_hand')
        # Assuming directory name contains 'left_hand' or 'right_hand'
        hand_name = "left_hand" if "left_hand" in hand_dir.name else "right_hand"
        if "right_hand" not in hand_dir.name and "left_hand" not in hand_dir.name:
             # Fallback or use full name
             hand_name = hand_dir.name
        
        print(f"Processing hand: {hand_name} (Directory: {hand_dir.name})")

        traj_file = hand_dir / "Merged_Trajectory" / "merged_trajectory.txt"
        clamp_file = hand_dir / "Clamp_Data" / "clamp_data_tum.txt"
        video_path = hand_dir / "RGB_Images"
        video_file = video_path / "video.mp4"
        timestamps_file = video_path / "timestamps.csv"

        # Load Data
        # 1. Trajectory (Timestamp, tx, ty, tz, qx, qy, qz, qw)
        print(f"  Loading trajectory for {hand_name}...")
        if traj_file.exists():
            traj_data = pd.read_csv(traj_file, sep=" ", header=None, 
                                    names=["t", "tx", "ty", "tz", "qx", "qy", "qz", "qw"])
            # Log static trajectory path
            rr.log(f"world/{hand_name}/trajectory_path", rr.Points3D(
                positions=traj_data[["tx", "ty", "tz"]].values,
                colors=[[100, 100, 255]] * len(traj_data) if "left" in hand_name else [[255, 100, 100]] * len(traj_data),
                radii=[0.002] * len(traj_data)
            ), static=True)
            
            # Log Start Label
            start_pos = traj_data.iloc[0][["tx", "ty", "tz"]].values
            label_text = "Left Hand (Blue)" if "left" in hand_name else "Right Hand (Red)"
            rr.log(f"world/{hand_name}/start_label", rr.Points3D(
                positions=[start_pos],
                labels=[label_text],
                colors=[[100, 100, 255]] if "left" in hand_name else [[255, 100, 100]],
                radii=[0.01], 
            ), static=True)

            # Log dynamic pose
            for idx, row in traj_data.iterrows():
                rr.set_time_seconds("timestamp", row["t"])
                rr.log(f"world/{hand_name}/eef", rr.Transform3D(
                    translation=[row["tx"], row["ty"], row["tz"]],
                    rotation=rr.Quaternion(xyzw=[row["qx"], row["qy"], row["qz"], row["qw"]])
                ))
        else:
            print(f"  Warning: merged_trajectory.txt not found for {hand_name}")

        # 2. Clamp Data (Timestamp, width)
        # print(f"  Loading clamp data for {hand_name}...")
        # if clamp_file.exists():
        #    clamp_data = pd.read_csv(clamp_file, sep=" ", header=None, names=["t", "width"])
        #    for idx, row in clamp_data.iterrows():
        #        rr.set_time_seconds("timestamp", row["t"])
        #        # rr.log(f"world/{hand_name}/gripper/width", rr.Scalar(row["width"]))
        #        pass
        # else:
        #    # print(f"  Warning: clamp_data_tum.txt not found for {hand_name}")
        #    pass

        # 3. Video
        print(f"  Loading video for {hand_name}...")
        if video_file.exists() and timestamps_file.exists():
            video_timestamps = pd.read_csv(timestamps_file)
            cap = cv2.VideoCapture(str(video_file))
            
            frame_idx = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_idx < len(video_timestamps):
                    ts = video_timestamps.iloc[frame_idx]["header_stamp"]
                    rr.set_time_seconds("timestamp", ts)
                    
                    if "left" in hand_name:
                        # Translate camera visualization slightly if needed, or just log image
                        # For Rerun 2D image, we just log it. 
                        # If we want 3D camera frustum, we need calibration. 
                        # For now, just logging image to a separate entity.
                        pass
                    
                    # Compress to JPEG
                    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    rr.log(f"world/{hand_name}/camera", rr.Image(img_rgb).compress(jpeg_quality=80))
                
                frame_idx += 1
            cap.release()
        else:
            print(f"  Warning: Video or timestamps not found for {hand_name}")

    print("Conversion complete.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 convert_lumos_to_rrd.py <session_path> <output_path>")
        sys.exit(1)
    
    session_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    convert_lumos_to_rrd(session_path, output_path)
