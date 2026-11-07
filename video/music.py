"""合成原創襯底：慢速和弦墊音加低頻脈動，段落強度跟著分鏡走。"""
import json, sys, wave
import numpy as np

SR = 48000
tl = json.load(open(sys.argv[1], encoding="utf-8"))
total = tl["total"]
shot = {s["id"]: s for s in tl["shots"]}
N = int(total * SR)
t = np.arange(N) / SR
rng = np.random.default_rng(12)


def note(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# Am - F - C - G，每和弦 6 秒
CHORDS = [[45, 57, 60, 64], [41, 53, 57, 60], [48, 55, 60, 64], [43, 55, 59, 62]]
BEAT = 6.0
pad = np.zeros(N)
for i in range(int(total / BEAT) + 2):
    ch = CHORDS[i % 4]
    a = max(0, int((i * BEAT - 1.2) * SR))
    b = min(N, int(((i + 1) * BEAT + 1.2) * SR))
    if a >= N:
        break
    x = t[a:b] - t[a]
    env = np.minimum(1, x / 1.6) * np.minimum(1, (x[-1] - x) / 1.6)
    seg = np.zeros(b - a)
    for m in ch:
        f = note(m)
        for det, g in ((-.09, .5), (0, .7), (.11, .5)):
            ph = 2 * np.pi * (f + det) * x + rng.uniform(0, 6.28)
            seg += g * (np.sin(ph) + .28 * np.sin(2 * ph) + .1 * np.sin(3 * ph))
    pad[a:b] += seg * env
pad /= np.abs(pad).max()

# 低頻脈動：每 1.5 秒一下，9 天/秒段落加倍
sub = np.zeros(N)
def hit(at, gain):
    i = int(at * SR)
    if i >= N:
        return
    n = min(int(.42 * SR), N - i)
    x = np.arange(n) / SR
    f = 62 * np.exp(-x * 5) + 44
    sub[i:i + n] += gain * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 7)

site, site2, desc = shot["site"], shot["site2"], shot["descend"]
fast = [(site["start"], site2["start"] + site2["dur"]), (desc["start"], desc["start"] + desc["dur"])]
x = shot["hook"]["start"]
end = shot["end"]["start"] + 3
while x < end:
    hit(x, 1.0)
    x += .75 if any(a <= x < b for a, b in fast) else 1.5
sub /= max(np.abs(sub).max(), 1e-6)

# 強度曲線
keys = [(0, .55), (shot["hook"]["start"], .6), (shot["hook"]["start"] + 1.5, .9), (shot["rig"]["start"], 1), (shot["storm"]["start"], 1.0),
        (shot["end"]["start"], .85), (total - 3.5, .8), (total - .2, 0), (total, 0)]
curve = np.interp(t, [k[0] for k in keys], [k[1] for k in keys])
intro = np.clip((t - shot["hook"]["start"]) / 1.2, 0, 1)
mix = (pad * .62 + sub * .55 * intro) * curve

# 立體聲微差、低通讓墊音退到旁白後面
kernel = np.hanning(121); kernel /= kernel.sum()
pad_l = np.convolve(mix, kernel, mode="same")
d = int(.012 * SR)
pad_r = np.concatenate([np.zeros(d), pad_l[:-d]])
st = np.stack([pad_l, pad_r], 1)
st = st / np.abs(st).max() * .7
with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print("music ok", st.shape, float(np.abs(st).max()))
