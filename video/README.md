# Intro film pipeline · 介紹影片製作流程

The 2:14 intro film is not screen-recorded. Every frame is rendered by the website itself under a virtual clock, so camera moves stay smooth regardless of GPU speed, and the narration sets the length of every shot.

2 分 14 秒的介紹影片不是螢幕錄影。每一幀都由網站本身在虛擬時鐘下算出來，鏡頭運動不受顯示卡速度影響；每個鏡頭多長，由旁白實際長度決定。

```text
narration.json ─▶ TTS ─▶ timeline.py ─┬─▶ shots.js ─▶ cap.mjs ─▶ concat2.py ─▶ footage   ─┐
                                      ├─▶ voice ─▶ music.py + mix.py ─────────▶ audio     ─┼─▶ HyperFrames ─▶ 9:16 MP4
                                      └─▶ build_comp2.py ─────────────────────▶ subtitles ─┘
```

## Steps · 步驟

Run everything inside `video/`. 全部在 `video/` 裡執行。

| # | Command | What happens | 做了什麼 |
|:-:|---|---|---|
| 1 | `python tts_gen.py narration.json voice -3% -10Hz` | 25 narration lines to speech (`zh-TW-YunJheNeural`) and measures each one | 25 句旁白轉成語音，並量出每句長度 |
| 2 | `python timeline.py` | Lays out shots and subtitles from real speech length, writes `timeline.json`, updates shot lengths in `shots.js`, builds the voice track | 依語音長度排鏡頭和字幕，更新 `shots.js` 的鏡頭秒數，產生旁白音軌 |
| 3 | `node cap.mjs --web .. --out final --final` | Opens the site headless, takes over `requestAnimationFrame` and `performance.now`, and renders each shot at 1080×1920, 30 fps | 無頭瀏覽器開啟網站，接管動畫時鐘，逐幀輸出每個鏡頭 |
| 4 | `python concat2.py` | Joins the shots into one footage file | 把各鏡頭接成一條影像 |
| 5 | `python music.py timeline.json vo/music.wav` | Synthesises an original music bed whose intensity follows the shots | 合成原創配樂，強弱跟著分鏡走 |
| 6 | `python mix.py` then copy `vo/mix.wav` to `hf/` | Ducks the music under the voice, adds hits, normalises to −16 LUFS | 旁白響時壓低配樂、加入音效、統一到 −16 LUFS |
| 7 | `python build_comp2.py` | Writes the HyperFrames composition: subtitles, phase HUD and four explainer animations | 產生 HyperFrames 合成頁：字幕、工期 HUD 和四段示意動畫 |
| 8 | `cd hf && npx hyperframes render -q delivery --crf 18 -o renders/tower-demo.mp4` | Renders the final film | 輸出成片 |

`shots.js` is the storyboard: one function per shot that sets the simulation time, camera path and scenario for any frame. Edit it to recut the film.

`shots.js` 就是分鏡表：每個鏡頭一個函式，決定任一幀的工期時間、鏡頭路徑和情境。要改片就改它。

## What you need · 需要準備

- Python 3.11+ with `edge-tts` and `numpy`; Node 20+ with `npm install` here for `playwright-core`; Google Chrome; ffmpeg.
- `cap.mjs` and `concat2.py` encode with `h264_nvenc`, so they expect an NVIDIA GPU. On other machines, swap it for `libx264`.
- Before step 8, put `hyperframes.json` (`{ "name": "tower-demo" }`) and `fonts/NotoSansTC-VF.ttf` ([Noto Sans TC](https://fonts.google.com/noto/specimen/Noto+Sans+TC), OFL) in `hf/`.
- Sound effects are not included. Put `riser`, `whoosh`, `whoosh-short`, `whoosh-cinematic`, `impact-bass-1` and `impact-bass-2` as `.mp3` in `video/sfx/`, or point `SKYRIG_SFX` at your own folder.

需要 Python（`edge-tts`、`numpy`）、Node（在此資料夾 `npm install`）、Chrome 和 ffmpeg。`cap.mjs` 和 `concat2.py` 用 NVIDIA 的 `h264_nvenc` 編碼，沒有 NVIDIA 顯示卡就換成 `libx264`。第 8 步前，在 `hf/` 放好 `hyperframes.json` 和 Noto Sans TC 字型。音效檔沒有附上，請把同名的 mp3 放在 `video/sfx/`，或用 `SKYRIG_SFX` 指到自己的資料夾。
