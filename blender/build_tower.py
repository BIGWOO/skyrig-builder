import json
import math
import os
import random
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True

import kit
import parts
from schedule_spec import *

ROOT = os.path.dirname(HERE)
WEB = ROOT  # schedule.json 與 parts.glb.txt 直接輸出到網站根目錄
TEX = os.path.join(ROOT, "blender", "tex")
os.makedirs(WEB, exist_ok=True)
os.makedirs(TEX, exist_ok=True)
kit.TEX_DIR = TEX

GROW, LIFT, POP = 0, 1, 2
NEVER = 9999.0
PI = math.pi
PLANT = parts.PLANT

items = {}
tasks = {k: [] for k in ("H0", "H1", "S0", "S1", "N0", "N1", "E0", "W0")}
bot_runs = []
log = []
KEYS = rig_keys()


def add(part, x, y, z, rz=0.0, s=(1, 1, 1), t=-1.0, d=.001, end=NEVER, endd=.5, mode=POP, frm=(0, 0, 0)):
    items.setdefault(part, []).append(
        [round(v, 3) for v in (x, y, z, rz, s[0], s[1], s[2], t, d, end, endd, frm[0], frm[1], frm[2], mode)])


def note(t0, t1, text):
    log.append([round(t0, 2), round(t1, 2), text])


def bot(name, t0, t1, z, x0=-17, y0=-9.5, x1=17, y1=9.5, mode=0, period=2.0):
    bot_runs.append([name, round(t0, 2), round(t1, 2), round(z, 3), x0, y0, x1, y1, mode, period])


def heavy_lift(specs, t0, t1, slots=4):
    groups = {"H0": [s for s in specs if s["x"] < 0], "H1": [s for s in specs if s["x"] >= 0]}
    for arm, lst in groups.items():
        if not lst:
            continue
        lst.sort(key=lambda s: (s["y"], s["x"]))
        cs = chunks(lst, slots)
        dt = (t1 - t0) / len(cs)
        for k, c in enumerate(cs):
            a = t0 + k * dt
            b = a + dt
            rz = rig_z(a, KEYS)
            pick = (-6.0 if arm == "H0" else 6.0, 12.4, rz - 5.0)
            q = [sum(s[v] for s in c) / len(c) for v in ("x", "y", "z")]
            q[2] += 1.2
            tasks[arm].append([round(v, 3) for v in (a, b, *pick, *q)] + [0])
            for s in c:
                frm = (pick[0] - s["x"], pick[1] - s["y"], pick[2] - s["z"])
                add(s["part"], s["x"], s["y"], s["z"], s.get("rz", 0), s.get("s", (1, 1, 1)),
                    a + .25 * (b - a), .6 * (b - a), s.get("end", NEVER), s.get("endd", .5), LIFT, frm)


def pour_tasks(bays, z, t0, t1):
    groups = {"H0": [b for b in bays if b[0] < 0], "H1": [b for b in bays if b[0] >= 0]}
    for arm, lst in groups.items():
        if not lst:
            continue
        lst.sort()
        dt = (t1 - t0) / len(lst)
        for k, (x, y) in enumerate(lst):
            a = t0 + k * dt
            tasks[arm].append([round(v, 3) for v in (a, a + dt, x, y, z + 3, x, y, z + 3)] + [2])


def side_lift(arm, part, x, y, z, rz, out, s, t0, dur):
    frm = (out[0] * 2.4, out[1] * 2.4, -1.0)
    tasks[arm].append([round(v, 3) for v in (t0, t0 + dur, x + frm[0], y + frm[1], z + 1.2 + frm[2], x, y, z + 1.2)] + [0])
    add(part, x, y, z, rz, s, t0 + .25 * dur, .6 * dur, NEVER, .5, LIFT, frm)
    tasks[arm].append([round(v, 3) for v in (t0 + dur, t0 + dur + .12, x, y, z + 1.0, x, y, z + 1.0)] + [1])


def site_prep():
    t0, t1 = 0, 15
    bot("drone", 0, 12, 18, -24, -14, 24, 26)
    bot("bot_dog", 2, 12, 0.02, -24, 13.5, 24, 27)
    note(0, 5, "無人機建立地形與鄰房基準模型")
    note(5, 10, "組立圍籬、觀景窗與進度看板")
    note(10, 15, "導牆施作與連續壁放樣")
    for k in range(18):
        x = -25.5 + k * 3
        kind = "hoard_win" if k % 3 == 1 else "hoard"
        if x < 20:
            add(kind, x, -15.5, 0, 0, t=3 + k * .15, d=.3, end=342, mode=GROW)
        add("hoard", x, 29, 0, 0, t=3 + k * .15, d=.3, end=342, mode=GROW)
    for k in range(15):
        y = -14 + k * 3
        add("hoard", -26, y, 0, PI / 2, t=4 + k * .15, d=.3, end=342, mode=GROW)
        add("hoard", 26, y, 0, PI / 2, t=4 + k * .15, d=.3, end=342, mode=GROW)
    add("led_board", -11, -15.2, 0, t=7, d=.5, end=348, mode=POP)
    add("led_screen", -11, -15.2, 0, t=7, d=.5, end=348, mode=POP)
    add("control_cabin", 12, 21, 0, t=8, d=.6, end=344)
    add("precast_yard", -11, 21.5, 0, t=8, d=.6, end=330)
    for i in range(14):
        add("pad_plate", -24 + (i % 2) * 48 if i < 12 else 0, -13 + (i % 12) * 2.2 if i < 12 else 0, .01, PI / 2, t=9, d=.3,
            end=320) if i < 12 else None


def perimeter():
    out = []
    n = 13
    for k in range(n):
        x = -18 + k * 3
        out.append((x, -WALL_Y - .4, 0))
    for k in range(8):
        y = -10.5 + k * 3
        out.append((WALL_X + .4, y, PI / 2))
    for k in range(n):
        x = 18 - k * 3
        out.append((x, WALL_Y + .4, 0))
    for k in range(8):
        y = 10.5 - k * 3
        out.append((-WALL_X - .4, y, PI / 2))
    return out


def dwall():
    panels = perimeter()
    t0, t1 = 15, 53
    dt = (t1 - t0) / len(panels)
    for k, (x, y, r) in enumerate(panels):
        add("guide_wall", x, y, 0, r, t=11 + k * .08, d=.3, end=t0 + k * dt + dt)
        add("dwall", x, y, 0, r, t=t0 + k * dt + dt * .4, d=dt * .6, mode=GROW)
        add("cap", x, y, .02, r, t=52 + k * .05, d=.3, mode=GROW)
    for i in range(0, len(panels), 2):
        x, y, r = panels[i]
        off = 3.6
        cx = x + (off if abs(y) < WALL_Y else 0) * (-1 if x > 0 else 1)
        cy = y + (off if abs(y) >= WALL_Y else 0) * (-1 if y > 0 else 1)
        bot("trench_cutter", t0 + i * dt, t0 + (i + 2) * dt, 0, cx, cy, cx, cy, 2)
    note(15, 53, "液壓抓斗機分段開挖、吊放鋼筋籠、水中澆置連續壁")
    note(52, 55, "連續壁頂梁，完成天架基座")


def piles():
    ps = [(x, y) for x in XS for y in YS]
    t0, t1 = 55, 70
    dt = (t1 - t0) / len(ps)
    for k, (x, y) in enumerate(ps):
        add("pile", x, y, -8.2, t=t0 + k * dt, d=dt * .8, mode=GROW)
        bot("pile_rig", t0 + k * dt, t0 + (k + 1) * dt, 0, x - 2, y, x - 2, y, 2)
    note(55, 70, "鑽機依地質模型逐根鑽掘、下鋼筋籠、澆置")


def excavate():
    nx, ny, nz = 10, 6, 4
    sx, sy = 40.6 / nx, 25.6 / ny
    layer = 9.0 / nz
    t0, t1 = 70, 104
    dtl = (t1 - t0) / nz
    for l in range(nz):
        ta = t0 + l * dtl
        order = [(i, j) for i in range(nx) for j in range(ny)]
        for n, (i, j) in enumerate(order):
            x = -20.3 + (i + .5) * sx
            y = -12.8 + (j + .5) * sy
            top = -.03 - l * layer
            add("soil", x, y, top, 0, (sx, sy, layer), end=ta + dtl * (n + 1) / len(order), endd=.25, mode=GROW)
        z = -l * layer
        bot("excavator", ta, ta + dtl, z - layer * .4, -17, -9.5, 17, 9.5, 0)
        bot("excavator", ta, ta + dtl, z - layer * .4, 17, 9.5, -17, -9.5, 0)
        bot("dump_truck", ta, ta + dtl, 0, -23.2, 13, -23.2, -13, 1, 2.5)
        bot("drone", ta, ta + dtl, 14, -19, -12, 19, 12)
    for z, ta, ts in ((-2.0, 78, 137), (-5.0, 90, 136.5)):
        for y in (-6.5, 6.5):
            add("strut", -19.5, y, z, 0, (39, 1, 1), t=ta, d=1, end=ts + 8 if z == -5 else 152, mode=LIFT, frm=(0, 0, 6))
        for x in (-14, -7, 7, 14):
            add("strut", x, -12, z - .42, PI / 2, (24, 1, 1), t=ta + 1, d=1, end=ts + 8 if z == -5 else 152, mode=LIFT, frm=(0, 0, 6))
    note(70, 104, "無人挖土機分層開挖，無人機每日結算土方")
    note(78, 92, "鋼支撐分層架設，軸力即時監測")


def erect_rig():
    masts = [(x, y) for x in (-RING_X, -7, 7, RING_X) for y in (-RING_Y, RING_Y)] + [(-RING_X, 0), (RING_X, 0)]
    for k, (x, y) in enumerate(masts):
        add("mast_pad", x, y, .0, t=105 + k * .2, d=.4, end=316, mode=GROW)
    n = 21
    for i in range(n):
        z = .56 + i * 3
        first, last = mast_section_times(z, KEYS)
        if first is None:
            continue
        for k, (x, y) in enumerate(masts):
            add("mast_sec", x, y, z, t=first + k * .03, d=.4, end=last + .3 + k * .03, endd=.4, mode=POP)
        add("hoist_sec", 0, RING_Y + 2.1, z - .56, t=first + .1, d=.4, end=last + .4, endd=.4, mode=POP)
    note(105, 118, "立柱分段立起，上下環桁架與重型龍門組立")
    note(118, 120, "試吊、防擺與急停測試")


def erect_ties():
    ties = [(-7, -RING_Y, 0, RING_Y - 10.05), (7, -RING_Y, 0, RING_Y - 10.05),
            (-7, 10.05, 0, RING_Y - 10.05), (7, 10.05, 0, RING_Y - 10.05),
            (-RING_X, 0, -PI / 2, RING_X - 18), (18, 0, -PI / 2, RING_X - 18)]
    return ties


def raft():
    bays = [(-15.6 + i * 7.8, -9 + j * 6) for i in range(5) for j in range(4)]
    t0, t1 = 120, 136
    note(120, 124, "筏基鋼筋網鋪設與綁紮")
    note(124, 132, "混凝土分區連續澆置")
    note(132, 136, "養護，溫度與強度感測回傳")
    for k, (x, y) in enumerate(bays):
        a = 120 + k * .18
        add("rb_slab", x, y, -7.02, 0, (1.115, .92, 1), t=a, d=.3, end=128 + k * .1, mode=POP)
    bot("bot_tie", 120, 124, -7.02, -18, -11, 18, 11)
    bot("bot_tie", 120, 124, -7.02, 18, 11, -18, -11)
    specs = bays[:]
    pour_tasks(specs, -7, 124, 132)
    dt = 8 / len(bays) * 2
    for k, (x, y) in enumerate(sorted(bays)):
        add("raft", x, y, -7.0, t=124 + k * .4, d=.5, mode=GROW)
    bot("bot_trowel", 128, 134, -7.0, -18, -11, 18, 11)
    bot("mixer", 124, 132, 0, 23.2, 4, 23.2, 4, 2)
    bot("mixer", 124, 132, 0, 23.2, 11, 23.2, 11, 2)


def storey_work(i):
    name, z0, z1 = STOREYS[i]
    t = cycle_start(i)
    h = z1 - z0
    szc = h / H_TYP
    ph = name == "屋突"
    grid = [(x, y) for x in XS for y in YS]
    if ph:
        grid = [(x, y) for x in (-3.5, 3.5) for y in (-3.25, 3.25)]
    core = [("core_door", 0, -3.25, 0, 1), ("core_wx", 0, 3.25, 0, 1), ("core_wx", -3.5, 0, PI / 2, .93),
            ("core_wx", 3.5, 0, PI / 2, .93), ("core_wx", 0, 0, PI / 2, .93)]

    note(t, t + .5, f"{name} 放樣機器人列印柱牆線位")
    note(t + .5, t + 2.5, f"{name} 預鑄柱與核心筒牆板吊裝定位")
    note(t + 2.5, t + 4.5, f"{name} 預鑄梁吊裝")
    note(t + 4.5, t + 6.0, f"{name} 半預鑄樓板吊裝")
    note(t + 6.0, t + 7.0, f"{name} 接頭灌漿，感測器確認強度")
    note(t + 7.0, t + 8.0, f"{name} 天架爬升一層")

    bot("bot_layout", t, t + .5, z0, -16, -9, 16, 9)
    bot("bot_dog", t + 6.4, t + 7.4, z1, -16, -9, 16, 9)
    bot("drone", t + 7.0, t + 7.8, z1 + 6, -19, -12, 19, 12)

    spec = [{"part": "column", "x": x, "y": y, "z": z0, "s": (1, 1, (h - .02) / H_TYP)} for x, y in grid]
    spec += [{"part": part, "x": x, "y": y, "z": z0, "rz": r, "s": (s, 1, (h - .02) / H_TYP)} for part, x, y, r, s in core]
    heavy_lift(spec, t + .5, t + 2.5)

    bays = [] if ph else [(XS[a] + BX / 2, YS[b] + BY / 2) for a in range(5) for b in range(3) if not (a == 2 and b == 1)]
    beams = []
    if not ph:
        for y in YS:
            for a in range(5):
                if not (a == 2 and abs(y) < 4):
                    beams.append((XS[a] + BX / 2, y, 0, 1))
        for x in XS:
            for b in range(3):
                if not (abs(x) < 4 and b == 1):
                    beams.append((x, YS[b] + BY / 2, PI / 2, .918))
    if beams:
        heavy_lift([{"part": "beam", "x": x, "y": y, "z": z1, "rz": r, "s": (s, 1, 1)} for x, y, r, s in beams], t + 2.5, t + 4.5)

    pour = bays or [(0, 0)]
    heavy_lift([{"part": "slab", "x": x, "y": y, "z": z1} for x, y in pour], t + 4.5, t + 6.0, 3)
    pour_tasks(pour, z1, t + 6.0, t + 7.0)
    if bays and z1 >= 40.8:
        add("slab", 0, 0, z1, 0, (1, 1, 1), t=t + 6.3, d=.1, mode=GROW)
    if z1 <= .1:
        for sy, sign in ((2.25 / BY, -1), (2.25 / BY, 1)):
            add("slab", 0, sign * (9.75 + 1.125), z1, 0, (39 / BX, sy, 1), t=t + 6.0, d=.2, mode=GROW)
        for sign in (-1, 1):
            add("slab", sign * 18.5, 0, z1, 0, (2 / BX, 19.5 / BY, 1), t=t + 6.0, d=.2, mode=GROW)
    if bays:
        bot("bot_trowel", t + 6.0, t + 7.0, z1, -16, -9, 16, 9)
        bot("bot_agv", t + 3.0, t + 5.0, z1, -16, -9, 16, 9, 1, 1.0)
    if not ph and i >= 1:
        add("stair", 0, 0, z0, 0, (1, 1, szc), t=t + 6.5, d=.3, mode=POP)

    if z1 > 0 and not ph:
        for x, y, r, length in erect_ties():
            tz = z1 - .45
            off = next((tt for tt in range(276, 312) if rig_z(tt, KEYS) - 15.5 <= tz), 305)
            add("tie", x, y, tz, r, (1, length, 1), t=t + 7.7, d=.3, end=off, endd=.4, mode=POP)


def face_placements():
    out = []
    for a in range(5):
        x = XS[a] + BX / 2
        out.append(("s", x, -10.05, 0.0, (0, -1), a, 1.0))
        out.append(("n", x, 10.05, PI, (0, 1), a, 1.0))
    for b in range(3):
        y = YS[b] + BY / 2
        out.append(("e", 18.0 - .0, y, PI / 2, (1, 0), b, .93))
        out.append(("w", -18.0, y, -PI / 2, (-1, 0), b, .93))
    return out


def envelope_storey(i):
    name, z0, z1 = STOREYS[i]
    ph = name == "屋突"
    if z0 < 0 or ph:
        return
    t = cycle_start(i)
    h = z1 - z0
    szc = h / H_TYP
    faces = face_placements()
    per_arm = {"S0": [], "S1": [], "N0": [], "N1": [], "E0": [], "W0": []}
    for f in faces:
        side, x, y, r, out, idx, sx = f
        arm = {"s": "S0" if x < 0 else "S1", "n": "N0" if x < 0 else "N1", "e": "E0", "w": "W0"}[side]
        per_arm[arm].append(f)

    damper_t = t + 9.0
    note(damper_t, damper_t + 2.5, f"{name} 黏滯阻尼器吊裝與螺栓扭力紀錄")
    for arm, lst in per_arm.items():
        dp = [f for f in lst if (f[0] in "sn" and f[5] in (1, 3)) or (f[0] in "ew" and f[5] == 1)]
        dt = 2.5 / max(len(dp), 1)
        for k, (side, x, y, r, out, idx, sx) in enumerate(dp):
            mx, my = out[0] * -.0, out[1] * -.0
            bx = x - out[0] * .0
            by = y - out[1] * .0 + (.0)
            inner = (x - out[0] * .3, y - out[1] * .3)
            side_lift(arm, "damper", inner[0], inner[1], z0, r, out, (sx * .86, 1, (h - .8 - .02) / 2.47 if h > 4 else .99), damper_t + k * dt, dt * .85)

    env_t = t + 18.0
    note(env_t, env_t + 5, f"{name} 預鑄外牆吊裝、自動打膠與水密測試")
    for arm, lst in per_arm.items():
        dt = 4.6 / max(len(lst), 1)
        for k, (side, x, y, r, out, idx, sx) in enumerate(lst):
            is_damper = (side in "sn" and idx in (1, 3)) or (side in "ew" and idx == 1)
            if name == "1F":
                part = "fac_lobby"
            elif is_damper:
                part = "fac_glass"
            elif side in "sn":
                part = "fac_a"
            else:
                part = "fac_b"
            zs = szc if part != "fac_lobby" else 1
            side_lift(arm, part, x, y, z0, r, out, (sx, 1, zs), env_t + k * dt, dt * .85)

    if name == "1F":
        for x in (-3.5, 3.5):
            pass
    tm = t + 23.0
    if i >= 3:
        bays = [(XS[a] + BX / 2, YS[b] + BY / 2) for a in range(5) for b in range(3) if not (a == 2 and b == 1)]
        note(tm, tm + 4, f"{name} 機電管束模組就位")
        note(tm + 4, tm + 8, f"{name} 輕隔間與整體衛浴安裝")
        note(tm + 8, tm + 12, f"{name} 天花與地坪")
        note(tm + 12, tm + 16, f"{name} 噴塗、櫥櫃與人形機器人收邊")
        bot("bot_agv", tm, tm + 4, z0, -16, -9, 16, 9, 1, .8)
        bot("bot_drill", tm, tm + 3, z0, -15, -8, 15, 8)
        bot("bot_board", tm + 4, tm + 8, z0, -15, -8, 15, 8)
        bot("bot_tile", tm + 8, tm + 12, z0, -15, -8, 15, 8)
        bot("bot_paint", tm + 12, tm + 16, z0, -15, -8, 15, 8)
        for q, (hx, hy) in enumerate([(-12.0, -6.0), (9.0, 5.8)]):
            bot("bot_humanoid", tm + 8, tm + 24, z0, hx, hy, hx, hy, 2)
        for k, (x, y) in enumerate(bays):
            add("mep_bundle", x, y, z0, 0, (1, 1, szc), t=tm + k * .24, d=.3, mode=LIFT, frm=(0, 0, -2.0))
            add("int_wall", x, y, z0, 0 if k % 2 else PI, (1, 1, 1), t=tm + 4 + k * .24, d=.3, mode=GROW)
            add("bath_pod", x - 1.9, y - 1.8 if y < 0 else y + 1.8, z0 + .04, t=tm + 5 + k * .2, d=.3, mode=LIFT, frm=(0, 3, 0))
            add("int_floor", x, y, z0, t=tm + 8 + k * .2, d=.3, mode=POP)
            add("int_ceil", x, y, z0, t=tm + 9 + k * .2, d=.3, mode=POP)
            add("kitchen", x + 2.2, y + 1.2 if y > 0 else y - 1.2, z0 + .03, PI if y > 0 else 0, t=tm + 12 + k * .2, d=.3, mode=POP)
        add("elev_rail", 0, 0, z0, 0, (1, 1, szc), t=tm, d=.3, mode=POP)


def roof():
    z = 40.8
    for hz in (4.5, 17.7, 30.9):
        bot("bot_humanoid", 312, 335, hz, -12.0, -6.0, -12.0, -6.0, 2)
    bot("bot_tile", 312, 335, 17.7, -15.0, -5.0, -9.0, -5.0, 1, 18.0)
    bot("bot_paint", 312, 335, 17.7, -15.5, -8.8, -8.0, -8.8, 1, 24.0)
    bot("bot_agv", 312, 335, 17.7, -14.5, -2.0, -8.0, -2.0, 1, 20.0)
    note(258, 262, "屋頂防水層機器人噴塗")
    note(262, 268, "女兒牆、機電設備與太陽能板吊裝")
    note(268, 276, "頂棚膜片與拱架分段吊下，龍門退到大樓外側")
    for a in range(5):
        for b in range(3):
            x, y = XS[a] + BX / 2, YS[b] + BY / 2
            add("waterproof", x, y, z, t=258 + (a + b) * .3, d=.3, mode=POP)
    spec = []
    for a in range(5):
        spec.append({"part": "parapet", "x": XS[a] + BX / 2, "y": -9.95, "z": z})
        spec.append({"part": "parapet", "x": XS[a] + BX / 2, "y": 9.95, "z": z})
    for b in range(3):
        spec.append({"part": "parapet", "x": -17.9, "y": YS[b] + BY / 2, "z": z, "rz": PI / 2, "s": (.93, 1, 1)})
        spec.append({"part": "parapet", "x": 17.9, "y": YS[b] + BY / 2, "z": z, "rz": PI / 2, "s": (.93, 1, 1)})
    spec.append({"part": "roof_kit", "x": -14, "y": 0, "z": z + .04})
    spec.append({"part": "roof_kit", "x": 7, "y": 6, "z": z + .04})
    for x in (-13, -6, 6, 13):
        spec.append({"part": "pv", "x": x, "y": -6.6, "z": z + .04})
    spec.append({"part": "pv", "x": -7, "y": 7, "z": z + .04})
    heavy_lift(spec, 262, 268, 6)
    bot("bot_paint", 258, 262, z + .04, -16, -9, 16, 9)
    for s, x in (("elev_car", 0),):
        add(s, x, 0, 0, t=318, d=.5, mode=POP)


def descend_finish():
    note(276, 304, "天架逐層下降，外牆最後補縫與錨定孔修補")
    note(304, 312, "環桁架落地分解，立柱節段回收")
    note(312, 335, "機電、消防與電梯系統全棟連動測試")
    note(335, 345, "鋪面、雨水花園與植樹")
    note(345, 360, "數位竣工模型交付與驗收")
    for k in range(8):
        bot("bot_dog", 312 + k * 2.8, 314.8 + k * 2.8, 4.5 + 3.3 * k, -16, -9, 16, 9)
    bot("drone", 345, 358, 46, -24, -14, 24, 26)


def landscape():
    x0, x1, y0, y1 = -26, 26, -15.5, 29
    random.seed(7)
    cells = []
    for i in range(9):
        for j in range(15):
            x, y = x0 + 3 + i * 6, y0 + 1.5 + j * 3
            if abs(x) < 19 and abs(y) < 11.5:
                continue
            cells.append((x, y))
    cells.sort(key=lambda c: (c[0] + c[1]))
    dt = 9 / len(cells)
    for k, (x, y) in enumerate(cells):
        lawn = (abs(y) > 16 or abs(x) > 21) and random.random() > .25
        add("land_lawn" if lawn else "land_pave", x, y, .02, t=335 + k * dt, d=.25, mode=POP)
    for x, y in ((-23, 15), (23, 15), (-14, 19), (0, 22), (14, 19), (-23, 25), (23, 25), (-23, -6), (23, -6)):
        add("tree", x, y, .05, t=340 + abs(x) * .08, d=.6, mode=POP)
    add("canopy", 0, -12.2, .05, t=342, d=.6, mode=POP)


def precast_plant():
    add("precast_plant", PLANT[0], PLANT[1], 0)
    bot("plant_gantry", 0, 280, 10.5, PLANT[0] - 26, PLANT[1], PLANT[0] + 26, PLANT[1], 1, 16.0)
    for k in range(3):
        bot("precast_truck", 0, 262, 0, k / 3, 0, 0, 0, 3)


def surroundings():
    add("ground", 0, 0, 0)
    add("road", 0, 0, 0)
    for k in range(9):
        x = -86 + k * 22
        if abs(x - 24) > 4:
            add("tree", x, -16.8, .08)
    for x, y, p, r in ((-52, 38, "block_a", 0), (-32, 62, "block_b", .0), (46, 40, "block_c", PI / 2), (70, 12, "block_b", 0),
                       (-74, 8, "block_c", PI / 2), (0, 58, "block_a", 0), (32, -50, "block_c", 0), (-34, -46, "block_a", 0),
                       (-70, -48, "block_b", 0), (72, -46, "block_a", 0), (88, 56, "block_a", 0), (-96, 52, "block_b", 0)):
        add(p, x, y, 0, r)
    add("soil", 0, 0, -9.0, 0, (40.6, 25.6, 3))
    for x in (-23.2, 23.2):
        pass
    for x, p in ((-22.6, "person_a"), (-19.1, "person_b"), (-13, "person_a"), (-3.4, "person_b"), (2.4, "person_a"), (11.7, "person_b")):
        add(p, x, -16.3, .08, PI / 2 if False else -PI / 2 + PI)


storey_count = len(STOREYS)

coll = bpy.data.collections.new("PARTS")
bpy.context.scene.collection.children.link(coll)
for o in list(bpy.data.objects):
    if o.name != "PARTS":
        bpy.data.objects.remove(o)
textures = kit.make_textures()
kit.make_materials(textures)
parts.build_all()

surroundings()
precast_plant()
site_prep()
dwall()
piles()
excavate()
erect_rig()
raft()
for i in range(storey_count):
    storey_work(i)
for i in range(storey_count):
    envelope_storey(i)
roof()
descend_finish()
landscape()

for k in tasks:
    tasks[k].sort(key=lambda a: a[0])
log.sort(key=lambda a: a[0])



def span(t, d):
    if t < 0 or t >= NEVER:
        return d
    return max(remap(t + d) - remap(t), .02)


out_items = {}
for part, rows in items.items():
    out_items[part] = [r[:7] + [round(remap(r[7]), 3), round(span(r[7], r[8]), 3), round(remap(r[9]), 3), round(span(r[9], r[10]), 3)] + r[11:] for r in rows]
out_tasks = {k: [[round(remap(q[0]), 3), round(remap(q[1]), 3)] + q[2:] for q in v] for k, v in tasks.items()}
out_bots = []
for b in sorted(bot_runs, key=lambda b: b[1]):
    a0, a1 = remap(b[1]), remap(b[2])
    out_bots.append(b[:1] + [round(a0, 3), round(a1, 3)] + b[3:9] + [round(b[9] * (a1 - a0) / max(b[2] - b[1], 1e-6), 3)])

schedule = {
    "meta": {"T": 90, "tRigOn": remap(T_RIG_ON), "tRigOff": remap(T_RIG_OFF), "tRingOn": remap(120), "tRoofOff0": remap(268), "tRoofOff1": remap(276),
             "ringX": RING_X, "ringY": RING_Y, "plant": PLANT,
             "storeys": [[n, a, b, round(remap(cycle_start(i)), 3)] for i, (n, a, b) in enumerate(STOREYS)]},
    "phases": [{"id": a, "name": b, "t0": c, "t1": d} for a, b, c, d in PHASES_OUT],
    "rigKeys": [[round(remap(a), 3), round(b, 3)] for a, b in KEYS],
    "parts": kit.PARTS,
    "items": out_items,
    "tasks": out_tasks,
    "bots": out_bots,
    "log": [[round(remap(a), 3), round(remap(b), 3), c] for a, b, c in log],
}
with open(os.path.join(WEB, "schedule.json"), "w", encoding="utf-8") as f:
    json.dump(schedule, f, ensure_ascii=False, separators=(",", ":"))

for ob in bpy.data.objects:
    ob.select_set(False)
vl = bpy.context.view_layer
for ob in coll.objects:
    ob.select_set(True)
vl.objects.active = coll.objects[0]
bpy.ops.export_scene.gltf(filepath=os.path.join(WEB, "parts.glb"), export_format="GLB", use_selection=True,
                          export_yup=True, export_apply=False, export_cameras=False, export_lights=False,
                          export_animations=False, export_image_format="AUTO", export_jpeg_quality=78)

import base64
with open(os.path.join(WEB, "parts.glb"), "rb") as src, open(os.path.join(WEB, "parts.glb.txt"), "wb") as dst:
    dst.write(base64.b64encode(src.read()))

assembled = bpy.data.collections.new("ASSEMBLED_FINAL")
bpy.context.scene.collection.children.link(assembled)
for part, rows in items.items():
    src = bpy.data.objects[part]
    for r in rows:
        if r[9] < NEVER:
            continue
        o = bpy.data.objects.new(f"{part}.i", src.data)
        o.location = r[:3]
        o.rotation_euler = (0, 0, r[3])
        o.scale = r[4:7]
        assembled.objects.link(o)
coll.hide_viewport = True
coll.hide_render = True
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "blender", "tower.blend"), compress=True)

tris = sum(p["tris"] for p in kit.PARTS.values())
n = sum(len(v) for v in items.values())
live = sum(kit.PARTS[k]["tris"] * len(v) for k, v in items.items())
print(f"BUILD_OK parts={len(kit.PARTS)} unique_tris={tris} instances={n} total_tris={live} "
      f"bots={len(bot_runs)} tasks={sum(len(v) for v in tasks.values())}")
print("TOP", sorted(((v.get('tris', 0), k) for k, v in kit.PARTS.items()), reverse=True)[:8])
print("HEAVY", sorted(((kit.PARTS[k]['tris'] * len(v), k, len(v)) for k, v in items.items()), reverse=True)[:6])
