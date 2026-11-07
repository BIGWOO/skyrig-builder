import math

XS = [-17.5, -10.5, -3.5, 3.5, 10.5, 17.5]
YS = [-9.75, -3.25, 3.25, 9.75]
BX, BY = 7.0, 6.5
H_TYP = 3.3
WALL_X, WALL_Y = 19.5, 12.0
RING_X, RING_Y = 21.0, 13.5

STOREYS = [("B2", -7.0, -3.5), ("B1", -3.5, 0.0), ("1F", 0.0, 4.5)]
for n in range(2, 13):
    z = 4.5 + H_TYP * (n - 2)
    STOREYS.append((f"{n}F", z, z + H_TYP))
STOREYS.append(("屋突", 40.8, 44.0))

PHASES = [
    ("survey", "基地整備與數位放樣", 0, 15),
    ("dwall", "連續壁", 15, 55),
    ("piles", "基樁", 55, 70),
    ("excavate", "自動開挖與支撐", 70, 105),
    ("rig", "天架組立", 105, 120),
    ("raft", "筏式基礎", 120, 136),
    ("basement", "地下室結構", 136, 152),
    ("tower", "主體結構與制震", 152, 256),
    ("envelope", "外牆與機電收尾", 256, 276),
    ("descend", "天架下降與拆除", 276, 312),
    ("interior", "內裝與系統測試", 312, 335),
    ("landscape", "景觀與交屋", 335, 360),
]
T_END = 360.0
T_STRUCT = 136.0
CYCLE = 8.0
T_RIG_ON = 106.0
T_RIG_OFF = 312.0


# 施工邏輯日 → 實際工期日。主體 2 天一層，全案 90 天。
REMAP = [(0, 0), (15, 3), (55, 13), (70, 18), (105, 27), (120, 30), (136, 33), (152, 36), (256, 62), (276, 70), (312, 78), (335, 85), (360, 90)]
PHASES_OUT = [
    ("prefab", "工廠預鑄", 0, 2), ("survey", "基地整備與數位放樣", 2, 3), ("dwall", "連續壁", 3, 13), ("piles", "基樁", 13, 18),
    ("excavate", "自動開挖與支撐", 18, 27), ("rig", "天架組立", 27, 30), ("raft", "筏式基礎", 30, 33), ("basement", "地下室預鑄吊裝", 33, 36),
    ("tower", "主體預鑄吊裝與制震", 36, 62), ("envelope", "外牆收尾與頂棚拆除", 62, 70), ("descend", "天架下降與拆除", 70, 78),
    ("interior", "內裝與系統測試", 78, 85), ("landscape", "景觀與交屋", 85, 90),
]


def remap(t):
    if t < 0 or t >= 9000:
        return t
    for (a0, b0), (a1, b1) in zip(REMAP, REMAP[1:]):
        if t <= a1:
            return b0 + (b1 - b0) * (t - a0) / (a1 - a0)
    return REMAP[-1][1]


def cycle_start(i):
    return T_STRUCT + CYCLE * i


def rig_keys():
    keys = [(T_RIG_ON, 2.0), (118.0, 12.0)]
    z = 12.0
    for i, (_, _, z1) in enumerate(STOREYS):
        target = max(12.0, z1 + 9.0)
        t = cycle_start(i)
        if target > z:
            keys.append((t + 7.4, z))
            keys.append((t + 8.0, target))
            z = target
    keys.append((276.0, z))
    keys.append((304.0, 6.0))
    keys.append((T_RIG_OFF, 6.0))
    return keys


def rig_z(t, keys=None):
    keys = keys or rig_keys()
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, z0), (t1, z1) in zip(keys, keys[1:]):
        if t <= t1:
            return z0 + (z1 - z0) * (t - t0) / max(t1 - t0, 1e-6)
    return keys[-1][1]


def rig_b(z):
    return max(z - 15.5, 1.5)


def mast_section_times(z, keys):
    margin = 3.0
    first, last = None, None
    t = T_RIG_ON
    while t <= T_RIG_OFF:
        if rig_z(t, keys) + margin >= z:
            if first is None:
                first = t
            last = t
        t += 0.25
    return first, last


def chunks(seq, n):
    n = max(1, n)
    k = math.ceil(len(seq) / n)
    return [seq[i:i + k] for i in range(0, len(seq), k)]
