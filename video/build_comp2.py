"""由 timeline.json 產生 HyperFrames 合成頁：字幕、施工 HUD 與四段示意動畫。"""
import json, math, pathlib, html, re

ROOT = pathlib.Path(__file__).parent
HF = ROOT / "hf"
tl = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))
sched = json.loads((ROOT.parent / "schedule.json").read_text(encoding="utf-8"))
total = tl["total"]
sh = {s["id"]: s for s in tl["shots"]}
vo = {v["id"]: v for v in tl["voice"]}
S = lambda k: sh[k]["start"]
E = lambda k: round(sh[k]["start"] + sh[k]["dur"], 3)
ITEMS = sum(len(v) for v in sched["items"].values())
TASKS = sum(len(v) for v in sched["tasks"].values())

SHOT_T = {"site": (0, 3), "site2": (18, 3), "rig": (27, 1), "deck": (36, 1), "night": (41, 1), "climb": (44.7, 1), "lowarm": (48.5, 1),
          "street": (59, 1), "descend": (56, 3), "fitout": (78.1, 1)}
hud = [{"a": S(k), "b": E(k), "T0": t0, "r": r} for k, (t0, r) in SHOT_T.items()]
phases = [[p["t0"], p["t1"], p["name"]] for p in sched["phases"]]


def cap_html(text):
    parts = []
    for p in re.split(r"(?<=[，。：、？])", text):
        if len(p) > 14:
            k = next((p.index(w) for w in ("和裝潢", "一條條", "一台", "是一台") if w in p), len(p) // 2)
            parts += [p[:k], p[k:]]
        elif p:
            parts.append(p)
    return "".join(f'<span class="nb">{html.escape(x)}</span>' for x in parts)


caps = "\n".join(
    f'<div class="clip cap-wrap" id="cap{i}" data-start="{c["start"]}" data-duration="{round(c["end"] - c["start"], 3)}" data-track-index="9"><p class="cap">{cap_html(c["text"])}</p></div>'
    for i, c in enumerate(tl["caps"]))
starts = json.dumps([c["start"] for c in tl["caps"]])

RX, RY, RR = 540, 700, 262


def arc(h0, h1, r):
    a0, a1 = (h0 / 24) * 2 * math.pi - math.pi / 2, (h1 / 24) * 2 * math.pi - math.pi / 2
    x0, y0, x1, y1 = RX + r * math.cos(a0), RY + r * math.sin(a0), RX + r * math.cos(a1), RY + r * math.sin(a1)
    return f"M{x0:.1f} {y0:.1f} A{r} {r} 0 {1 if h1 - h0 > 12 else 0} 1 {x1:.1f} {y1:.1f}"


ang = lambda i: i / 24 * 2 * math.pi - math.pi / 2
ticks = "".join(
    f'<line x1="{RX + 296 * math.cos(ang(i)):.1f}" y1="{RY + 296 * math.sin(ang(i)):.1f}" x2="{RX + (316 if i % 6 == 0 else 306) * math.cos(ang(i)):.1f}" y2="{RY + (316 if i % 6 == 0 else 306) * math.sin(ang(i)):.1f}" stroke="#8fa2ad" stroke-width="{5 if i % 6 == 0 else 3}"/>'
    for i in range(24))
hourlabels = "".join(
    f'<text x="{RX + 352 * math.cos(ang(h)):.1f}" y="{RY + 352 * math.sin(ang(h)) + 12:.1f}" text-anchor="middle" font-size="34" font-weight="700" fill="#c5d0d6">{h}</text>'
    for h in (0, 6, 12, 18))
chain = "".join(f'<div class="blk" id="blk{i}">{b}</div>' for i, b in enumerate(["鋼筋", "模板", "澆置", "養護", "拆模"]))

plan = ""
XS = [120 + i * 168 for i in range(6)]
YS = [240, 400, 560, 720]
for x in XS:
    plan += f'<path class="draw" d="M{x} {YS[0]}V{YS[-1]}"/>'
for y in YS:
    plan += f'<path class="draw" d="M{XS[0]} {y}H{XS[-1]}"/>'
for x in XS:
    for y in YS:
        plan += f'<rect class="col" x="{x - 15}" y="{y - 15}" width="30" height="30"/>'
for x0, y0, x1, y1 in [(288, 240, 288, 400), (456, 400, 624, 400), (792, 400, 792, 560), (288, 560, 456, 560), (624, 560, 624, 720)]:
    plan += f'<path class="draw wall" d="M{x0} {y0}L{x1} {y1}"/>'
rows = [("C-12", "預鑄柱", "重型 H0", "吊裝"), ("B-07", "預鑄梁", "重型 H1", "吊裝"), ("DMP-3", "阻尼器", "輕型 L2", "安裝"), ("FAC-41", "外牆板", "輕型 L4", "掛裝")]
script = "".join(f'<div class="row" id="srow{i}"><b>{a}</b><span>{b}</span><span>{c}</span><span class="act">{d}</span></div>' for i, (a, b, c, d) in enumerate(rows))
conf = [("吊裝路徑碰撞", "改走內側路徑"), ("工序衝突", "物料提前一班"), ("作業重疊", "拆除順延半天")]
confs = "".join(f'<div class="cf" id="cf{i}"><span class="cf-a">{a}</span><span class="cf-b">{b}</span></div>' for i, (a, b) in enumerate(conf))


def tower(x, w, floors, fh, cid, label, sub):
    base = 1120
    h = floors * fh
    top = base - h
    fl = "".join(f'<line x1="{x}" x2="{x + w}" y1="{base - i * fh}" y2="{base - i * fh}" stroke="#5fd0f2" stroke-width="2" opacity=".55"/>' for i in range(1, floors))
    gap = 16
    masts = "".join(f'<rect x="{mx}" y="{top - 46}" width="9" height="{h + 46}" fill="#f2c230"/>' for mx in (x - gap, x + w + gap - 9))
    ring = f'<rect x="{x - gap - 8}" y="{top - 56}" width="{w + 2 * gap + 16}" height="12" fill="#f2c230"/><rect x="{x + w * .28}" y="{top - 44}" width="9" height="30" fill="#e8622a"/><rect x="{x + w * .66}" y="{top - 44}" width="9" height="30" fill="#e8622a"/>'
    return f'''<g id="{cid}"><rect x="{x}" y="{top}" width="{w}" height="{h}" fill="#0d2b3f" stroke="#5fd0f2" stroke-width="3"/>{fl}{masts}{ring}</g>
    <text id="{cid}t" x="{x + w / 2}" y="1176" text-anchor="middle" font-size="40" font-weight="800" fill="#f7f8f6">{label}</text>
    <text id="{cid}s" x="{x + w / 2}" y="1222" text-anchor="middle" font-size="30" font-weight="500" fill="#f2c230">{sub}</text>'''


towers = tower(70, 170, 4, 30, "tw0", "小型建物", "立柱短配") + tower(365, 190, 12, 30, "tw1", "12 層住宅", "本案配置") + tower(690, 230, 24, 30, "tw2", "超高層", "加節加臂")
cards = [("人力", "現場人力降到最低"), ("安全", "高空與重物交給機器"), ("時程", "先預演，時程更準"), ("精度", "工廠預鑄，精度更高")]
residents = [("噪音", "影響期縮短"), ("粉塵", "現場澆置減少"), ("交通", "構件準時到場")]
res_html = "".join(f'<div class="card rcard" id="rcard{i}"><b>{a}</b><span>{b}</span></div>' for i, (a, b) in enumerate(residents))
card_html = "".join(f'<div class="card" id="card{i}"><b>{a}</b><span>{b}</span></div>' for i, (a, b) in enumerate(cards))

fade = json.dumps([f"#cap{i} .cap" for i in range(len(tl["caps"]))])
p2, p3, e1, r1 = vo["P2"], vo["P3"], vo["E1"], vo["R1"]
CHIP = 'style="right:130px;top:202px;padding:10px 22px 12px;font-size:40px;font-weight:800;color:#14191d;background:#f2c230"'

page = f'''<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<title>天架造樓系統 Demo</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
  @font-face {{ font-family: "TowerTC"; src: url("fonts/NotoSansTC-VF.ttf") format("truetype"); font-weight: 100 900; font-style: normal; }}
  :root {{ --ink: #f7f8f6; --line: #f2c230; --panel: rgba(10, 15, 20, .76); --cy: #5fd0f2; --bp: #061220; --red: #e8552a; }}
  body {{ margin: 0; background: #000; color: var(--ink); font-family: "TowerTC", sans-serif; }}
  #root {{ position: relative; width: 1080px; height: 1920px; overflow: hidden; background: #000; }}
  #footage {{ position: absolute; inset: 0; width: 1080px; height: 1920px; object-fit: cover; }}
  #shade {{ position: absolute; inset: 0; background: linear-gradient(180deg, rgba(0,0,0,.5) 0, rgba(0,0,0,0) 22%, rgba(0,0,0,0) 62%, rgba(0,0,0,.42) 86%, rgba(0,0,0,.2) 100%); }}
  #dip {{ position: absolute; inset: 0; background: #000; opacity: 0; }}
  .clip {{ position: absolute; }}
  .cap-wrap {{ left: 70px; right: 130px; top: 1290px; height: 230px; display: flex; align-items: flex-end; justify-content: center; }}
  .cap {{ margin: 0; max-width: 840px; padding: 16px 28px 20px; background: var(--panel); border-left: 6px solid var(--line); font-size: 54px; font-weight: 700; line-height: 1.32; letter-spacing: .01em; text-align: left; }}
  .nb {{ display: inline-block; white-space: nowrap; }}

  .hud {{ left: 44px; top: 190px; width: 600px; padding: 18px 24px 20px; background: var(--panel); }}
  .hud-num {{ font-size: 104px; line-height: 1; font-weight: 800; font-variant-numeric: tabular-nums; }}
  .hud-ph {{ margin-top: 12px; font-size: 40px; font-weight: 700; color: var(--line); }}
  #hud-bar {{ position: relative; margin-top: 14px; width: 552px; height: 8px; background: rgba(255,255,255,.3); }}
  #hud-fill {{ position: absolute; left: 0; top: 0; height: 8px; width: 552px; transform-origin: 0 50%; background: var(--line); }}
  #hud-note {{ margin-top: 12px; font-size: 26px; font-weight: 500; }}
  .tag {{ left: 44px; top: 190px; display: flex; flex-direction: column; gap: 8px; }}
  .tag-k {{ align-self: flex-start; padding: 6px 18px 8px; font-size: 34px; font-weight: 800; color: #14191d; background: var(--line); }}
  .tag-v {{ align-self: flex-start; padding: 8px 20px 12px; font-size: 52px; font-weight: 800; background: var(--panel); }}

  #title {{ left: 60px; right: 130px; top: 200px; }}
  #title h1 {{ margin: 0; font-size: 104px; font-weight: 900; line-height: 1.14; text-shadow: 0 4px 26px rgba(0,0,0,.6); }}
  #title p {{ display: inline-block; margin: 14px 0 0; padding: 8px 18px 12px; font-size: 36px; font-weight: 700; color: var(--line); background: var(--panel); }}

  #pain {{ inset: 0; background: rgba(5, 9, 14, .8); }}
  #pain h1 {{ position: absolute; left: 60px; top: 196px; margin: 0; font-size: 80px; font-weight: 900; }}
  #pain svg {{ position: absolute; left: 0; top: 0; }}
  .dial-a {{ position: absolute; left: 340px; top: 590px; width: 400px; text-align: center; font-size: 100px; font-weight: 900; line-height: 1.1; }}
  .dial-b {{ position: absolute; left: 340px; top: 712px; width: 400px; text-align: center; font-size: 38px; font-weight: 700; color: #c5d0d6; }}
  #dialB {{ color: #ff8a5c; }}
  #chain {{ position: absolute; left: 44px; top: 1120px; width: 900px; height: 120px; display: flex; gap: 10px; }}
  .blk {{ width: 164px; height: 96px; display: flex; align-items: center; justify-content: center; font-size: 42px; font-weight: 800; background: #1c2a33; border: 3px solid #5a707c; box-sizing: border-box; }}
  #stuck {{ position: absolute; left: 218px; top: 1060px; padding: 2px 16px 6px; font-size: 36px; font-weight: 800; background: var(--red); color: #fff; }}

  .bp {{ inset: 0; background-color: var(--bp); background-image: linear-gradient(rgba(95,208,242,.08) 1px, transparent 1px), linear-gradient(90deg, rgba(95,208,242,.08) 1px, transparent 1px); background-size: 60px 60px; }}
  .bp h1 {{ position: absolute; left: 60px; top: 196px; margin: 0; font-size: 80px; font-weight: 900; }}
  .bp .sub {{ position: absolute; left: 62px; top: 302px; font-size: 38px; font-weight: 700; color: var(--line); }}
  #plan {{ position: absolute; left: 0; top: 150px; }}
  #plan .draw {{ fill: none; stroke: var(--cy); stroke-width: 3; stroke-dasharray: 1100; stroke-dashoffset: 1100; }}
  #plan .wall {{ stroke-width: 9; stroke: #d6f2fb; }}
  #plan .col {{ fill: var(--line); opacity: 0; }}
  #scan {{ position: absolute; left: 90px; top: 370px; width: 900px; height: 6px; background: var(--line); box-shadow: 0 0 26px 6px rgba(242,194,48,.65); opacity: 0; }}
  #script {{ position: absolute; left: 60px; top: 900px; width: 880px; }}
  .row {{ display: grid; grid-template-columns: 200px 210px 240px 1fr; align-items: center; height: 72px; padding: 0 22px; font-size: 38px; font-weight: 600; border-bottom: 2px solid rgba(95,208,242,.35); }}
  .row b {{ color: var(--cy); font-variant-numeric: tabular-nums; }}
  .row .act {{ color: var(--line); font-weight: 800; }}
  #count {{ position: absolute; left: 62px; top: 1200px; font-size: 34px; font-weight: 700; color: #c5d0d6; }}

  #cflist {{ left: 44px; top: 362px; width: 800px; display: flex; flex-direction: column; gap: 12px; }}
  .cf {{ display: flex; align-items: center; justify-content: space-between; padding: 12px 22px 16px; background: rgba(6, 18, 32, .88); border-left: 8px solid var(--red); font-size: 38px; font-weight: 700; }}
  .cf-b {{ color: var(--cy); font-size: 34px; }}
  #stamp {{ left: 190px; top: 780px; width: 680px; padding: 20px 0 30px; text-align: center; font-size: 110px; font-weight: 900; color: #7dff9e; border: 10px solid #7dff9e; background: rgba(6, 18, 32, .82); }}

  #scale svg {{ position: absolute; left: 0; top: 0; }}

  #benefits {{ left: 44px; top: 190px; display: grid; grid-template-columns: 1fr 1fr; gap: 16px; width: 900px; }}
  .card {{ padding: 16px 22px 20px; background: rgba(10, 15, 20, .84); border-top: 8px solid var(--line); }}
  .card b {{ display: block; font-size: 66px; font-weight: 900; line-height: 1.2; }}
  .card span {{ display: block; margin-top: 2px; font-size: 32px; font-weight: 600; color: #dfe6ea; }}

  #ninety {{ left: 60px; top: 200px; }}
  #ninety b {{ display: block; font-size: 190px; font-weight: 900; line-height: 1; color: var(--line); text-shadow: 0 6px 30px rgba(0,0,0,.7); }}
  #ninety span {{ display: inline-block; margin-top: 12px; padding: 8px 20px 12px; font-size: 44px; font-weight: 800; background: var(--panel); }}
  #residents {{ left: 44px; top: 268px; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; width: 900px; }}
  .rcard b {{ font-size: 60px; }}
  .rcard span {{ font-size: 28px; }}
  #endcard {{ left: 60px; right: 130px; top: 190px; }}
  #endcard h2 {{ margin: 0; font-size: 100px; font-weight: 900; line-height: 1.14; }}
  #endcard p {{ margin: 14px 0 0; font-size: 36px; font-weight: 700; color: var(--line); }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{total}">
  <video id="footage" data-start="0" data-duration="{total}" data-track-index="0" src="footage.mp4" muted playsinline></video>
  <audio id="mix" data-start="0" data-duration="{total}" data-track-index="1" src="mix.wav"></audio>
  <div id="shade"></div>

  <div class="clip" id="pain" data-start="0" data-duration="{sh['idle']['dur']}" data-track-index="2">
    <h1>工地大半時間是停的</h1>
    <svg width="1080" height="1300" viewBox="0 0 1080 1300">
      <circle cx="{RX}" cy="{RY}" r="{RR}" fill="none" stroke="#2c3a43" stroke-width="58"/>
      <path id="arc-off" d="{arc(17, 32, RR)}" fill="none" stroke="#a23a1a" stroke-width="58" stroke-dasharray="1500" stroke-dashoffset="1500"/>
      <path id="arc-on" d="{arc(8, 16.99, RR)}" fill="none" stroke="#f2c230" stroke-width="58" stroke-dasharray="900" stroke-dashoffset="900"/>
      {ticks}{hourlabels}
      <line id="hand" x1="{RX}" y1="{RY - 200}" x2="{RX}" y2="{RY - 322}" stroke="#f7f8f6" stroke-width="12" stroke-linecap="round"/>
    </svg>
    <div class="dial-a" id="dialA">8 小時</div><div class="dial-b" id="dialAs">人工施工（示意）</div>
    <div class="dial-a" id="dialB">16 小時</div><div class="dial-b" id="dialBs">工地停著（示意）</div>
    <div id="chain">{chain}</div>
    <div id="stuck">卡關</div>
  </div>

  <div class="clip" id="title" data-start="{S('heroB')}" data-duration="{round(S('aiplan') - S('heroB'), 3)}" data-track-index="2">
    <h1>會長高的工地</h1>
    <p>24 小時不停工｜12 層 90 天｜概念模擬</p>
  </div>

  <div class="clip bp" id="aiplan" data-start="{S('aiplan')}" data-duration="{sh['aiplan']['dur']}" data-track-index="2">
    <h1>AI 讀圖，拆成建造腳本</h1>
    <svg id="plan" width="1080" height="760" viewBox="0 0 1080 760">{plan}</svg>
    <div id="scan"></div>
    <div id="script">{script}</div>
    <div id="count">{ITEMS:,} 件構件 → {TASKS:,} 筆吊裝任務</div>
  </div>

  <div class="clip tag" id="twintag" data-start="{S('twin')}" data-duration="{sh['twin']['dur']}" data-track-index="3"><span class="tag-k">數位預演</span><span class="tag-v">開工前，系統先蓋一次</span></div>
  <div class="clip" id="cflist" data-start="{S('twin')}" data-duration="{sh['twin']['dur']}" data-track-index="4">{confs}</div>
  <div class="clip" id="stamp" data-start="{round(E('twin') - 2.1, 3)}" data-duration="2.1" data-track-index="5">驗證通過</div>

  <div class="clip bp" id="scale" data-start="{S('scale')}" data-duration="{sh['scale']['dur']}" data-track-index="2">
    <h1>規模不同，邏輯相同</h1>
    <div class="sub">立柱節段與手臂都是模組</div>
    <svg width="1080" height="1260" viewBox="0 0 1080 1260"><line x1="40" x2="1040" y1="1120" y2="1120" stroke="#8fa2ad" stroke-width="4"/>{towers}</svg>
  </div>

  <div class="clip hud" id="hud" data-start="{S('site')}" data-duration="{round(E('rig') - S('site'), 3)}" data-track-index="6">
    <div class="hud-num hudn">第 0 天</div><div class="hud-ph hudp">基地整備</div>
    <div id="hud-bar"><div id="hud-fill"></div></div>
    <div id="hud-note">概念模擬，工期與數值皆為示意</div>
  </div>
  <div class="clip hud" id="hudB" data-start="{S('deck')}" data-duration="{round(E('street') - S('deck'), 3)}" data-track-index="6"><div class="hud-num hudn">第 152 天</div><div class="hud-ph hudp">主體結構</div></div>
  <div class="clip hud" id="hudC" data-start="{S('descend')}" data-duration="{round(E('fitout') - S('descend'), 3)}" data-track-index="6"><div class="hud-num hudn">第 276 天</div><div class="hud-ph hudp">天架下降</div></div>
  <div class="clip" id="speedA" {CHIP} data-start="{S('site')}" data-duration="{round(E('rig') - S('site'), 3)}" data-track-index="7">3 天/秒</div>
  <div class="clip" id="speedB" {CHIP} data-start="{S('deck')}" data-duration="{round(E('street') - S('deck'), 3)}" data-track-index="7">1 天/秒</div>
  <div class="clip" id="speedC" {CHIP} data-start="{S('descend')}" data-duration="{round(E('fitout') - S('descend'), 3)}" data-track-index="7">3 天/秒</div>
  <div class="clip tag" id="storm-tag" data-start="{S('storm')}" data-duration="{sh['storm']['dur']}" data-track-index="6"><span class="tag-k">情境演練</span><span class="tag-v">颱風來襲</span></div>
  <div class="clip tag" id="fac-tag" data-start="{S('factory')}" data-duration="{sh['factory']['dur']}" data-track-index="6"><span class="tag-k">工廠預鑄</span><span class="tag-v">工地只做吊裝和接合</span></div>
  <div class="clip" id="ninety" data-start="{S('finale')}" data-duration="{round(e1['start'] - S('finale'), 3)}" data-track-index="6"><b>90 天</b><span>12 層完工（概念目標）</span></div>
  <div class="clip" id="benefits" data-start="{e1['start']}" data-duration="{round(E('finale') - e1['start'], 3)}" data-track-index="6">{card_html}</div>
  <div class="clip tag" id="res-tag" data-start="{S('neighbor')}" data-duration="{sh['neighbor']['dur']}" data-track-index="7"><span class="tag-k">對鄰居的好處</span></div>
  <div class="clip" id="residents" data-start="{S('neighbor')}" data-duration="{sh['neighbor']['dur']}" data-track-index="6">{res_html}</div>
  <div class="clip" id="endcard" data-start="{round(S('end') + .6, 3)}" data-duration="{round(sh['end']['dur'] - .6, 3)}" data-track-index="6">
    <h2>天架造樓系統</h2>
    <p>互動式 3D 概念模擬｜工期數值皆為示意</p>
  </div>
  {caps}
  <div id="dip"></div>
</div>
<script>
  const HUD = {json.dumps(hud)};
  const PH = {json.dumps(phases, ensure_ascii=False)};
  const FAST = [[{S('site')}, {S('rig')}], [{S('descend')}, {S('fitout')}]];
  const dayAt = (t) => {{ for (const s of HUD) if (t >= s.a && t < s.b) return s.T0 + (t - s.a) * s.r; return null; }};
  const phaseAt = (T) => (PH.find((p) => T >= p[0] && T < p[1]) || PH[PH.length - 1])[2];
  const el = (id) => document.getElementById(id);
  const nums = [...document.querySelectorAll(".hudn")], phs = [...document.querySelectorAll(".hudp")];
  const clock = {{ _t: 0 }};
  Object.defineProperty(clock, "t", {{
    get() {{ return this._t; }},
    set(v) {{
      this._t = v;
      const T = dayAt(v);
      if (T === null) return;
      const label = "第 " + Math.floor(T) + " 天";
      nums.forEach((n) => (n.textContent = label));
      phs.forEach((n) => (n.textContent = phaseAt(T)));
      el("hud-fill").style.transform = "scaleX(" + (T / 90).toFixed(4) + ")";
      const fast = FAST.some(([a, b]) => v >= a && v < b);
      el("speedA").textContent = fast ? "3 天/秒" : "1 天/秒";
      el("speedC").textContent = fast ? "3 天/秒" : "1 天/秒";
    }},
  }});
  const tl = gsap.timeline({{ paused: true }});
  tl.to(clock, {{ t: {total}, duration: {total}, ease: "none" }}, 0);
  {fade}.forEach((sel, i) => tl.fromTo(sel, {{ opacity: 0, y: 10 }}, {{ opacity: 1, y: 0, duration: .16, ease: "power2.out" }}, {starts}[i]));

  const P2 = {p2['start']}, P3 = {p3['start']};
  tl.fromTo("#pain h1", {{ y: 24, opacity: 0 }}, {{ y: 0, opacity: 1, duration: .5, ease: "power3.out" }}, .15);
  tl.fromTo("#hand", {{ rotation: 120, svgOrigin: "{RX} {RY}" }}, {{ rotation: 240, duration: P2 - .2, ease: "none" }}, .2);
  tl.fromTo("#arc-on", {{ strokeDashoffset: 900 }}, {{ strokeDashoffset: 0, duration: P2 - .2, ease: "none" }}, .2);
  tl.to("#hand", {{ rotation: 480, duration: 3.2, ease: "power1.inOut" }}, P2);
  tl.fromTo("#arc-off", {{ strokeDashoffset: 1500 }}, {{ strokeDashoffset: 0, duration: 3.2, ease: "power1.inOut" }}, P2);
  tl.fromTo(["#dialB", "#dialBs"], {{ opacity: 0 }}, {{ opacity: 1, duration: .25 }}, P2 + 1.2);
  tl.fromTo(["#dialA", "#dialAs"], {{ opacity: 1 }}, {{ opacity: 0, duration: .25 }}, P2 + 1.2);
  tl.fromTo("#chain .blk", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: .3, stagger: .08 }}, P3 - .9);
  tl.fromTo("#stuck", {{ opacity: 0, y: 10 }}, {{ opacity: 1, y: 0, duration: .2 }}, P3 + .25);
  tl.to("#blk1", {{ backgroundColor: "#8a2f14", borderColor: "#e8552a", duration: .25 }}, P3 + .25);
  tl.to(["#blk2", "#blk3", "#blk4"], {{ x: 40, opacity: .45, duration: .55, stagger: .12, ease: "power2.inOut" }}, P3 + .55);

  tl.fromTo("#title h1", {{ y: 26, opacity: 0 }}, {{ y: 0, opacity: 1, duration: .5, ease: "power3.out" }}, {S('heroB') + .1});
  tl.fromTo("#title p", {{ opacity: 0 }}, {{ opacity: 1, duration: .5 }}, {S('heroB') + .4});

  const A0 = {S('aiplan')}, AD = {sh['aiplan']['dur']};
  tl.fromTo("#aiplan h1", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: .4 }}, A0 + .1);
  tl.to("#plan .draw", {{ strokeDashoffset: 0, duration: 1.3, stagger: .05, ease: "power1.inOut" }}, A0 + .2);
  tl.to("#plan .col", {{ opacity: 1, duration: .15, stagger: .03 }}, A0 + 1.3);
  tl.fromTo("#scan", {{ opacity: 0 }}, {{ opacity: 1, duration: .15 }}, A0 + .3);
  tl.fromTo("#scan", {{ y: 0 }}, {{ y: 500, duration: AD * .34, ease: "none" }}, A0 + .3);
  tl.to("#scan", {{ opacity: 0, duration: .2 }}, A0 + .3 + AD * .34);
  tl.fromTo("#script .row", {{ opacity: 0, x: -30 }}, {{ opacity: 1, x: 0, duration: .3, stagger: .42, ease: "power2.out" }}, A0 + AD * .44);
  tl.fromTo("#count", {{ opacity: 0 }}, {{ opacity: 1, duration: .4 }}, A0 + AD * .78);

  const T0 = {S('twin')}, TD = {sh['twin']['dur']};
  tl.fromTo(".cf", {{ opacity: 0, x: -40 }}, {{ opacity: 1, x: 0, duration: .3, stagger: TD * .15, ease: "power2.out" }}, T0 + TD * .12);
  [0, 1, 2].forEach((i) => tl.to("#cf" + i, {{ borderLeftColor: "#7dff9e", duration: .2 }}, T0 + TD * (.24 + .15 * i)));
  tl.fromTo("#stamp", {{ opacity: 0, scale: 1.5 }}, {{ opacity: 1, scale: 1, duration: .3, ease: "back.out(2)" }}, {E('twin') - 2.1});

  const G0 = {S('scale')}, GD = {sh['scale']['dur']};
  tl.fromTo("#scale h1", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: .4 }}, G0 + .1);
  tl.fromTo("#scale .sub", {{ opacity: 0 }}, {{ opacity: 1, duration: .4 }}, G0 + .4);
  [["#tw0", .1], ["#tw1", .36], ["#tw2", .6]].forEach(([id, k]) => {{
    tl.fromTo(id, {{ scaleY: 0, svgOrigin: "540 1120" }}, {{ scaleY: 1, duration: 1.1, ease: "power2.out" }}, G0 + GD * k);
    tl.fromTo([id + "t", id + "s"], {{ opacity: 0 }}, {{ opacity: 1, duration: .3 }}, G0 + GD * k + .5);
  }});

  const e = {e1['start']}, ed = {e1['dur']};
  [[0, 0], [1, .42], [2, .6], [3, .78]].forEach(([i, k]) => tl.fromTo("#card" + i, {{ opacity: 0, y: 26 }}, {{ opacity: 1, y: 0, duration: .32, ease: "power3.out" }}, e + ed * k));

  tl.fromTo("#ninety b", {{ scale: 1.4, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: .35, ease: "back.out(2)" }}, {S('finale') + .05});
  const r = {r1['start']}, rd = {r1['dur']};
  [[0, .1], [1, .28], [2, .45]].forEach(([i, k]) => tl.fromTo("#rcard" + i, {{ opacity: 0, y: 26 }}, {{ opacity: 1, y: 0, duration: .32, ease: "power3.out" }}, r + rd * k));

  tl.fromTo("#endcard h2", {{ y: 26, opacity: 0 }}, {{ y: 0, opacity: 1, duration: .7, ease: "power3.out" }}, {S('end') + .7});
  tl.fromTo("#endcard p", {{ opacity: 0 }}, {{ opacity: 1, duration: .6 }}, {S('end') + 1.1});
  tl.fromTo("#dip", {{ opacity: 0 }}, {{ opacity: 1, duration: .22, ease: "power1.in" }}, {S('site') - .22});
  tl.to("#dip", {{ opacity: 0, duration: .3, ease: "power1.out" }}, {S('site')});
  tl.to("#dip", {{ opacity: 1, duration: .8 }}, {total - .8});
  window.__timelines["main"] = tl;
</script>
</body>
</html>
'''
(HF / "index.html").write_text(page, encoding="utf-8")
print("comp written", len(page))
