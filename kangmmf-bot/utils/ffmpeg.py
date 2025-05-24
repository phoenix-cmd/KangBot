import subprocess
import os

def convert_video_to_webm(input_path: str, output_path: str) -> bool:
    os.makedirs("temp", exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",                      # Overwrite output
        "-i", input_path,          # Input file
        "-ss", "0",                # Start time
        "-t", "3",                 # Max duration (3s)
        "-vf", "scale=trunc(min(512\,iw)/2)*2:trunc(min(512\,ih)/2)*2,setsar=1",  # Force even dimensions
        "-c:v", "libvpx-vp9",      # VP9 codec
        "-b:v", "512K",            # Bitrate
        "-pix_fmt", "yuva420p",    # Transparency support
        "-auto-alt-ref", "0",      # Disable alternate reference frames
        "-an",                     # No audio
        output_path
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return os.path.exists(output_path)
    except Exception as e:
        print(f"FFmpeg error: {e}")
        return False
