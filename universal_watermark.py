import subprocess, os, uuid

def add_text_watermark(input_path: str, text: str, start=2):
    out = input_path.replace(".mp4", f"_wm_{uuid.uuid4().hex[:6]}.mp4")

    vf = (
        "drawtext="
        f"text='{text}':"
        "fontcolor=white@0.32:"
        "fontsize=w*0.045:"
        "x=w-tw-0.03*w:"
        "y=h-th-0.05*h:"
        f"enable='gte(t,{start})'"
    )

    cmd = [
        "ffmpeg","-y","-i",input_path,
        "-vf",vf,
        "-c:v","libx264","-preset","fast","-crf","18",
        "-c:a","copy",
        "-map_metadata","-1",
        out
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(input_path)
    return out
