import subprocess
import os

def convert_video_to_webm(input_path: str, output_path: str) -> bool:
    os.makedirs("temp", exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-ss", "0",
        "-t", "3",
        "-vf", "fps=30,scale=512:512:force_original_aspect_ratio=decrease,pad=512:512:(ow-iw)/2:(oh-ih)/2:color=0x00000000",
        "-c:v", "libvpx-vp9",
        "-b:v", "256K",
        "-pix_fmt", "yuva420p",
        "-an",
        "-auto-alt-ref", "0",
        output_path
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return os.path.exists(output_path)
    except Exception as e:
        print(f"FFmpeg error: {e}")
        return False
