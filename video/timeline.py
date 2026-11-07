"""由旁白實際長度排出全片時間軸：鏡頭秒數、字幕、HUD，並處理語音。"""
import json, re, subprocess, pathlib

ROOT = pathlib.Path(__file__).parent
PROJ = ROOT
TEMPO = 1.08
PITCH = .94  # 約下移一個半音
lines = {l["id"]: l for l in json.loads((PROJ / "narration.json").read_text(encoding="utf-8"))}
raw = json.loads((ROOT / "voice" / "durations.json").read_text())
dur = {k: v / TEMPO for k, v in raw.items()}

# 鏡頭：[id, [行 id...], 開頭留白, 行距, 結尾留白]
PLAN = [
    ("idle", ["P1", "P2", "P3"], .3, .25, .35),
    ("heroB", ["P4"], .05, 0, .05),
    ("hook", ["P5"], .05, 0, .45),
    ("aiplan", ["A1"], .1, 0, .4),
    ("twin", ["A2"], .05, 0, .9),
    ("factory", ["F1"], .05, 0, .4),
    ("site", ["B1"], .1, 0, .15),
    ("site2", ["B2"], .05, 0, .8),
    ("rig", ["B3"], .05, 0, .3),
    ("scale", ["S1"], .1, 0, .5),
    ("deck", ["B4"], .05, 0, .3),
    ("night", ["B5"], .05, 0, .3),
    ("climb", ["B6"], .05, 0, .3),
    ("lowarm", ["B7"], .05, 0, .3),
    ("street", ["B8"], .05, 0, .4),
    ("storm", ["B9"], .05, 0, .3),
    ("descend", ["B10"], .05, 0, 1.4),
    ("fitout", ["B11"], .05, 0, .4),
    ("finale", ["E0", "E1"], .05, .25, .4),
    ("neighbor", ["R1"], .05, 0, .4),
    ("end", ["E2", "E3"], .2, .3, 2.4),
]

t = 0.0
shots, voice = [], []
for sid, ids, head, gap, tail in PLAN:
    s0 = t
    x = t + head
    for i, lid in enumerate(ids):
        voice.append({"id": lid, "start": round(x, 3), "dur": round(dur[lid], 3)})
        x += dur[lid] + (gap if i < len(ids) - 1 else 0)
    t = x + tail
    t = round(t * 30) / 30
    shots.append({"id": sid, "start": round(s0, 3), "dur": round(t - s0, 3)})
total = round(t, 3)


def split_text(text):
    """依標點切成每段 22 字內的字幕，保留句中標點以外的文字。"""
    parts = [p for p in re.split(r"(?<=[，。：、？])", text) if p]
    out, cur = [], ""
    for p in parts:
        if cur and len(cur) + len(p) > 20:
            out.append(cur); cur = p
        else:
            cur += p
    if cur:
        out.append(cur)
    return out


caps = []
for v in voice:
    segs = split_text(lines[v["id"]]["text"])
    n = sum(len(s) for s in segs)
    x = v["start"]
    for s in segs:
        d = v["dur"] * len(s) / n
        caps.append({"start": round(x, 3), "end": round(x + d, 3), "text": s.rstrip("，。、："), "line": v["id"]})
        x += d

data = {"total": total, "shots": shots, "voice": voice, "caps": caps, "siteSwitch": 0}
(ROOT / "timeline.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

p = ROOT / "shots.js"
src = p.read_text(encoding="utf-8")
auto = "const DUR = " + json.dumps({s["id"]: s["dur"] for s in shots}) + f", SW = {data['siteSwitch']}; // AUTO"
if "// AUTO" in src:
    src = re.sub(r"const DUR = .*// AUTO", auto, src)
else:
    src = src.replace("(() => {\n", "(() => {\n  " + auto + "\n", 1)
p.write_text(src, encoding="utf-8")

# 語音：提速不變調、補一點低頻厚度、輕壓縮，再依時間點鋪成一軌
tmp = ROOT / "vo"
tmp.mkdir(exist_ok=True)
args, filt = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"], []
for i, v in enumerate(voice):
    args += ["-i", str(ROOT / "voice" / f"{v['id']}.mp3")]
    ms = int(v["start"] * 1000)
    filt.append(f"[{i}:a]aresample=48000,asetrate=48000*{PITCH},aresample=48000,atempo={round(TEMPO / PITCH, 5)},adelay={ms}:all=1[a{i}]")
mix = "".join(f"[a{i}]" for i in range(len(voice)))
filt.append(f"{mix}amix=inputs={len(voice)}:normalize=0:dropout_transition=0,"
            "highpass=f=70,equalizer=f=160:t=q:w=1.1:g=3,equalizer=f=3200:t=q:w=1.4:g=1.5,"
            f"acompressor=threshold=-20dB:ratio=2.5:attack=8:release=160:makeup=2,apad=whole_dur={total},atrim=0:{total},"
            "loudnorm=I=-16:TP=-1.5:LRA=7[out]")
subprocess.check_call(args + ["-filter_complex", ";".join(filt), "-map", "[out]", "-ar", "48000", "-ac", "2", str(tmp / "voice.wav")])
print("total", total)
for s in shots:
    print(s)
print("captions", len(caps), "max chars", max(len(c["text"]) for c in caps))
