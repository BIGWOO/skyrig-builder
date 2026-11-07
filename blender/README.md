# Procedural site generator · 程序化工地生成

One Python script builds the entire construction site in Blender and writes the two data files the website reads.

用一支 Python 腳本在 Blender 裡生成整個工地，並輸出網站讀取的兩個資料檔。

```bash
# run from the repository root · 在 repo 根目錄執行
blender --background --factory-startup --python blender/build_tower.py
```

Written for Blender 5.2. When it finishes it prints a `BUILD_OK` line with part, instance, triangle and task counts.

以 Blender 5.2 撰寫，完成時會印出 `BUILD_OK`，列出零件、構件、三角面和任務數量。

## What it writes · 輸出

| Output | 說明 |
|---|---|
| `schedule.json` | Phases, rig climbing keys, every instance with its appear and remove time, lifting tasks, robot timelines · 工期階段、天架爬升關鍵幀、每件構件的出現與移除時間、吊裝任務、機器人排程 |
| `parts.glb.txt` | The 102 part meshes as base64 GLB · 102 種零件模型（base64 GLB） |
| `parts.glb` | Same meshes as a plain GLB, git-ignored · 同一份模型的原始 GLB，不進 git |
| `blender/tex/` | Procedural textures (concrete, soil, asphalt…) made from FFT noise, git-ignored · 用 FFT 雜訊生成的材質貼圖，不進 git |
| `blender/tower.blend` | The assembled scene at day 90, for inspection, git-ignored · 第 90 天的完整場景，方便檢查，不進 git |

## Files · 檔案

| File | Role | 用途 |
|---|---|---|
| `schedule_spec.py` | Grid, storey heights, phase dates, rig climbing curve | 柱網、樓高、各階段日期、天架爬升曲線 |
| `kit.py` | Mesh helpers, procedural textures and materials | 建模工具、程序化貼圖與材質 |
| `parts.py` | The 102 part definitions: columns, beams, slabs, façade, rig, arms, robots, trucks, neighbours | 102 種零件：柱、梁、樓板、外牆、天架、手臂、機器人、卡車、鄰房 |
| `build_tower.py` | Places every part on the 90-day timeline and exports | 把每件構件排上 90 天時間軸並輸出 |

Change a date in `schedule_spec.py` or a part in `parts.py`, rerun the script, and reload the website: the simulation, the tour and the AI rehearsal all read the new data.

改 `schedule_spec.py` 的日期或 `parts.py` 的零件，重跑腳本再重新整理網頁，模擬、導覽和 AI 預演都會讀到新資料。
