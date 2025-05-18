import subprocess
import os

def convert_video_to_webm(input_path: str, output_path: str) -> bool:
    os.makedirs("temp", exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",                      # overwrite without asking
        "-i", input_path,          # input file
        "-ss", "0",                # start at 0s
        "-t", "3",                 # duration 3s
        "-vf", "scale=512:-1",     # resize to 512px wide (Telegram sticker size)
        "-c:v", "libvpx-vp9",      # VP9 codec (Telegram-compatible)
        "-b:v", "256K",            # bitrate
        "-an",                     # no audio
        output_path
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return os.path.exists(output_path)
    except Exception as e:
        print(f"FFmpeg error: {e}")
        return False
