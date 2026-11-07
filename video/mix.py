"""旁白、配樂（旁白響時自動壓低）與音效混成一軌，輸出 -16 LUFS。"""
import json, os, subprocess, pathlib

ROOT = pathlib.Path(__file__).parent
tl = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))
sh = {s["id"]: s for s in tl["shots"]}
SFX = pathlib.Path(os.environ.get("SKYRIG_SFX", ROOT / "sfx"))  # 音效檔資料夾，檔名見下方 hits
S = lambda k: sh[k]["start"]
hits = [
    ("riser", S("heroB") - 1.2, -22),
    ("impact-bass-1", S("hook"), -14),
    ("whoosh", S("aiplan") - .2, -23),
    ("impact-bass-2", S("site") - .35, -17),
    ("whoosh", S("site") - .2, -22),
    ("whoosh-short", S("factory") - .1, -24),
    ("whoosh-short", S("rig") - .1, -24),
    ("whoosh-short", S("scale") - .1, -24),
    ("whoosh-short", S("deck") - .1, -24),
    ("whoosh-short", S("street") - .1, -24),
    ("whoosh", S("storm") - .2, -22),
    ("whoosh-short", S("fitout") - .1, -24),
    ("impact-bass-2", S("finale") + .1, -17),
    ("whoosh-short", S("neighbor") - .1, -24),
    ("whoosh-cinematic", S("end") - .4, -22),
]
args = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(ROOT / "vo" / "voice.wav"), "-i", str(ROOT / "vo" / "music.wav")]
f = []
for i, (name, at, db) in enumerate(hits):
    args += ["-i", str(SFX / f"{name}.mp3")]
    f.append(f"[{i + 2}:a]aresample=48000,aformat=channel_layouts=stereo,volume={db}dB,adelay={int(at * 1000)}:all=1[s{i}]")
f.append("[0:a]asplit=2[vo][key]")
f.append("[1:a]volume=-17dB[m0]")
f.append("[m0][key]sidechaincompress=threshold=0.03:ratio=5:attack=40:release=520:makeup=1[m1]")
inputs = "[vo][m1]" + "".join(f"[s{i}]" for i in range(len(hits)))
f.append(f"{inputs}amix=inputs={len(hits) + 2}:normalize=0:dropout_transition=0,atrim=0:{tl['total']},alimiter=limit=0.84:level=false,loudnorm=I=-16:TP=-1.5:LRA=9[out]")
subprocess.check_call(args + ["-filter_complex", ";".join(f), "-map", "[out]", "-ar", "48000", "-ac", "2", str(ROOT / "vo" / "mix.wav")])
print("mix ok")
