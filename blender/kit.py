import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Vector

PARTS = {}
MATS = {}
TEX_DIR = None


def fft_noise(n, slope, seed):
    rng = np.random.default_rng(seed)
    spec = np.fft.rfft2(rng.normal(size=(n, n)))
    fy = np.fft.fftfreq(n)[:, None]
    fx = np.fft.rfftfreq(n)[None, :]
    f = np.sqrt(fx * fx + fy * fy)
    f[0, 0] = 1
    out = np.fft.irfft2(spec / f ** slope, s=(n, n))
    return (out - out.mean()) / out.std()


def save_image(name, rgb, alpha=None):
    h, w = rgb.shape[:2]
    a = np.ones((h, w)) if alpha is None else alpha
    px = np.dstack([np.clip(rgb, 0, 1), a]).astype(np.float32)
    img = bpy.data.images.new(name, w, h, alpha=alpha is not None)
    img.pixels.foreach_set(px[::-1].ravel())
    ext = "png" if alpha is not None else "jpg"
    img.filepath_raw = os.path.join(TEX_DIR, f"{name}.{ext}")
    img.file_format = "PNG" if alpha is not None else "JPEG"
    img.save()
    img.pack()
    return img


def tint(gray, col):
    return np.dstack([gray * c for c in col])


def make_textures():
    t = {}
    n = 512
    c = 0.62 + 0.035 * fft_noise(n, 1.1, 1) + 0.02 * fft_noise(n, 0.4, 2)
    c[:: n // 2, :] -= 0.14
    c[:, :: n // 2] -= 0.14
    for y in range(n // 4, n, n // 2):
        for x in range(n // 8, n, n // 4):
            yy, xx = np.ogrid[-y:n - y, -x:n - x]
            c[(xx * xx + yy * yy) < 16] -= 0.2
    t["concrete"] = save_image("tx_concrete", tint(c, (1.0, 0.985, 0.95)))
    s = 0.34 + 0.09 * fft_noise(n, 1.3, 3) + 0.05 * fft_noise(n, 0.5, 4)
    t["soil"] = save_image("tx_soil", tint(s, (1.0, 0.72, 0.48)))
    a = 0.17 + 0.03 * fft_noise(n, 0.3, 5) + 0.012 * fft_noise(n, 1.2, 6)
    t["asphalt"] = save_image("tx_asphalt", tint(a, (1, 1, 1.03)))
    p = 0.58 + 0.03 * fft_noise(n, 1.0, 7)
    p[:: n // 4, :] -= 0.2
    for i, y in enumerate(range(0, n, n // 4)):
        off = (i % 2) * n // 8
        p[y:y + n // 4, off:: n // 4] -= 0.2
    t["pave"] = save_image("tx_pave", tint(p, (0.98, 0.93, 0.85)))
    w = np.tile(fft_noise(n, 1.0, 8).mean(axis=0, keepdims=True), (n, 1))
    wood = 0.42 + 0.09 * w + 0.015 * fft_noise(n, 0.6, 9)
    t["wood"] = save_image("tx_wood", tint(wood, (1.0, 0.72, 0.46)))
    pc = 0.86 + 0.012 * fft_noise(n, 0.9, 10)
    t["pc"] = save_image("tx_pc", tint(pc, (1.0, 0.985, 0.955)))
    g = 0.3 + 0.07 * fft_noise(n, 0.9, 11)
    t["grass"] = save_image("tx_grass", tint(g, (0.52, 0.8, 0.34)))

    m = 256
    b = np.full((m, m, 3), 0.64)
    b = b * (1 + 0.03 * fft_noise(m, 1.0, 12))[..., None] * np.array([0.98, 0.93, 0.86])
    for row in range(4):
        for col in range(4):
            y0, x0 = 16 + row * 60, 12 + col * 60
            b[y0:y0 + 38, x0:x0 + 36] = (0.2, 0.26, 0.32)
            b[y0:y0 + 38, x0 + 17:x0 + 19] = (0.5, 0.5, 0.5)
    t["block"] = save_image("tx_block", b)

    q = 128
    net = np.zeros((q, q))
    step = q // 6
    net[:: step, :] = 1
    net[:: step + 0, :] = 1
    net[:, :: step] = 1
    from_edges = np.roll(net, 1, axis=0) + np.roll(net, 1, axis=1)
    alpha = np.clip(net + from_edges, 0, 1) * 0.9 + 0.06
    rgb = np.dstack([np.full((q, q), 0.12), np.full((q, q), 0.42), np.full((q, q), 0.46)])
    t["net"] = save_image("tx_net", rgb, alpha)
    return t


def material(name, col, rough=0.6, metal=0.0, tex=None, uv=1.0, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes["Principled BSDF"]
    n.inputs["Base Color"].default_value = (*col, 1)
    n.inputs["Roughness"].default_value = rough
    n.inputs["Metallic"].default_value = metal
    if tex is not None:
        i = m.node_tree.nodes.new("ShaderNodeTexImage")
        i.image = tex
        m.node_tree.links.new(i.outputs["Color"], n.inputs["Base Color"])
    if emit:
        n.inputs["Emission Color"].default_value = (*emit, 1)
        n.inputs["Emission Strength"].default_value = 1.0
    MATS[name] = (m, uv)
    return m


def make_materials(t):
    material("concrete", (1, 1, 1), 0.82, tex=t["concrete"], uv=2.4)
    material("concrete_sm", (0.66, 0.65, 0.62), 0.78)
    material("rebar", (0.36, 0.2, 0.13), 0.62, 0.55)
    material("form", (0.76, 0.78, 0.8), 0.38, 0.75)
    material("yellow", (0.93, 0.6, 0.04), 0.46, 0.15)
    material("orange", (0.9, 0.3, 0.06), 0.4, 0.1)
    material("robot", (0.88, 0.89, 0.87), 0.34)
    material("dark", (0.07, 0.08, 0.09), 0.5, 0.2)
    material("steel", (0.5, 0.53, 0.56), 0.36, 0.9)
    material("steel_red", (0.58, 0.09, 0.07), 0.42, 0.25)
    material("chrome", (0.86, 0.87, 0.88), 0.14, 1)
    material("rubber", (0.03, 0.03, 0.035), 0.88)
    material("glass", (0.32, 0.5, 0.58), 0.06, 0.4)
    material("pc", (1, 1, 1), 0.62, tex=t["pc"], uv=2.0)
    material("alu", (0.13, 0.14, 0.15), 0.38, 0.8)
    material("wood", (1, 1, 1), 0.56, tex=t["wood"], uv=1.2)
    material("drywall", (0.91, 0.9, 0.87), 0.8)
    material("tile", (0.74, 0.7, 0.64), 0.32)
    material("duct", (0.68, 0.71, 0.74), 0.42, 0.85)
    material("pipe_red", (0.72, 0.08, 0.05), 0.42)
    material("pipe_blue", (0.08, 0.3, 0.62), 0.42)
    material("pipe_green", (0.12, 0.45, 0.28), 0.42)
    material("copper", (0.78, 0.42, 0.22), 0.34, 1)
    material("soil", (1, 1, 1), 0.95, tex=t["soil"], uv=4.0)
    material("asphalt", (1, 1, 1), 0.92, tex=t["asphalt"], uv=5.0)
    material("pave", (1, 1, 1), 0.74, tex=t["pave"], uv=2.4)
    material("grass", (1, 1, 1), 0.95, tex=t["grass"], uv=4.0)
    material("leaf", (0.13, 0.32, 0.12), 0.8)
    material("bark", (0.2, 0.13, 0.09), 0.9)
    material("block", (1, 1, 1), 0.7, tex=t["block"], uv=12.0)
    material("net", (1, 1, 1), 0.9, tex=t["net"], uv=0.6)
    material("etfe", (0.82, 0.9, 0.94), 0.25)
    material("skin", (0.72, 0.52, 0.4), 0.6)
    material("cloth_a", (0.14, 0.2, 0.32), 0.8)
    material("cloth_b", (0.75, 0.32, 0.18), 0.8)
    material("cloth_c", (0.82, 0.8, 0.74), 0.8)
    material("led", (0.02, 0.02, 0.02), 0.4)
    material("pv", (0.03, 0.06, 0.16), 0.18, 0.6)
    material("white", (0.93, 0.93, 0.9), 0.3)
    material("car_a", (0.55, 0.06, 0.05), 0.26, 0.5)
    material("car_b", (0.15, 0.2, 0.28), 0.26, 0.5)
    material("lamp", (1, 0.9, 0.7), 0.4, emit=(1.0, 0.85, 0.6))
    material("shell", (0.86, 0.85, 0.81), 0.27, 0.05)
    material("joint", (0.05, 0.055, 0.062), 0.4, 0.55)
    material("visor", (0.008, 0.01, 0.014), 0.07, 0.7)
    material("amber", (1, 0.55, 0.12), 0.3, emit=(1.0, 0.5, 0.08))


class P:
    def __init__(self, name, zh, note, layer):
        self.name = name
        self.bm = bmesh.new()
        self.slots = []
        self.bev_edges = []
        PARTS[name] = {"zh": zh, "note": note, "layer": layer}

    def _slot(self, mat):
        if mat not in self.slots:
            self.slots.append(mat)
        return self.slots.index(mat)

    def _face(self, vs, slot, smooth=False):
        f = self.bm.faces.new(vs)
        f.material_index = slot
        f.smooth = smooth
        return f

    def bx(self, x0, x1, y0, y1, z0, z1, mat, bev=False):
        s = self._slot(mat)
        pts = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
               (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        v = [self.bm.verts.new(p) for p in pts]
        fs = [self._face(q, s) for q in (
            (v[3], v[2], v[1], v[0]), (v[4], v[5], v[6], v[7]),
            (v[0], v[1], v[5], v[4]), (v[1], v[2], v[6], v[5]),
            (v[2], v[3], v[7], v[6]), (v[3], v[0], v[4], v[7]))]
        if bev:
            self.bev_edges += list({e for f in fs for e in f.edges})
        return self

    def box(self, c, d, mat, bev=False):
        return self.bx(c[0] - d[0] / 2, c[0] + d[0] / 2, c[1] - d[1] / 2, c[1] + d[1] / 2,
                       c[2] - d[2] / 2, c[2] + d[2] / 2, mat, bev)

    def _frame(self, a, b):
        a, b = Vector(a), Vector(b)
        w = (b - a).normalized()
        u = w.cross(Vector((0, 0, 1)))
        if u.length < 1e-4:
            u = w.cross(Vector((1, 0, 0)))
        u.normalize()
        return a, b, u, w.cross(u).normalized()

    def cyl(self, a, b, r, mat, seg=10, caps=True, r2=None):
        a, b, u, v = self._frame(a, b)
        r2 = r if r2 is None else r2
        s = self._slot(mat)
        ring0, ring1 = [], []
        for i in range(seg):
            q = 2 * math.pi * i / seg
            d = u * math.cos(q) + v * math.sin(q)
            ring0.append(self.bm.verts.new(a + d * r))
            ring1.append(self.bm.verts.new(b + d * r2))
        for i in range(seg):
            j = (i + 1) % seg
            self._face((ring0[i], ring0[j], ring1[j], ring1[i]), s, True)
        if caps:
            self._face(ring1, s)
            self._face(ring0[::-1], s)
        return self

    def beam(self, a, b, w, h, mat):
        a, b, u, v = self._frame(a, b)
        u, v = u * (w / 2), v * (h / 2)
        s = self._slot(mat)
        c = [u + v, -u + v, -u - v, u - v]
        r0 = [self.bm.verts.new(a + d) for d in c]
        r1 = [self.bm.verts.new(b + d) for d in c]
        for i in range(4):
            j = (i + 1) % 4
            self._face((r0[i], r0[j], r1[j], r1[i]), s)
        self._face(r1, s)
        self._face(r0[::-1], s)
        return self

    def hbeam(self, a, b, h, w, mat):
        a2, b2, u, v = self._frame(a, b)
        t = max(h, w) * 0.09
        for sgn in (-1, 1):
            off = v * (sgn * (h - t) / 2)
            self.beam(a2 + off, b2 + off, w, t, mat)
        self.beam(a2, b2, t * 0.7, h - t, mat)
        return self

    def ball(self, c, r, mat, sub=2, sz=(1, 1, 1)):
        from mathutils import Matrix
        m = Matrix.Translation(c) @ Matrix.Diagonal((sz[0], sz[1], sz[2], 1))
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=r, matrix=m)
        s = self._slot(mat)
        faces = {f for v in res["verts"] for f in v.link_faces}
        for f in faces:
            f.material_index = s
            f.smooth = True
        return self

    def loft(self, secs, mat, seg=20, sq=2.0):
        """沿路徑放樣平滑外殼。secs 為 (中心, 側向半寬, 前後半寬)，sq 大於 2 時截面偏方。"""
        s = self._slot(mat)
        pts = [Vector(c[0]) for c in secs]
        rings = []
        for i, (c, a, b) in enumerate(secs):
            t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            side = Vector((0, 1, 0))
            side = (side - t * side.dot(t)).normalized()
            front = side.cross(t).normalized()
            ring = []
            for k in range(seg):
                q = 2 * math.pi * k / seg
                cq, sq_ = math.cos(q), math.sin(q)
                e = 2 / sq
                d = side * (a * math.copysign(abs(cq) ** e, cq)) + front * (b * math.copysign(abs(sq_) ** e, sq_))
                ring.append(self.bm.verts.new(pts[i] + d))
            rings.append(ring)
        for r0, r1 in zip(rings, rings[1:]):
            for k in range(seg):
                n = (k + 1) % seg
                self._face((r0[k], r0[n], r1[n], r1[k]), s, True)
        self._face(rings[0][::-1], s, True)
        self._face(rings[-1], s, True)
        return self

    def wheel(self, c, r, w, axis="y"):
        d = {"x": (w / 2, 0, 0), "y": (0, w / 2, 0)}[axis]
        a = (c[0] - d[0], c[1] - d[1], c[2])
        b = (c[0] + d[0], c[1] + d[1], c[2])
        self.cyl(a, b, r, "rubber", 14)
        d2 = {"x": (w / 2 + 0.005, 0, 0), "y": (0, w / 2 + 0.005, 0)}[axis]
        self.cyl((c[0] - d2[0], c[1] - d2[1], c[2]), (c[0] + d2[0], c[1] + d2[1], c[2]), r * 0.55, "steel", 10)
        return self

    def done(self, bevel=0.0):
        bm = self.bm
        if bevel and self.bev_edges:
            bm.edges.ensure_lookup_table()
            bmesh.ops.bevel(bm, geom=[e for e in self.bev_edges if e.is_valid], offset=bevel, segments=1,
                            profile=0.5, affect="EDGES", clamp_overlap=True)
        uv = bm.loops.layers.uv.new()
        for f in bm.faces:
            scale = MATS[self.slots[f.material_index]][1]
            n = f.normal
            ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
            for l in f.loops:
                p = l.vert.co
                if az >= ax and az >= ay:
                    l[uv].uv = (p.x / scale, p.y / scale)
                elif ax >= ay:
                    l[uv].uv = (p.y / scale, p.z / scale)
                else:
                    l[uv].uv = (p.x / scale, p.z / scale)
        me = bpy.data.meshes.new(self.name)
        bm.to_mesh(me)
        bm.free()
        for s in self.slots:
            me.materials.append(MATS[s][0])
        ob = bpy.data.objects.new(self.name, me)
        bpy.data.collections["PARTS"].objects.link(ob)
        PARTS[self.name]["tris"] = sum(len(p.vertices) - 2 for p in me.polygons)
        return ob
