import math

PLANT = (172, -78)
import random

from kit import P
from schedule_spec import RING_X, RING_Y, WALL_X, WALL_Y


def rect_frame(p, x0, x1, z0, z1, y, t, d, mat):
    p.bx(x0, x1, y - d, y + d, z0, z0 + t, mat)
    p.bx(x0, x1, y - d, y + d, z1 - t, z1, mat)
    p.bx(x0, x0 + t, y - d, y + d, z0, z1, mat)
    p.bx(x1 - t, x1, y - d, y + d, z0, z1, mat)


def structure():
    P("column", "RC 柱", "90×90 公分鋼筋混凝土柱。澆置時埋入成熟度感測器，機器人依即時強度決定拆模時間。", "struct") \
        .bx(-.45, .45, -.45, .45, 0, 3.3, "concrete", True).done(.02)
    P("beam", "RC 大梁", "60×80 公分大梁，與樓板一次澆置，避免施工縫。", "struct") \
        .bx(-3.05, 3.05, -.3, .3, -.8, -.003, "concrete", True).done(.015)
    P("slab", "RC 樓板", "厚 15 公分樓板。整平機器人依雷射基準控制平整度。", "struct") \
        .bx(-3.5, 3.5, -3.25, 3.25, -.15, 0, "concrete").done()
    P("core_wx", "核心筒剪力牆", "厚 30 公分 RC 牆，圍住樓梯與電梯，也是天架錨定的主要反力點。", "struct") \
        .bx(-3.5, 3.5, -.15, .15, 0, 3.3, "concrete").done()
    d = P("core_door", "核心筒開口牆", "電梯與樓梯出入口，開口位置由 BIM 直接輸出給模板機器人。", "struct")
    d.bx(-3.5, -2.5, -.15, .15, 0, 3.3, "concrete").bx(-1.0, .4, -.15, .15, 0, 3.3, "concrete")
    d.bx(1.8, 3.5, -.15, .15, 0, 3.3, "concrete").bx(-2.5, -1, -.15, .15, 2.3, 3.3, "concrete")
    d.bx(.4, 1.8, -.15, .15, 2.3, 3.3, "concrete").done()
    s = P("stair", "預鑄樓梯", "工廠預鑄樓梯段，由重型手臂吊入，免現場支模。", "struct")
    for flip, (x0, x1) in enumerate(((-3.3, -2.15), (-1.95, -.8))):
        for i in range(10):
            y = -2.2 + i * .28 if flip == 0 else 2.0 - i * .28
            s.bx(x0, x1, min(y, y + .28), max(y, y + .28), 0 + (flip * 1.65) + i * .165, (flip * 1.65) + (i + 1) * .165,
                 "concrete_sm")
    s.bx(-3.3, -.8, 2.0, 3.0, 1.55, 1.65, "concrete_sm").bx(-3.3, -.8, -3.0, -2.2, 3.15, 3.3, "concrete_sm")
    s.done()
    r = P("elev_rail", "電梯導軌", "機器人依雷射垂線自動校準導軌，免人員在井道內作業。", "mep")
    for x, y in ((1.05, -1.0), (2.65, -1.0), (1.05, 1.1), (2.65, 1.1)):
        r.hbeam((x, y, 0), (x, y, 3.3), .1, .08, "steel")
    r.cyl((.5, 2.4, 0), (.5, 2.4, 3.3), .05, "pipe_red", 8, False).cyl((.8, 2.4, 0), (.8, 2.4, 3.3), .05, "pipe_blue", 8, False)
    r.bx(.2, 3.2, 2.5, 2.54, 0, 3.3, "duct").done()
    c = P("elev_car", "電梯車廂", "完工後由電梯本身載運內裝機器人上下，取代施工電梯。", "mep")
    c.bx(.9, 2.8, -.9, 1.0, 0, 2.5, "chrome").bx(.85, 2.85, -.95, 1.05, 2.5, 2.65, "dark").done()
    P("pile", "基樁", "全套管基樁，鑽掘機依地質模型自動調整鑽速。", "struct") \
        .cyl((0, 0, -22), (0, 0, 0), .75, "concrete_sm", 16).bx(-1.2, 1.2, -1.2, 1.2, -.9, 0, "concrete").done()
    P("raft", "筏基", "厚 120 公分筏式基礎，把樓重均勻傳到地盤。", "struct") \
        .bx(-3.9, 3.9, -3, 3, -1.2, 0, "concrete").done()
    w = P("dwall", "連續壁單元", "厚 80 公分地下擋土牆。液壓抓斗機邊掘邊量垂直度，超限自動修正。", "struct")
    w.bx(-1.5, 1.5, -.4, .4, -22, 0.02, "concrete_sm").bx(-1.49, 1.49, -.41, .41, -9, 0.02, "concrete").done()
    P("cap", "連續壁頂梁", "把連續壁連成一圈，也是天架立柱的基座。", "struct") \
        .bx(-1.5, 1.5, -.75, .75, 0, .35, "concrete").done()
    P("strut", "鋼支撐", "開挖期間的臨時支撐，內建軸力計，超限時自動預警並調整預力。", "form") \
        .hbeam((0, 0, 0), (1, 0, 0), .4, .4, "yellow").done()
    P("soil", "土方", "土方量由無人機每日掃描結算，自動派車。", "site") \
        .bx(-.5, .5, -.5, .5, -1, 0, "soil").done()
    P("parapet", "女兒牆", "屋頂防水收邊。", "struct").bx(-3.5, 3.5, -.1, .1, 0, 1.2, "concrete").done()


def rebar():
    c = P("rb_col", "柱鋼筋籠", "地面機器人工作站預組的鋼筋籠，整組吊裝，取代高空綁紮。", "rebar")
    for i in range(4):
        q = -.33 + i * .22
        for a, b in ((q, -.33), (q, .33), (-.33, q), (.33, q)):
            if abs(a) != .33 or abs(b) != .33 or i == 0:
                c.cyl((a, b, 0), (a, b, 4.2), .016, "rebar", 5, False)
    for k in range(13):
        z = .15 + k * .27
        for a, b, cc, d in ((-.36, -.36, .36, -.36), (.36, -.36, .36, .36), (.36, .36, -.36, .36), (-.36, .36, -.36, -.36)):
            c.beam((a, b, z), (cc, d, z), .012, .012, "rebar")
    c.done()
    b = P("rb_beam", "梁鋼筋籠", "含預留套管的梁筋籠，到位後輕型手臂自動點焊固定。", "rebar")
    for y in (-.22, 0, .22):
        for z in (-.7, -.1):
            b.cyl((-3.5, y, z), (3.5, y, z), .014, "rebar", 5, False)
    for k in range(23):
        x = -3.3 + k * .3
        for a, cc in (((x, -.25, -.74), (x, .25, -.74)), ((x, .25, -.74), (x, .25, -.06)),
                      ((x, .25, -.06), (x, -.25, -.06)), ((x, -.25, -.06), (x, -.25, -.74))):
            b.beam(a, cc, .01, .01, "rebar")
    b.done()
    s = P("rb_slab", "樓板鋼筋網", "雙向雙層鋼筋網，由綁紮機器人沿鋼筋行走完成交點固定。", "rebar")
    for zz in (-.05, -.11):
        for k in range(26):
            x = -3.15 + k * .252
            s.beam((x, -3.1, zz), (x, 3.1, zz), .012, .012, "rebar")
        for k in range(24):
            y = -2.9 + k * .252
            s.beam((-3.3, y, zz + .012), (3.3, y, zz + .012), .012, .012, "rebar")
    for x, y in ((-1.2, .6), (1.4, -1.1), (.2, 1.9)):
        s.cyl((x, y, -.15), (x, y, .05), .06, "pipe_green", 10)
    s.cyl((-3.2, -2, -.08), (3.2, 1.6, -.08), .012, "pipe_blue", 5, False).done()
    w = P("rb_wall", "牆鋼筋", "預組牆筋網片。", "rebar")
    for k in range(29):
        x = -3.4 + k * .243
        w.cyl((x, 0, 0), (x, 0, 4), .01, "rebar", 4, False)
    for k in range(16):
        w.beam((-3.5, 0, .15 + k * .25), (3.5, 0, .15 + k * .25), .012, .012, "rebar")
    w.done()


def forms():
    f = P("fm_col", "柱鋁模", "可重複使用的鋁模。拆模後自動清潔、噴脫模劑，再送往上一層。", "form")
    for x, y in ((-.5, 0), (.5, 0)):
        f.bx(x - .03, x + .03, -.5, .5, 0, 3.2, "form")
    for y in (-.5, .5):
        f.bx(-.5, .5, y - .03, y + .03, 0, 3.2, "form")
    for k in range(5):
        z = .3 + k * .65
        f.bx(-.56, .56, -.56, .56, z, z + .06, "dark")
    f.done()
    d = P("fm_deck", "樓板鋁模與支撐", "快拆式鋁模台，支撐保留至強度達標，面板先行回收。", "form")
    for i in range(6):
        for j in range(5):
            x = -3.5 + i * 7 / 6
            y = -3.25 + j * 1.3
            d.bx(x + .01, x + 7 / 6 - .01, y + .01, y + 1.29, -.19, -.15, "form")
    for x in (-2.6, 0, 2.6):
        for y in (-2.2, 0, 2.2):
            d.cyl((x, y, -3.3), (x, y, -.19), .04, "steel", 6, False)
            d.bx(x - .1, x + .1, y - .1, y + .1, -3.3, -3.28, "dark")
    d.done()
    b = P("fm_beam", "梁底鋁模", "與樓板鋁模同一套模組，由手臂整組定位。", "form")
    b.bx(-3.05, 3.05, -.36, .36, -.85, -.8, "form").bx(-3.05, 3.05, -.36, -.3, -.8, -.1, "form")
    b.bx(-3.05, 3.05, .3, .36, -.8, -.1, "form")
    for x in (-2.2, 0, 2.2):
        b.cyl((x, 0, -3.3), (x, 0, -.85), .05, "steel", 6, False)
    b.done()
    P("fm_wall", "牆鋁模", "核心筒系統模板。", "form") \
        .bx(-3.5, 3.5, -.2, -.15, 0, 3.2, "form").bx(-3.5, 3.5, .15, .2, 0, 3.2, "form").done()


def damper():
    p = P("damper", "黏滯阻尼器組", "人字形鋼斜撐加雙黏滯阻尼器。地震時活塞擠壓矽油，把振動能量轉成熱，降低層間變位。輕型手臂以扭力紀錄鎖固，每顆螺栓都留檔。", "damper")
    top = (0, 0, 2.42)
    for sx in (-1, 1):
        base = (sx * 3.05, 0, .1)
        a = (sx * 2.72, 0, .34)
        b = (sx * 1.5, 0, 1.17)
        c = (sx * .95, 0, 1.55)
        p.bx(sx * 3.3 - .3, sx * 3.3 + .3, -.16, .16, 0, .04, "steel_red")
        p.bx(sx * 3.02 - .28, sx * 3.02 + .28, -.012, .012, .03, .42, "steel_red")
        p.cyl(base, a, .07, "steel_red", 10)
        p.cyl(a, b, .15, "dark", 16)
        p.cyl((sx * 2.72, 0, .34), (sx * 2.67, 0, .375), .19, "steel", 16)
        p.cyl((sx * 1.55, 0, 1.135), (sx * 1.5, 0, 1.17), .19, "steel", 16)
        p.cyl(((sx * 2.5), .19, .49), ((sx * 1.72), .19, 1.02), .03, "copper", 8)
        p.cyl(b, c, .055, "chrome", 12)
        p.cyl(c, (sx * .3, 0, 2.03), .1, "yellow", 12)
        p.cyl((sx * .3, -.09, 2.03), (sx * .3, .09, 2.03), .12, "steel", 12)
    p.bx(-.6, .6, -.16, .16, 2.42, 2.47, "steel_red").bx(-.55, .55, -.012, .012, 1.95, 2.42, "steel_red")
    p.done()


def facade():
    a = P("fac_a", "預鑄外牆與陽台", "工廠一次完成窗框、磁磚與防水的預鑄外牆，機械臂吊裝後自動打膠並做水密測試。", "facade")
    a.bx(-3.5, -3.1, -.12, .12, 0, 3.3, "pc", True).bx(3.1, 3.5, -.12, .12, 0, 3.3, "pc", True)
    a.bx(-3.1, 3.1, -.12, .12, 2.75, 3.3, "pc").bx(-3.1, 3.1, -.12, .12, 0, .12, "pc")
    rect_frame(a, -3.1, 3.1, .12, 2.75, 0, .06, .05, "alu")
    for x, g in ((-1.03, 0), (1.03, 0)):
        a.bx(x - .03, x + .03, -.05, .05, .12, 2.75, "alu")
    a.bx(-3.04, 3.04, -.012, .012, .18, 2.69, "glass")
    a.bx(-3.5, 3.5, -1.5, -.12, -.02, .14, "pc", True)
    a.bx(-3.5, 3.5, -1.5, -1.46, .14, .26, "alu")
    for k in range(29):
        x = -3.4 + k * .243
        a.bx(x - .012, x + .012, -1.47, -1.45, .26, 1.3, "alu")
    a.bx(-3.5, 3.5, -1.49, -1.44, 1.3, 1.34, "alu")
    a.bx(-3.5, 3.5, -1.45, -1.43, .26, 1.3, "glass")
    a.bx(1.9, 3.3, -1.4, -.95, .14, .55, "pc").bx(1.95, 3.25, -1.36, -.99, .55, .57, "soil")
    for i in range(6):
        a.ball((2.05 + i * .22, -1.17, .68), .16, "leaf", 1)
    a.bx(-3.3, -2.3, -1.4, -.75, .14, .9, "white")
    for k in range(7):
        a.bx(-3.28, -2.32, -1.41, -1.39, .22 + k * .09, .25 + k * .09, "dark")
    a.done(.012)
    b = P("fac_b", "預鑄外牆含格柵", "臥室立面。木紋鋁格柵固定在預鑄板上，在工廠完成，現場零濕作業。", "facade")
    b.bx(-3.5, 3.5, -.12, .12, 0, .9, "pc").bx(-3.5, 3.5, -.12, .12, 2.45, 3.3, "pc")
    for x0, x1 in ((-3.5, -2.9), (-.3, .3), (2.9, 3.5)):
        b.bx(x0, x1, -.12, .12, .9, 2.45, "pc", True)
    for x0, x1 in ((-2.9, -.3), (.3, 2.9)):
        rect_frame(b, x0, x1, .9, 2.45, 0, .05, .05, "alu")
        b.bx(x0 + .03, x1 - .03, -.01, .01, .93, 2.42, "glass")
        b.bx((x0 + x1) / 2 - .02, (x0 + x1) / 2 + .02, -.05, .05, .9, 2.45, "alu")
    for k in range(13):
        x = -3.3 + k * .55
        b.bx(x - .04, x + .04, -.34, -.14, .95, 3.2, "wood")
    b.bx(-3.5, 3.5, -.36, -.12, 3.2, 3.26, "alu").bx(-3.5, 3.5, -.3, -.12, .86, .92, "alu")
    b.done(.012)
    g = P("fac_glass", "展示玻璃帷幕", "制震斜撐所在的開間刻意用全玻璃，讓住戶和路人都看得到阻尼器。", "facade")
    for i in range(5):
        x = -3.5 + i * 1.75
        g.bx(x - .03, x + .03, -.1, .1, 0, 3.3, "alu")
    for z in (.02, 1.1, 2.2, 3.28):
        g.bx(-3.5, 3.5, -.1, .1, z - .02, z + .02, "alu")
    g.bx(-3.47, 3.47, -.012, .012, 0, 3.3, "glass").done()
    l = P("fac_lobby", "一樓門廳帷幕", "4.5 公尺挑高玻璃門廳。", "facade")
    for i in range(7):
        x = -3.5 + i * 7 / 6
        l.bx(x - .04, x + .04, -.1, .1, 0, 4.5, "alu")
    l.bx(-3.5, 3.5, -.1, .1, 3.5, 3.56, "alu").bx(-3.5, 3.5, -.1, .1, 4.42, 4.5, "alu")
    l.bx(-3.46, 3.46, -.012, .012, 0, 4.45, "glass").bx(-3.5, 3.5, -.14, -.1, 3.56, 4.42, "wood").done()


def interior():
    P("int_floor", "地坪與整體地板", "鋪磚機器人依掃描模型切磚與鋪貼。", "interior") \
        .bx(-3.5, 3.5, -3.25, 3.25, 0, .03, "wood").done()
    c = P("int_ceil", "輕鋼架天花板", "天花鑽孔機器人依 BIM 打吊筋孔，免去仰頭作業。", "interior")
    c.bx(-3.45, 3.45, -3.2, 3.2, 2.6, 2.63, "drywall")
    for x in (-1.8, 0, 1.8):
        for y in (-1.6, 1.6):
            c.cyl((x, y, 2.585), (x, y, 2.6), .1, "lamp", 12)
    c.done()
    w = P("int_wall", "輕隔間牆", "機器人鎖固板材與批土，不需人員搬運重物。", "interior")
    w.bx(-3.45, -.5, -.05, .05, .03, 2.6, "drywall").bx(.5, 3.45, -.05, .05, .03, 2.6, "drywall")
    w.bx(-.5, .5, -.05, .05, 2.1, 2.6, "drywall").bx(-.05, .05, .05, 3.2, .03, 2.6, "drywall")
    w.bx(-.47, .47, -.03, .03, .03, 2.1, "wood").bx(-.5, -.45, -.06, .06, .03, 2.1, "alu").done()
    m = P("mep_bundle", "天花機電管束", "風管、消防、給排水與線架在地面預組成模組，由 AGV 送到樓層，抬升機一次到位。", "mep")
    m.bx(-3.5, 3.5, 1.3, 1.9, 2.82, 3.08, "duct")
    for k in range(5):
        x = -3.3 + k * 1.65
        m.bx(x - .02, x + .02, 1.28, 1.92, 2.8, 3.1, "dark")
    m.cyl((-3.5, .8, 2.98), (3.5, .8, 2.98), .05, "pipe_red", 10, False)
    m.cyl((-3.5, .55, 2.98), (3.5, .55, 2.98), .035, "pipe_blue", 10, False)
    m.cyl((-3.5, .35, 3.0), (3.5, .35, 3.0), .06, "pipe_green", 10, False)
    m.bx(-3.5, 3.5, -.6, -.15, 3.03, 3.05, "duct")
    for k in range(13):
        m.bx(-3.4 + k * .56, -3.36 + k * .56, -.6, -.15, 3.05, 3.08, "duct")
    for x in (-2.4, 0, 2.4):
        m.cyl((x, .8, 2.93), (x, .8, 2.62), .012, "pipe_red", 6, False).ball((x, .8, 2.6), .03, "chrome", 1)
        m.cyl((x - .4, .1, 3.3), (x - .4, .1, 2.8), .006, "steel", 4, False)
    m.done()
    b = P("bath_pod", "整體衛浴模組", "防水、磁磚、管線在工廠完成的衛浴盒，整組推入定位，省下一半以上的濕作業工項。", "interior")
    b.bx(-1.15, 1.15, -.9, -.84, 0, 2.4, "white").bx(-1.15, 1.15, .84, .9, 0, 2.4, "white")
    b.bx(-1.15, -1.09, -.9, .9, 0, 2.4, "white").bx(-1.15, 1.15, -.9, .9, 0, .1, "tile")
    b.bx(-1.15, 1.15, -.9, .9, 2.34, 2.4, "white").bx(.3, 1.08, -.8, .8, .1, .55, "white")
    b.bx(-.95, -.45, .4, .82, .1, .5, "white").bx(-.5, -.15, -.84, -.5, .7, .85, "white").done()
    k = P("kitchen", "廚具模組", "櫃體與管線接頭標準化，由輕型手臂吊掛定位。", "interior")
    k.bx(-1.5, 1.5, -.3, .3, 0, .86, "wood").bx(-1.52, 1.52, -.32, .32, .86, .9, "tile")
    k.bx(-1.5, 1.5, -.18, .3, 1.5, 2.2, "white").bx(-.7, -.1, -.2, .2, .9, .92, "chrome").done()
    t = P("roof_kit", "屋頂設備", "水箱、空調主機與機電間。", "mep")
    t.bx(-2, 2, -1.5, 1.5, 0, 2.4, "duct", True)
    for i in range(3):
        t.bx(3 + i * 1.6, 4.4 + i * 1.6, -1.2, 1.2, 0, 1.5, "white", True)
        t.cyl((3.7 + i * 1.6, 0, 1.5), (3.7 + i * 1.6, 0, 1.6), .5, "dark", 18)
    t.cyl((-2, 0, 1.2), (3, 0, 1.2), .08, "pipe_blue", 10, False).done(.02)
    s = P("pv", "太陽能板陣列", "屋頂發電，補足公共用電。", "mep")
    for i in range(5):
        for j in range(2):
            x, y = -3 + i * 1.5, -1 + j * 2.1
            s.beam((x, y, .35), (x, y + 1.9, .95), 1.4, .04, "pv")
            s.cyl((x, y + .2, 0), (x, y + .2, .42), .03, "steel", 6, False).cyl((x, y + 1.7, 0), (x, y + 1.7, .88), .03, "steel", 6, False)
    s.done()
    P("waterproof", "屋頂防水層", "噴塗機器人控制膜厚，感測器全面驗證。", "interior") \
        .bx(-3.5, 3.5, -3.25, 3.25, 0, .04, "pipe_green").done()


def rig():
    m = P("mast_sec", "伸縮立柱節", "天架主立柱。頂升油壓缸把上部頂起，新節由底部塞入，就像塔吊爬升。每層都用錨定桿拉回樓板。", "rig")
    for x in (-1, 1):
        for y in (-1, 1):
            m.bx(x - .1, x + .1, y - .1, y + .1, 0, 3, "yellow")
    for a, b in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
        m.beam((a[0], a[1], .05), (b[0], b[1], .05), .08, .08, "yellow")
        m.beam((a[0], a[1], .05), (b[0], b[1], 1.5), .06, .06, "yellow")
        m.beam((b[0], b[1], 1.5), (a[0], a[1], 2.95), .06, .06, "yellow")
    m.bx(-.05, .05, -1.14, -1.1, 0, 3, "steel").done()
    P("mast_pad", "立柱基座", "立柱落在連續壁頂梁，施工荷重傳入深基礎。", "rig") \
        .bx(-1.6, 1.6, -1.6, 1.6, 0, .5, "concrete", True).bx(-1.3, 1.3, -1.3, 1.3, .5, .56, "steel").done(.02)
    t = P("tie", "樓板錨定桿", "立柱與已完成樓板之間的水平拉桿，內建荷重計，風大時即時回傳反力。", "rig")
    t.hbeam((0, 0, 0), (0, 1, 0), .24, .24, "yellow").done()
    h = P("hoist_sec", "物料升降塔與泵送管", "鋼筋、模板與機器人都由齒軌升降機送上來。混凝土泵送管沿塔爬升。", "rig")
    for x in (-.75, .75):
        for y in (-.75, .75):
            h.cyl((x, y, 0), (x, y, 3), .06, "steel", 8, False)
    for k in range(2):
        z = .1 + k * 1.5
        h.beam((-.75, -.75, z), (.75, -.75, z + 1.4), .05, .05, "steel").beam((.75, .75, z), (-.75, .75, z + 1.4), .05, .05, "steel")
        h.beam((-.75, -.75, z), (-.75, .75, z + 1.4), .05, .05, "steel").beam((.75, .75, z), (.75, -.75, z + 1.4), .05, .05, "steel")
    h.cyl((1.05, .2, 0), (1.05, .2, 3), .07, "orange", 10, False).bx(-.1, .1, -.86, -.78, 0, 3, "dark").done()
    c = P("hoist_cage", "升降機吊籠", "載重 3 噸，物料進籠前由 RFID 比對安裝序號。", "rig")
    c.bx(-1.3, 1.3, -2.9, -1, 0, .1, "yellow")
    for x in (-1.3, 1.3):
        for y in (-2.9, -1):
            c.cyl((x, y, 0), (x, y, 2.6), .04, "yellow", 6, False)
    c.bx(-1.3, 1.3, -2.9, -1, 2.55, 2.6, "yellow").bx(-.2, .2, -1, -.8, 0, 2.6, "dark").done()

    a = P("ring_a", "天架上環桁架", "環繞大樓的作業桁架，分區供應電力與壓縮空氣，頂部是重型龍門軌道。", "rig")
    def truss(x0, y0, x1, y1, n):
        for i in range(n):
            f0, f1 = i / n, (i + 1) / n
            p0 = (x0 + (x1 - x0) * f0, y0 + (y1 - y0) * f0)
            p1 = (x0 + (x1 - x0) * f1, y0 + (y1 - y0) * f1)
            a.beam((*p0, 0), (*p1, 0), .16, .16, "yellow").beam((*p0, 2.4), (*p1, 2.4), .2, .2, "yellow")
            a.beam((*p0, 0), (*p0, 2.4), .12, .12, "yellow")
            if i % 2:
                a.beam((*p0, 0), (*p1, 2.4), .08, .08, "yellow")
            else:
                a.beam((*p0, 2.4), (*p1, 0), .08, .08, "yellow")
    for sx in (-1, 1):
        truss(sx * RING_X, -RING_Y, sx * RING_X, RING_Y, 9)
    for sy in (-1, 1):
        truss(-RING_X, sy * RING_Y, RING_X, sy * RING_Y, 14)
        a.hbeam((-RING_X, sy * RING_Y, 2.62), (RING_X, sy * RING_Y, 2.62), .3, .2, "dark")
    a.bx(-RING_X - 1, RING_X + 1, -RING_Y - 1, -RING_Y + 1, -.06, 0, "dark")
    a.bx(-RING_X - 1, RING_X + 1, RING_Y - 1, RING_Y + 1, -.06, 0, "dark")
    a.bx(-RING_X - 1, -RING_X + 1, -RING_Y, RING_Y, -.06, 0, "dark")
    a.bx(RING_X - 1, RING_X + 1, -RING_Y, RING_Y, -.06, 0, "dark")
    a.bx(-8, 8, RING_Y - 2.4, RING_Y, -.5, -.42, "steel")
    for x in (-RING_X, -7, 7, RING_X):
        for y in (-RING_Y, RING_Y):
            a.bx(x - 1.25, x + 1.25, y - 1.25, y + 1.25, -1.6, 2.7, "orange")
            for sgn in (-1, 1):
                a.cyl((x + sgn * .8, y - 1.3, -1.6), (x + sgn * .8, y - 1.3, 1.6), .1, "chrome", 10)
    for x in (-RING_X, RING_X):
        a.bx(x - 1.25, x + 1.25, -1.25, 1.25, -1.6, 2.7, "orange")
    cable = [-RING_X + 2 + k * (2 * RING_X - 4) / 3 for k in range(4)]
    for x0, x1 in zip(cable, cable[1:]):
        a.beam((x0, -RING_Y + .9, 1.1), (x1, -RING_Y + .9, 1.1), .05, .05, "white")
    a.done()
    b = P("ring_b", "天架下環作業層", "外牆與制震安裝層，懸掛在立柱上，人員只在這層巡檢。", "rig")
    # 欄杆在作業層外緣，台車走內側軌道才不會撞到立柱
    gx, gy = RING_X + .9, RING_Y + .9
    gap = 1.5  # 北側留升降機吊籠通過的開口
    for sy in (-1, 1):
        for sx in ((-1, 1) if sy > 0 else (0,)):
            x0, x1 = sorted((sx * gap, sx * (RING_X + 1))) if sx else (-RING_X - 1, RING_X + 1)
            b.bx(x0, x1, sy * RING_Y - 1, sy * RING_Y + 1, -.1, 0, "dark")
            x0, x1 = sorted((sx * gap, sx * gx)) if sx else (-gx, gx)
            b.bx(x0, x1, sy * gy - .04, sy * gy + .04, 1.05, 1.13, "yellow")
        b.hbeam((-RING_X, sy * (RING_Y - .95), .15), (RING_X, sy * (RING_Y - .95), .15), .22, .16, "steel")
    for sx in (-1, 1):
        b.bx(sx * RING_X - 1, sx * RING_X + 1, -RING_Y, RING_Y, -.1, 0, "dark")
        b.bx(sx * gx - .04, sx * gx + .04, -gy, gy, 1.05, 1.13, "yellow")
        b.hbeam((sx * (RING_X - .95), -RING_Y, .15), (sx * (RING_X - .95), RING_Y, .15), .22, .16, "steel")
    for k in range(int(2 * RING_X / 3) + 1):
        x = -RING_X + k * 3
        for sy in (-1, 1):
            if sy < 0 or abs(x) > gap:
                b.cyl((x, sy * gy, 0), (x, sy * gy, 1.1), .025, "yellow", 5, False)
    for k in range(int(2 * RING_Y / 3) + 1):
        y = -RING_Y + k * 3
        for sx in (-1, 1):
            b.cyl((sx * gx, y, 0), (sx * gx, y, 1.1), .025, "yellow", 5, False)
    b.done()
    r = P("roof_frame", "天架頂棚拱架", "可開闔頂棚的骨架，雨天把作業層蓋起來。", "rig")
    n = 8
    for k in range(n):
        q0, q1 = k / n, (k + 1) / n
        y0, y1 = -RING_Y + 2 * RING_Y * q0, -RING_Y + 2 * RING_Y * q1
        z0, z1 = 2.5 + 5.4 * math.sin(math.pi * q0), 2.5 + 5.4 * math.sin(math.pi * q1)
        r.beam((0, y0, z0), (0, y1, z1), .14, .22, "steel")
    r.done()
    e = P("roof_panel", "ETFE 可動頂棚", "透光膜頂棚。平常滑開讓吊裝進出，下雨或澆置時自動闔上，白天不用開燈。", "rig")
    n = 16
    for k in range(n):
        q0, q1 = k / n, (k + 1) / n
        y0, y1 = -RING_Y + 2 * RING_Y * q0, -RING_Y + 2 * RING_Y * q1
        z0, z1 = 2.56 + 5.4 * math.sin(math.pi * q0), 2.56 + 5.4 * math.sin(math.pi * q1)
        e.beam((0, y0, z0), (0, y1, z1), 6.9, .02, "etfe")
    e.done()
    for name, length in (("net_x", 44.0), ("net_y", 29.0)):
        q = P(name, "透視防護網", "你要的「不完全封閉」。作業層只用透光金屬網擋墜物，路人從街上看得到每一層的進度，遇颱風再自動捲收。", "net")
        q.bx(-length / 2, length / 2, -.005, .005, -11.5, 2.4, "net").done()
    g = P("bridge", "重型龍門", "橫跨大樓的龍門樑，沿上環軌道前後移動，負責 80% 以上的吊裝。", "rig")
    for sy in (-1, 1):
        g.bx(-1.1, 1.1, sy * RING_Y - .6, sy * RING_Y + .6, 2.8, 3.8, "orange", True)
        g.wheel((-.7, sy * RING_Y, 2.86), .2, .2, "x").wheel((.7, sy * RING_Y, 2.86), .2, .2, "x")
    for x in (-.7, .7):
        n = 12
        for k in range(n):
            y0, y1 = -RING_Y + 2 * RING_Y * k / n, -RING_Y + 2 * RING_Y * (k + 1) / n
            g.beam((x, y0, 3.0), (x, y1, 3.0), .22, .3, "orange").beam((x, y0, 4.4), (x, y1, 4.4), .22, .22, "orange")
            g.beam((x, y0, 3.0), (x, y0, 4.4), .1, .1, "orange")
            g.beam((x, y0, 3.0) if k % 2 else (x, y0, 4.4), (x, y1, 4.4) if k % 2 else (x, y1, 3.0), .08, .08, "orange")
    g.done(.02)
    w = P("trolley", "龍門小車", "載著重型手臂沿龍門橫移，定位精度由雷射追蹤。", "rig")
    w.bx(-1.1, 1.1, -1.1, 1.1, 2.6, 3.0, "dark", True).bx(-.8, .8, -.8, .8, 3.0, 3.3, "yellow", True)
    w.cyl((-.5, -.7, 2.4), (-.5, .7, 2.4), .35, "steel", 14).done(.02)
    P("tele", "伸縮臂節", "把重型手臂往下送到需要的樓層，從筏基到屋頂都用同一支手臂。", "rig") \
        .bx(-.3, .3, -.3, .3, -1, 0, "dark").bx(-.32, -.28, -.1, .1, -1, 0, "steel").done()
    P("tele_top", "伸縮臂外套管", "伸縮臂外層。", "rig") \
        .bx(-.42, .42, -.42, .42, -4.5, 2.6, "yellow", True).done(.03)
    c = P("carriage", "輕型手臂滑車", "沿環形軌道移動，到位後夾緊軌道再施工。", "rig")
    c.bx(-.5, .5, -.45, .45, 0, .34, "orange", True).wheel((-.3, -.3, .05), .1, .08).wheel((.3, -.3, .05), .1, .08)
    c.wheel((-.3, .3, .05), .1, .08).wheel((.3, .3, .05), .1, .08).done(.015)


def arm(prefix, zh, note, l1, l2, r):
    b = P(f"{prefix}_base", zh, note, "robot")
    b.cyl((0, 0, 0), (0, 0, r * .4), r * 1.4, "dark", 18).cyl((0, 0, r * .4), (0, 0, r * 1.5), r * 1.05, "orange", 18)
    b.bx(-r * .7, r * .7, -r, r, r * 1.5, r * 2.5, "orange", True).done(r * .06)
    u = P(f"{prefix}_upper", zh, note, "robot")
    u.cyl((0, -r * .85, 0), (0, r * .85, 0), r * .85, "dark", 18)
    u.cyl((r * .2, 0, 0), (l1 - r * .2, 0, 0), r * .55, "orange", 12, True, r * .42)
    u.cyl((l1, -r * .6, 0), (l1, r * .6, 0), r * .6, "dark", 16)
    u.cyl((r * .4, r * .25, r * .55), (l1 * .7, r * .25, r * .35), r * .12, "chrome", 8).done()
    f = P(f"{prefix}_fore", zh, note, "robot")
    f.cyl((0, 0, 0), (l2 - r * .2, 0, 0), r * .42, "white", 12, True, r * .3)
    f.cyl((l2, -r * .4, 0), (l2, r * .4, 0), r * .42, "dark", 14)
    f.cyl((l2 * .3, r * .3, 0), (l2 * .8, r * .3, 0), r * .06, "copper", 6, False).done()
    w = P(f"{prefix}_wrist", zh, note, "robot")
    w.cyl((0, 0, 0), (0, 0, -r * .9), r * .32, "dark", 12)
    w.bx(-r * .9, r * .9, -r * .35, r * .35, -r * 1.1, -r * .9, "steel", True)
    for s in (-1, 1):
        w.bx(s * r * .85 - r * .1, s * r * .85 + r * .1, -r * .3, r * .3, -r * 1.8, -r * 1.1, "orange", True)
    w.cyl((r * .3, 0, -r * .8), (r * .3, 0, -r * 1.35), r * .08, "chrome", 6).done(r * .03)


def bots():
    def base(p, l, w, h, mat, r=.09):
        p.bx(-l / 2, l / 2, -w / 2, w / 2, .1, .1 + h, mat, True)
        for sx in (-1, 1):
            for sy in (-1, 1):
                p.wheel((sx * l * .34, sy * (w / 2 + .03), r), r, .07)
        p.bx(l / 2 - .02, l / 2 + .005, -.08, .08, .1 + h * .6, .1 + h * .8, "dark")
        return p

    p = base(P("bot_layout", "放樣機器人", "把 BIM 線位以 2 毫米精度列印在樓板上，全站儀即時校正。", "robot"), .6, .45, .22, "robot")
    p.cyl((0, 0, .32), (0, 0, .9), .02, "steel", 6).cyl((0, 0, .9), (0, 0, 1.0), .08, "dark", 12).done(.01)
    p = base(P("bot_tie", "鋼筋綁紮機器人", "沿鋼筋跨行走，以視覺辨識交點，自動綁紮，取代長時間彎腰作業。", "robot"), 1.1, .9, .25, "orange")
    p.cyl((.3, 0, .35), (.3, 0, .1), .03, "steel", 6).bx(-.2, .2, -.3, .3, .35, .65, "dark", True).done(.015)
    p = base(P("bot_trowel", "樓板整平機器人", "雷射控制標高，自動鏝平新澆混凝土，夜間也能連續作業。", "robot"), .9, .9, .3, "yellow")
    p.cyl((0, 0, .1), (0, 0, .02), .62, "steel", 16).done(.015)
    p = base(P("bot_drill", "天花鑽孔機器人", "升降平台把鑽機送到天花板，自動換鑽頭與集塵。", "robot"), 1.0, .7, .3, "robot")
    p.cyl((0, 0, .4), (0, 0, 2.2), .05, "chrome", 8).bx(-.15, .15, -.15, .15, 2.2, 2.5, "orange", True).done(.015)
    p = base(P("bot_board", "板材安裝機器人", "吸盤舉升石膏板，定位後自動鎖固，單板 40 公斤也不傷人。", "robot"), 1.3, .8, .35, "robot")
    p.bx(-.05, .05, -.6, .6, .5, 2.4, "drywall").cyl((-.2, 0, .45), (-.1, 0, 1.6), .04, "chrome", 8).done(.015)
    p = base(P("bot_paint", "噴塗機器人", "依牆面掃描規劃路徑，控制膜厚並回收飛沫。", "robot"), .8, .6, .3, "pipe_blue")
    p.cyl((0, 0, .4), (0, 0, 2.3), .03, "chrome", 8).bx(.05, .3, -.1, .1, 1.4, 1.6, "white", True).done(.015)
    p = base(P("bot_tile", "鋪磚機器人", "自動抹漿、吸取、壓實並量測高低差。", "robot"), 1.2, .9, .3, "orange")
    p.bx(.1, .8, -.35, .35, .1, .14, "tile").cyl((-.2, 0, .4), (.45, 0, .5), .04, "steel", 8).done(.015)
    p = base(P("bot_agv", "物料 AGV", "依 BIM 動線把貨盤送到安裝點，電梯、升降機都能自動呼叫。", "robot"), 1.6, 1.1, .22, "yellow", .08)
    p.bx(-.7, .7, -.45, .45, .36, .9, "form").done(.015)
    h = P("bot_humanoid", "人形內裝機器人", "在住宅尺度的空間裡工作，負責收邊、五金、櫥櫃與設備安裝這類需要雙手的細部工項。", "robot")

    def mid(a2, b2, k):
        return tuple(a2[i] + (b2[i] - a2[i]) * k for i in range(3))

    def seam(a2, b2, k, r0, r1):
        h.loft([(mid(a2, b2, k - .012), r0, r1), (mid(a2, b2, k + .012), r0, r1)], "joint", 18)

    def leg(sy, kx):
        hip, knee, ankle = (0, sy, .9), (kx, sy, .49), (0, sy, .1)
        h.ball(hip, .074, "joint", 3)
        h.loft([(mid(hip, knee, .08), .064, .08), (mid(hip, knee, .3), .078, .096), (mid(hip, knee, .62), .068, .084),
                (mid(hip, knee, .88), .053, .062)], "shell", 20)
        seam(hip, knee, .46, .0755, .093)
        h.ball(knee, .05, "joint", 3)
        h.loft([((knee[0] + .036, sy, knee[2] + .05), .03, .012), ((knee[0] + .052, sy, knee[2]), .044, .02),
                ((knee[0] + .038, sy, knee[2] - .055), .03, .012)], "shell", 14)
        h.loft([(mid(knee, ankle, .08), .049, .054), (mid(knee, ankle, .28), .056, .07), (mid(knee, ankle, .62), .046, .053),
                (mid(knee, ankle, .9), .037, .04)], "shell", 20)
        seam(knee, ankle, .5, .0525, .0635)
        h.ball(ankle, .036, "joint", 3)
        h.loft([((-.085, sy, .052), .04, .036), ((-.04, sy, .078), .054, .058), ((.05, sy, .068), .058, .05),
                ((.125, sy, .05), .056, .036), ((.158, sy, .036), .046, .022)], "joint", 20, 2.8)
        h.loft([((-.09, sy, .012), .046, .014), ((.05, sy, .012), .06, .014), ((.16, sy, .012), .05, .014)], "rubber", 16, 3)

    leg(-.1, .022)
    leg(.1, .036)
    h.loft([((0, 0, .835), .05, .05), ((.002, 0, .875), .118, .082), ((.004, 0, .93), .128, .092), ((.002, 0, .985), .112, .082)], "shell", 24, 2.5)
    h.loft([((0, 0, .975), .09, .068), ((0, 0, 1.05), .082, .062), ((0, 0, 1.115), .1, .074)], "joint", 22)
    for z in (1.0, 1.035, 1.07):
        h.loft([((0, 0, z - .006), .094, .073), ((0, 0, z + .006), .094, .073)], "joint", 22)
    h.loft([((.004, 0, 1.095), .104, .078), ((.012, 0, 1.16), .126, .092), ((.02, 0, 1.25), .17, .112), ((.018, 0, 1.33), .196, .116),
            ((.006, 0, 1.4), .178, .098), ((0, 0, 1.45), .1, .068), ((0, 0, 1.47), .06, .05)], "shell", 28, 2.4)
    h.loft([((.122, 0, 1.2), .05, .006), ((.14, 0, 1.28), .088, .016), ((.126, 0, 1.36), .07, .008)], "visor", 16, 3)
    h.bx(.15, .159, -.055, .055, 1.302, 1.309, "amber")
    h.loft([((-.098, 0, 1.15), .1, .02), ((-.13, 0, 1.2), .118, .04), ((-.135, 0, 1.36), .13, .045), ((-.1, 0, 1.42), .105, .018)], "joint", 22, 3)
    h.bx(-.18, -.174, -.055, .055, 1.25, 1.33, "amber")
    h.cyl((0, 0, 1.46), (.004, 0, 1.54), .046, "joint", 16, True, .04)
    h.loft([((.006, 0, 1.53), .03, .03), ((.008, 0, 1.55), .07, .08), ((.012, 0, 1.59), .085, .098), ((.014, 0, 1.64), .088, .102),
            ((.012, 0, 1.685), .08, .094), ((.006, 0, 1.715), .056, .066), ((.002, 0, 1.73), .02, .024)], "shell", 28, 2.5)
    h.loft([((.016, 0, 1.6), .0895, .1035), ((.018, 0, 1.63), .092, .107), ((.018, 0, 1.665), .0895, .1035)], "visor", 30, 2.5)
    h.bx(.118, .127, -.062, .062, 1.628, 1.634, "amber")
    h.loft([((.03, 0, 1.726), .012, .03), ((-.05, 0, 1.722), .012, .04)], "orange", 10, 3)

    def arm(sy, elbow, wrist, grip):
        sh = (0, sy, 1.375)
        h.ball(sh, .062, "joint", 3)
        h.loft([((0, sy * .98, 1.44), .045, .06), ((0, sy * 1.07, 1.415), .062, .078), ((0, sy * 1.1, 1.36), .05, .066)], "shell", 18, 2.5)
        h.loft([(mid(sh, elbow, .16), .046, .05), (mid(sh, elbow, .4), .052, .056), (mid(sh, elbow, .84), .036, .04)], "shell", 18)
        seam(sh, elbow, .55, .0485, .0535)
        h.ball(elbow, .038, "joint", 3)
        h.loft([(mid(elbow, wrist, .1), .035, .037), (mid(elbow, wrist, .36), .047, .048), (mid(elbow, wrist, .84), .03, .032)], "shell", 18)
        h.ball(wrist, .026, "joint", 3)
        d = (wrist[0] - elbow[0], wrist[1] - elbow[1], wrist[2] - elbow[2])
        n = sum(v * v for v in d) ** .5
        d = tuple(v / n for v in d)
        pt = lambda k, off=0.0, up=0.0: (wrist[0] + d[0] * k, wrist[1] + d[1] * k + off, wrist[2] + d[2] * k + up)
        h.loft([(pt(.018), .03, .02), (pt(.05), .042, .022), (pt(.088), .04, .018)], "joint", 14, 2.6)
        for f, off in enumerate((-.03, -.01, .01, .03)):
            ln = (.055, .065, .062, .05)[f]
            tip = pt(.088 + ln * .55, off, -ln * .35 if grip else -ln * .1)
            end = pt(.088 + ln * .95, off, -ln * .95 if grip else -ln * .3)
            h.cyl(pt(.086, off), tip, .0085, "joint", 8, True, .0075).cyl(tip, end, .0075, "joint", 8, True, .0062)
        side = 1 if sy > 0 else -1
        h.cyl(pt(.04, side * -.04, -.012), pt(.082, side * -.052, -.042), .0095, "joint", 8, True, .0075)

    arm(-.235, (.095, -.3, 1.15), (.32, -.335, 1.21), True)
    arm(.235, (.02, .275, 1.12), (.17, .262, .96), False)
    hx, hy, hz = .425, -.345, 1.185
    h.loft([((hx - .055, hy, hz + .03), .022, .03), ((hx + .06, hy, hz + .03), .024, .032), ((hx + .095, hy, hz + .03), .018, .024)], "orange", 12, 2.6)
    h.cyl((hx - .005, hy, hz + .02), (hx - .03, hy, hz - .1), .017, "joint", 10)
    h.cyl((hx + .095, hy, hz + .03), (hx + .19, hy, hz + .03), .0045, "chrome", 8, True, .002)
    h.done(.004)
    d = P("bot_dog", "四足巡檢機器人", "每天自主巡檢，用光達比對竣工與 BIM 誤差，發現偏差就開單。", "robot")
    d.bx(-.4, .4, -.14, .14, .42, .58, "robot", True).bx(.32, .5, -.1, .1, .5, .62, "dark", True)
    for sx in (-.3, .3):
        for sy in (-.17, .17):
            d.beam((sx, sy, .46), (sx + .08, sy, .24), .05, .05, "dark").beam((sx + .08, sy, .24), (sx, sy, .02), .04, .04, "orange")
    d.cyl((.1, 0, .58), (.1, 0, .7), .05, "dark", 12).done(.01)
    d = P("drone", "測繪無人機", "每天兩次攝影測量，自動更新進度模型與土方量。", "robot")
    d.bx(-.18, .18, -.12, .12, 0, .1, "robot", True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            d.beam((0, 0, .06), (sx * .34, sy * .34, .1), .025, .025, "dark")
            d.cyl((sx * .34, sy * .34, .12), (sx * .34, sy * .34, .13), .17, "dark", 12)
    d.done(.01)

    e = P("excavator", "無人挖土機", "依開挖模型自動作業，靠近連續壁或基樁 50 公分時自動減速。", "robot")
    for sy in (-1, 1):
        e.bx(-2.1, 2.1, sy * 1.25 - .32, sy * 1.25 + .32, 0, .8, "rubber", True)
    e.bx(-1.3, 1.3, -1.2, 1.2, .8, 1.0, "dark").bx(-1.6, 1.1, -1.25, 1.25, 1.0, 2.0, "yellow", True)
    e.bx(.1, 1.1, -1.2, -.3, 2.0, 2.7, "glass").bx(-1.6, -.3, -1.2, 1.2, 2.0, 2.3, "yellow", True)
    e.beam((.9, .5, 1.8), (3.6, .5, 3.6), .4, .5, "yellow").beam((3.6, .5, 3.6), (5.3, .5, 1.0), .28, .4, "yellow")
    e.cyl((1.4, .25, 2.0), (3.0, .25, 3.2), .06, "chrome", 8)
    e.bx(4.9, 5.7, .05, .95, .3, 1.0, "dark", True).done(.03)
    c = P("trench_cutter", "液壓抓斗機", "連續壁專用，抓斗內建傾斜儀，即時修正溝槽垂直度。", "robot")
    for sy in (-1, 1):
        c.bx(-2.5, 2.5, sy * 1.5 - .4, sy * 1.5 + .4, 0, .9, "rubber", True)
    c.bx(-2, 1.4, -1.4, 1.4, .9, 2.5, "orange", True)
    c.beam((1.0, 0, 2.0), (4.4, 0, 14), .35, .35, "orange").beam((4.4, 0, 14), (4.4, 0, 3), .06, .06, "steel")
    c.bx(3.1, 5.7, -.4, .4, 1.0, 3.0, "dark", True).done(.03)
    c = P("pile_rig", "全套管鑽機", "依地質模型自動調整轉速與下壓力。", "robot")
    for sy in (-1, 1):
        c.bx(-2.2, 2.2, sy * 1.3 - .35, sy * 1.3 + .35, 0, .8, "rubber", True)
    c.bx(-2, 1, -1.2, 1.2, .8, 2.3, "pipe_blue", True).bx(1.1, 1.6, -.3, .3, 0, 15, "dark")
    c.cyl((2.0, 0, 0), (2.0, 0, 9), .4, "steel", 12).cyl((2.0, 0, 9), (2.0, 0, 10), .55, "orange", 12).done(.03)
    t = P("dump_truck", "電動土方車", "自動進出場並過秤，輪胎洗淨才上路。", "robot")
    t.bx(-3.6, 3.6, -1.15, 1.15, .7, 1.0, "dark").bx(1.8, 3.6, -1.15, 1.15, 1.0, 2.9, "white", True).bx(2.9, 3.62, -1, 1, 1.9, 2.6, "glass")
    t.bx(-3.6, 1.6, -1.2, 1.2, 1.0, 2.5, "yellow", True)
    for x in (-2.6, -1.1, 2.6):
        t.wheel((x, -1.15, .5), .5, .3).wheel((x, 1.15, .5), .5, .3)
    t.done(.03)
    t = P("mixer", "預拌混凝土車", "送貨單與配比自動核對，進場坍度由感測器檢測。", "robot")
    t.bx(-3.6, 3.6, -1.15, 1.15, .7, 1.0, "dark").bx(1.8, 3.6, -1.15, 1.15, 1.0, 2.9, "robot", True).bx(2.9, 3.62, -1, 1, 1.9, 2.6, "glass")
    t.cyl((-3.2, 0, 2.2), (-1.0, 0, 2.3), .7, "orange", 16, True, 1.2).cyl((-1.0, 0, 2.3), (1.4, 0, 2.2), 1.2, "orange", 16, True, .6)
    for x in (-2.6, -1.1, 2.6):
        t.wheel((x, -1.15, .5), .5, .3).wheel((x, 1.15, .5), .5, .3)
    t.done(.03)
    r = P("precast_yard", "現場暫置區", "預鑄構件依吊裝順序暫放，車到就吊，現場不囤料。", "site")
    r.bx(-7, 7, -3, 3, 0, .12, "concrete_sm")
    for k in range(3):
        r.bx(-6.4, -2.2, -2.4 + k * 1.6, -1.6 + k * 1.6, .12, .9, "concrete_sm", True).bx(-6.4, -2.2, -2.4 + k * 1.6, -1.6 + k * 1.6, .95, 1.73, "concrete_sm", True)
    for k in range(4):
        r.bx(-1.2, 6.4, -2.6, 2.6, .14 + k * .2, .31 + k * .2, "concrete", True)
    r.done(.02)
    t = P("precast_truck", "預鑄構件運輸車", "依吊裝順序準時到場，構件掃碼後直接上吊，不佔用街道等候。", "robot")
    t.bx(-7, 6.2, -1.2, 1.2, .9, 1.15, "dark").bx(3.9, 6.2, -1.2, 1.2, 1.15, 3.1, "white", True).bx(5.3, 6.22, -1, 1, 2.1, 2.8, "glass")
    t.bx(-6.8, 3.6, -1.2, 1.2, 1.15, 1.26, "steel")
    for k in range(5):
        t.bx(-6.8 + k * 2.6, -6.72 + k * 2.6, -1.2, 1.2, 1.26, 1.7, "yellow")
    for x in (-5.6, -4.3, -3, 4.8):
        t.wheel((x, -1.15, .5), .5, .3).wheel((x, 1.15, .5), .5, .3)
    t.done(.03)
    q = P("precast_load", "預鑄構件", "工廠養護達標才裝車，到場掃碼後直接上吊。", "robot")
    q.bx(-6.6, 3.4, -1.1, 1.1, 1.26, 1.5, "concrete_sm", True).bx(-6.6, 3.4, -1.1, 1.1, 1.52, 1.76, "concrete", True).bx(-6.2, 2.8, -.8, .8, 1.78, 2.4, "concrete_sm", True).done(.03)
    c = P("control_cabin", "現場控制中心", "數位分身控制室，人員在這裡監看整棟樓的機器與品質資料。", "site")
    c.bx(-4, 4, -1.5, 1.5, 0, 3, "white", True).bx(-3.6, 3.6, -1.52, -1.5, 1.0, 2.5, "glass").bx(-4.1, 4.1, -1.7, 1.7, 3, 3.15, "dark").done(.02)


def plant():
    f = P("precast_plant", "預鑄工廠", "柱、梁、樓板與外牆在工廠模組化澆置，養護達標才出廠。現場的濕作業、噪音與車流都跟著減少。", "site")
    f.bx(-62, 68, -40, 47.8, -.12, .03, "pave")
    f.bx(-40, 40, -18, 18, .02, .3, "concrete_sm")
    for i in range(9):
        x = -40 + i * 10
        for y in (-18, 18):
            f.hbeam((x, y, .3), (x, y, 12.5), .5, .4, "steel")
        f.hbeam((x, -18, 12.5), (x, 18, 12.5), .7, .35, "steel")
    for y in (-18, 18):
        f.hbeam((-40, y, 9.6), (40, y, 9.6), .6, .5, "yellow")
    for i in range(8):
        x0 = -40 + i * 10
        f.loft([((x0, -18, 12.6), .02, .02), ((x0, 18, 12.6), .02, .02)], "steel", 4)
        for k in range(3):
            y0 = -18 + k * 12
            f.bx(x0, x0 + 10, y0, y0 + 12, 12.6, 12.75, "alu")
            f.bx(x0, x0 + 10, y0 + 8, y0 + 12, 12.8, 14.6, "etfe")
    f.bx(-40.1, 40.1, -18.1, -17.9, .3, 12.5, "duct")
    f.bx(-40.1, -39.9, -18, 18, .3, 12.5, "duct")
    for sx, ln in ((-29, 5), (-13, 7), (3, 7), (21, 7)):
        f.bx(sx - 6, sx + 6, -14, -6, .3, .75, "form", True)
        f.bx(sx - 6, sx + 6, 4, 13, .3, .75, "form", True)
        f.bx(sx - 5.5, sx + 5.5, -13.5, -6.5, .75, 1.0, "concrete", True)
        for k in range(4):
            f.bx(sx - 5.4 + k * 2.8, sx - 3.6 + k * 2.8, 4.8, 12.2, .75, 1.35, "concrete_sm", True)
    for i, x in enumerate((-44, -44, -51, -51)):
        y = 12 if i % 2 else 26
        f.cyl((x, y, 6), (x, y, 20), 3.2, "white", 18).cyl((x, y, 4.4), (x, y, 6), 3.2, "white", 18, True, 1.0).cyl((x, y, 20), (x, y, 20.6), 3.2, "white", 18, True, 2.4)
        for a0 in (-1, 1):
            for b0 in (-1, 1):
                f.beam((x + a0 * 2, y + b0 * 2, 0), (x + a0 * 2, y + b0 * 2, 6), .25, .25, "steel")
    f.bx(-53, -41, -8, 6, .02, 7, "yellow", True).bx(-52, -42, -7, 5, 7, 11, "white", True)
    f.beam((-44, 8, 22), (-44, 14, 10), .9, .9, "steel")
    for ix in range(4):
        for iy in range(3):
            x, y = 21 + ix * 11, 24 + iy * 6
            for h in range(3):
                f.bx(x - 4.6, x + 4.6, y - 2.2, y + 2.2, .02 + h * .32, .3 + h * .32, "concrete", True)
    for ix in range(4):
        x = -30 + ix * 7
        for y in (24, 31):
            for h in range(4):
                f.bx(x - .4, x + .4 , y - 2.6, y + 2.6, .04 + h * .84, .84 + h * .84, "concrete_sm", True)
    f.done(.03)
    g = P("plant_gantry", "工廠門式起重機", "把脫模後的構件吊到養護區與出貨區，動線依建造腳本排序。", "robot")
    for sx in (-1, 1):
        g.bx(sx * .9 - .3, sx * .9 + .3, -17.5, 17.5, -.5, .1, "orange", True)
    g.bx(-.5, .5, -17, 17, .1, .9, "orange", True).bx(-1, 1, -3, -1, -.6, .1, "dark", True).cyl((0, -2, -.6), (0, -2, -4), .03, "steel", 6, False)
    g.bx(-2.4, 2.4, -3.6, -.4, -4.5, -4, "concrete_sm", True).done(.03)


def site():
    g = P("ground", "街區地面", "基地四周的街區。", "site")
    W, S, N = 110, -62, 70
    for a, b in ((-W, -20.3), (20.3, W)):
        g.bx(a, b, S, -30.2, -.12, 0, "pave").bx(a, b, -15.6, N, -.12, 0, "pave")
    g.bx(W, 460, -15.6, N, -.12, 0, "pave").bx(238, 460, -130, -30.2, -.12, 0, "pave")
    g.bx(-20.3, 20.3, -15.5, -12.8, -.12, 0, "pave").bx(-20.3, 20.3, 12.8, N, -.12, 0, "pave")
    g.bx(-20.3, 20.3, S, -30.2, -.12, 0, "pave")
    g.done()
    r = P("road", "街道", "基地南側的街道，動線與交通維持自動排程。", "site")
    gate = PLANT[0] + 10
    r.bx(-110, 460, -30.2, -18.2, -.12, .02, "asphalt").bx(-110, 460, -18.2, -18, 0, .15, "concrete_sm")
    r.bx(-110, gate - 7, -30.2, -30, .02, .15, "concrete_sm").bx(gate + 7, 460, -30.2, -30, .02, .15, "concrete_sm")
    for k in range(114):
        x = -108 + k * 5
        r.bx(x, x + 2.4, -24.2, -24.05, .02, .04, "white")
    for k in range(9):
        r.bx(-30 + k * .9, -29.5 + k * .9, -29.6, -18.6, .02, .04, "white")
    r.bx(-110, 460, -18, -15.6, -.12, .08, "pave").done()
    h = P("hoard", "工地圍籬", "鋼製圍籬，下方是吸音板，隔離人車與施工區。", "site")
    h.bx(-1.5, 1.5, -.03, .03, 0, 2.4, "pc").bx(-1.5, 1.5, -.05, .05, 0, .12, "yellow").bx(-1.5, 1.5, -.05, .05, 2.28, 2.4, "yellow")
    h.bx(1.42, 1.5, -.1, .1, 0, 2.6, "steel").done()
    h = P("hoard_win", "透明觀景窗圍籬", "在人行道高度開透明窗，小朋友也看得到。這是讓路人參與工程的設計。", "site")
    h.bx(-1.5, 1.5, -.03, .03, 0, .8, "pc").bx(-1.5, 1.5, -.03, .03, 2.1, 2.4, "pc")
    h.bx(-1.5, 1.5, -.05, .05, 2.28, 2.4, "yellow").bx(-1.5, 1.5, -.05, .05, .75, .82, "yellow")
    h.bx(-1.5, -1.4, -.03, .03, .8, 2.1, "pc").bx(1.4, 1.5, -.03, .03, .8, 2.1, "pc")
    h.bx(-.03, .03, -.03, .03, .8, 2.1, "pc").bx(-1.4, 1.4, -.008, .008, .8, 2.1, "glass").done()
    l = P("led_board", "進度看板支架", "面向街道的進度看板，即時顯示樓層、工項與空污噪音數值。", "site")
    l.bx(-5.3, 5.3, -.2, .2, 3, 7, "dark", True).cyl((-3, 0, 0), (-3, 0, 3), .12, "steel", 10).cyl((3, 0, 0), (3, 0, 3), .12, "steel", 10).done(.02)
    P("led_screen", "進度看板", "面向街道的進度看板，即時顯示樓層、工項與空污噪音數值。", "site") \
        .bx(-5.1, 5.1, -.22, -.2, 3.2, 6.8, "led").done()
    p = P("person_a", "路人", "路人從人行道就看得到施工進度。", "site")
    def person(p, cl, cb):
        for s in (-1, 1):
            p.cyl((0, s * .1, 0), (0, s * .1, .86), .08, cb, 7, True, .09)
            p.cyl((0, s * .24, 1.42), (.04, s * .25, .85), .05, cl, 6)
        p.cyl((0, 0, .84), (0, 0, 1.45), .19, cl, 9, True, .22).ball((0, 0, 1.6), .115, "skin", 1)
    person(p, "cloth_b", "cloth_a")
    p.done()
    p = P("person_b", "路人", "路人從人行道就看得到施工進度。", "site")
    person(p, "cloth_c", "cloth_a")
    p.done()
    p = P("person_c", "現場巡檢員", "人員只做巡檢與判斷，不進入吊裝區。", "site")
    person(p, "orange", "cloth_a")
    p.ball((0, 0, 1.66), .125, "yellow", 1).done()
    t = P("tree", "行道樹", "保留既有行道樹，施工前由無人機建檔。", "site")
    random.seed(4)
    t.cyl((0, 0, 0), (0, 0, 2.6), .17, "bark", 8, False, .1)
    for i in range(7):
        q = i * 2.4
        t.ball((math.cos(q) * 1.1, math.sin(q) * 1.1, 3.4 + (i % 3) * .55), 1.25, "leaf", 2, (1, 1, .85))
    t.ball((0, 0, 4.6), 1.3, "leaf", 2).done()
    b = P("block_a", "鄰棟建物", "鄰房貼有傾斜感測器，震動與沉陷超限時自動暫停開挖。", "site")
    b.bx(-9, 9, -7, 7, 0, 22, "block").bx(-3, 3, -2, 2, 22, 24.5, "concrete_sm").bx(-8, -5, -3, 0, 22, 23.2, "duct").done()
    b = P("block_b", "鄰棟建物", "鄰房貼有傾斜感測器，震動與沉陷超限時自動暫停開挖。", "site")
    b.bx(-7, 7, -8, 8, 0, 34, "block").bx(-7.1, 7.1, -8.1, 8.1, 0, 3.6, "alu").bx(-2.5, 2.5, -3, 3, 34, 37, "concrete_sm").done()
    b = P("block_c", "鄰棟建物", "鄰房貼有傾斜感測器，震動與沉陷超限時自動暫停開挖。", "site")
    b.bx(-11, 11, -6, 6, 0, 13, "block").bx(-11.1, 11.1, -6.1, 6.1, 0, 3.4, "wood").done()
    c = P("car", "汽車", "街道上的車流。", "site")
    c.bx(-2.2, 2.2, -.86, .86, .35, .95, "car_a", True).bx(-1.2, 1.1, -.76, .76, .95, 1.42, "glass")
    for x in (-1.4, 1.4):
        c.wheel((x, -.85, .33), .33, .22).wheel((x, .85, .33), .33, .22)
    c.done(.04)
    a = P("land_pave", "景觀鋪面", "鋪面單元。", "landscape")
    a.bx(-3, 3, -1.5, 1.5, 0, .06, "pave").done()
    a = P("land_lawn", "景觀綠地", "雨水花園，兼具滯洪功能。", "landscape")
    a.bx(-3, 3, -1.5, 1.5, 0, .05, "grass").bx(-3.05, 3.05, -1.55, -1.5, 0, .12, "concrete_sm").bx(-3.05, 3.05, 1.5, 1.55, 0, .12, "concrete_sm").done()
    a = P("canopy", "入口雨遮", "鋼構木紋雨遮。", "landscape")
    a.bx(-4.5, 4.5, -2.2, 2.2, 3.2, 3.32, "wood").bx(-4.55, 4.55, -2.25, 2.25, 3.32, 3.38, "alu")
    for x in (-3.8, 3.8):
        a.cyl((x, -1.9, 0), (x, -1.9, 3.2), .06, "alu", 10)
    a.done()
    a = P("guide_wall", "導牆", "連續壁開挖前的 L 型導牆，同時是抓斗機的定位基準。", "site")
    a.bx(-1.5, 1.5, -.75, -.5, -.02, .12, "concrete_sm").bx(-1.5, 1.5, .5, .75, -.02, .12, "concrete_sm").done()
    a = P("pad_plate", "鋪路鋼板", "重機行走區，土壓由感測器監控。", "site")
    a.bx(-3, 3, -1.5, 1.5, 0, .025, "steel").done()


def build_all():
    structure()
    rebar()
    forms()
    damper()
    facade()
    interior()
    rig()
    arm("arm_h", "重型機械臂", "負責柱筋籠、外牆與設備的吊裝，也能換裝布料頭澆置混凝土，末端設有力量回授與防擺控制。", 3.4, 3.2, .36)
    arm("arm_l", "輕型機械臂", "可換工具：點焊、螺栓鎖固、打膠、噴塗、視覺量測。", 1.7, 1.6, .15)
    bots()
    plant()
    site()
