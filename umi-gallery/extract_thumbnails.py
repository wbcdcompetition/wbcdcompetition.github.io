#!/usr/bin/env python3
"""
Extract first camera frame from each MCAP file and save as JPEG thumbnail.
Since the camera data is H.264 encoded, we need to decode it using av (PyAV).
"""
import sys
from pathlib import Path
from mcap.reader import make_reader
from mcap_protobuf.decoder import DecoderFactory
import av
import io


def extract_thumbnail(mcap_path: str, output_dir: str = "public/thumbnails"):
    """Extract first camera frame and save as JPEG thumbnail."""
    mcap_path = Path(mcap_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / f"{mcap_path.stem}.jpg"
    print(f"Extracting thumbnail from: {mcap_path}")
    
    # Collect H.264 NAL units until we have a complete frame
    h264_data = bytearray()
    found_sps = False
    frame_count = 0
    
    with open(mcap_path, "rb") as f:
        reader = make_reader(f, decoder_factories=[DecoderFactory()])
        
        for schema, channel, message, decoded_msg in reader.iter_decoded_messages():
            if "CompressedImage" not in (schema.name if schema else ""):
                continue
            
            # Get format and data
            format_str = decoded_msg.format if hasattr(decoded_msg, 'format') else ""
            if format_str != 'h264':
                continue
            
            data = bytes(decoded_msg.data)
            
            # Check for SPS NAL unit (start of a keyframe sequence)
            # NAL type 7 = SPS, 8 = PPS, 5 = IDR (keyframe)
            if data[:4] == b'\x00\x00\x00\x01':
                nal_type = data[4] & 0x1F
                if nal_type == 7:  # SPS - Sequence Parameter Set
                    found_sps = True
                    h264_data = bytearray(data)
                elif found_sps and nal_type in [5, 8]:  # IDR frame or PPS
                    h264_data.extend(data)
                elif found_sps and nal_type == 5:  # IDR keyframe
                    h264_data.extend(data)
                    break
            
            frame_count += 1
            if frame_count > 100:  # Don't search forever
                break
    
    if not h264_data:
        print(f"  No H.264 keyframe found, trying first frame...")
        # Fall back to just using the first frame data
        with open(mcap_path, "rb") as f:
            reader = make_reader(f, decoder_factories=[DecoderFactory()])
            for schema, channel, message, decoded_msg in reader.iter_decoded_messages():
                if "CompressedImage" in (schema.name if schema else ""):
                    h264_data = bytes(decoded_msg.data)
                    break
    
    if not h264_data:
        print(f"  ERROR: No image data found")
        return None
    
    # Try to decode using PyAV
    try:
        # Create a memory buffer that looks like an H.264 stream
        # PyAV needs a container, so we'll try raw H.264 parsing
        container = av.open(io.BytesIO(bytes(h264_data)), format='h264')
        
        for frame in container.decode(video=0):
            # Convert to PIL Image and save as JPEG
            img = frame.to_image()
            img.save(str(output_path), 'JPEG', quality=85)
            print(f"  Saved: {output_path}")
            return str(output_path)
            
    except Exception as e:
        print(f"  PyAV decode failed: {e}")
        print(f"  Trying alternative method...")
        
        # Alternative: Try to find and extract any JPEG/PNG data that might exist
        # Some MCAP files might have mixed formats
        with open(mcap_path, "rb") as f:
            reader = make_reader(f, decoder_factories=[DecoderFactory()])
            for schema, channel, message, decoded_msg in reader.iter_decoded_messages():
                if "CompressedImage" not in (schema.name if schema else ""):
                    continue
                data = bytes(decoded_msg.data)
                # Check for JPEG
                if data[:2] == b'\xff\xd8':
                    with open(output_path, 'wb') as out:
                        out.write(data)
                    print(f"  Saved JPEG: {output_path}")
                    return str(output_path)
                # Check for PNG
                if data[:8] == b'\x89PNG\r\n\x1a\n':
                    png_path = output_path.with_suffix('.png')
                    with open(png_path, 'wb') as out:
                        out.write(data)
                    print(f"  Saved PNG: {png_path}")
                    return str(png_path)
    
    print(f"  Could not extract thumbnail")
    return None


def extract_all_thumbnails(input_dir: str = "public/mcap", output_dir: str = "public/thumbnails"):
    """Extract thumbnails from all MCAP files."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    mcap_files = list(input_dir.glob("*.mcap"))
    print(f"Found {len(mcap_files)} MCAP files\n")
    
    for mcap_file in mcap_files:
        try:
            extract_thumbnail(str(mcap_file), str(output_dir))
        except Exception as e:
            print(f"  ERROR: {e}")
        print()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        extract_all_thumbnails()
    else:
        extract_thumbnail(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "public/thumbnails")
