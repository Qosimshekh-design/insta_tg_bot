FFMPEG = "ffmpeg.exe"
import subprocess, os, uuid

def uniquify_video_hard(input_path: str) -> str:
    out = input_path.replace(".mp4", f"_uniq_{uuid.uuid4().hex[:6]}.mp4")

    vf = (
        "scale=iw*1.035:ih*1.035,"
        "crop=iw/1.035:ih/1.035:2:2,"
        "eq=brightness=0.015:contrast=1.03:saturation=1.01,"
        "noise=alls=8:allf=t+u"
    )

    cmd = [
    FFMPEG,
    "-y",
    "-i", input_path,
    ...
]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(input_path)
    return out
