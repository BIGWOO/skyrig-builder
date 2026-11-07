import asyncio, json, subprocess, sys, pathlib
import edge_tts

SRC, OUT = sys.argv[1], pathlib.Path(sys.argv[2])
VOICE, RATE, PITCH = "zh-TW-YunJheNeural", sys.argv[3], sys.argv[4]
OUT.mkdir(parents=True, exist_ok=True)
lines = json.loads(open(SRC, encoding="utf-8").read())


async def one(l):
    p = OUT / f"{l['id']}.mp3"
    text = l.get("speak", l["text"])
    for attempt in range(40):
        try:
            await edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH).save(str(p))
            break
        except edge_tts.exceptions.NoAudioReceived:
            print(l["id"], "no audio, attempt", attempt + 1, flush=True)
            await asyncio.sleep(1.5)
    else:
        return l["id"], 0, len(l["text"])
    d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]))
    await asyncio.sleep(1)
    return l["id"], round(d, 3), len(l["text"])


async def main():
    res = [await one(l) for l in lines]
    for r in res:
        print(r, round(r[2] / r[1], 2) if r[1] else "FAILED")
    print("total", round(sum(r[1] for r in res), 2))
    json.dump({r[0]: r[1] for r in res}, open(OUT / "durations.json", "w"), indent=1)


asyncio.run(main())
