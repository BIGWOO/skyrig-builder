import json, subprocess, pathlib

tl = json.load(open("timeline.json", encoding="utf-8"))
pathlib.Path("hf").mkdir(exist_ok=True)
for k in ("aiplan", "scale"):
    d = next(s["dur"] for s in tl["shots"] if s["id"] == k)
    subprocess.check_call(f"ffmpeg -y -hide_banner -loglevel error -f lavfi -i color=c=0x061220:s=1080x1920:r=30 -t {d} -c:v h264_nvenc -preset p6 -rc vbr -cq 16 -b:v 0 -pix_fmt yuv420p final/{k}.mp4".split())
lines = [f"file 'final/{s['id']}.mp4'" for s in tl["shots"]]
pathlib.Path("list.txt").write_text("\n".join(lines) + "\n")
subprocess.check_call("ffmpeg -y -hide_banner -loglevel error -f concat -i list.txt -c copy hf/footage.mp4".split())
d = float(subprocess.check_output("ffprobe -v error -show_entries format=duration -of csv=p=0 hf/footage.mp4".split()))
print("footage", d, "timeline", tl["total"])
s = {x["id"]: x for x in tl["shots"]}
at = [s[k]["start"] + s[k]["dur"] * .6 for k in ("heroB", "factory", "site2", "deck", "lowarm", "storm", "descend", "fitout", "neighbor")] + [s["finale"]["start"] + 1.2, s["finale"]["start"] + 8.5, s["twin"]["start"] + 7]
pathlib.Path("at.txt").write_text(",".join(f"{x:.2f}" for x in at))
