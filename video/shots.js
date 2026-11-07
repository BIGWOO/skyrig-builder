// 分鏡：座標沿用 three.js（y 向上，大樓中心在原點，街道在 +z）。
(() => {
  const DUR = {"idle": 12.4, "heroB": 3.633, "hook": 4.667, "aiplan": 6.8, "twin": 8.367, "factory": 6.933, "site": 4.967, "site2": 2.667, "rig": 4.633, "scale": 7.4, "deck": 4.933, "night": 5.8, "climb": 5.2, "lowarm": 5.2, "street": 4.833, "storm": 4.767, "descend": 7.4, "fitout": 5.967, "finale": 9.833, "neighbor": 6.267, "end": 11.4}, SW = 0; // AUTO
  const s = window.__sim, A = s.A, V = s.camera.position.constructor;
  const lerp = (a, b, k) => a + (b - a) * k;
  const sm = (k) => k * k * (3 - 2 * k);
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  // 關鍵幀 [u, ...values]，段內平滑
  const K = (u, keys) => {
    if (u <= keys[0][0]) return keys[0].slice(1);
    for (let i = 1; i < keys.length; i++) if (u <= keys[i][0]) {
      const a = keys[i - 1], b = keys[i], k = sm((u - a[0]) / (b[0] - a[0]));
      return a.slice(1).map((v, j) => lerp(v, b[j + 1], k));
    }
    return keys[keys.length - 1].slice(1);
  };
  const orbit = (deg, r, y) => [Math.cos(deg * Math.PI / 180) * r, y, Math.sin(deg * Math.PI / 180) * r];
  const tip = (a) => [a.p.x, a.p.y, a.p.z];
  const rigY = () => A.rig.position.y;
  const add = (a, b) => a.map((v, i) => v + b[i]);

  const IDLE = { id: "idle", name: "", T: 51.7, fx: "night", park: true, cam: "overview", steps: [] };
  const NIGHT_WORK = { id: "nightwork", name: "", T: 41, fx: "night", park: true, cam: "overview", steps: [] };
  const DAY_END = { id: "dayend", name: "", T: 90, fx: "day", cam: "overview", steps: [] };
  const NIGHT_END = { id: "end", name: "", T: 90, fx: "night", cam: "overview", steps: [] };
  const STORM = { id: "storm", name: "", T: 65, fx: "storm", park: true, netRoll: true, roof: 1, cam: "overview", steps: [] };
  const QUAKE = { id: "quake", name: "", T: 360, fx: "quake", cam: "overview", steps: [], actions: [["", "with"]] };

  // 3 天/秒 → 9 天/秒，0.4 秒內轉速
  const ramp = (t0, r0, sw, r1, w = .4) => (x) => {
    if (x <= sw) return t0 + r0 * x;
    const q = Math.min(x - sw, w), d = r0 * q + (r1 - r0) * q * q / (2 * w);
    return t0 + r0 * sw + d + Math.max(x - sw - w, 0) * r1;
  };
  const wp = (o) => { const v = new V(); o.getWorldPosition(v); return [v.x, v.y, v.z]; };
  const mix = (a, b, k) => a.map((v, i) => lerp(v, b[i], k));
  const exposure = (v) => { s.renderer.toneMappingExposure = v; };

  window.__SHOTS = [
    {
      id: "idle", T0: 51.7, rate: 0, scenario: IDLE,
      cam(u) {
        const [deg, r, y, ty] = K(u, [[0, 88, 100, 10, 18], [1, 96, 84, 8, 20]]);
        return { p: orbit(deg, r, y), t: [0, ty, 0], fov: 42 };
      },
    },
    {
      id: "heroB", T0: 30, rate: 1,
      cam(u) {
        const h = A.heavy[1], e = wp(h.arm.el);
        const [x, y, z, fov] = K(u, [[0, -1.2, 2.3, 2.6, 50], [1, .5, 2, 1, 44]]);
        const q = add(mix(e, tip(h), .3), [0, 1, 0]);
        return { p: [x, y, z], t: [q[0], Math.max(q[1], 7.5), q[2]], fov: fov + 6, track: 1.3 };
      },
    },
    {
      id: "hook", T0: 53.5, rate: 1,
      cam(u) {
        const y = rigY();
        const [x, py, z, ty, fov] = K(u, [[0, 15, y + 7, 21, y - 7, 46], [.5, 28, y + 18, 50, y - 8, 43], [1, 40, 76, 102, 24, 40]]);
        return { p: [x, py, z], t: [0, ty, 0], fov, track: 2 };
      },
    },
    {
      id: "twin", T0: 0, rate: 10.5, twin: true,
      cam(u) {
        const [deg, r, y, ty] = K(u, [[0, 40, 112, 70, 20], [1, 115, 112, 62, 22]]);
        return { p: orbit(deg, r, y), t: [0, ty, 0], fov: 40 };
      },
    },
    {
      id: "fitout", T0: 78.1, rate: 1,
      post() { exposure(1.15); },
      cam(u) {
        const [x, z, tx, tz] = K(u, [[0, -16.9, 4.1, -11.5, 6.2], [1, -15.8, 4.6, -11.5, 6.1]]);
        return { p: [x, 19.2, z], t: [tx, 18.75, tz], fov: 54 };
      },
    },
    {
      id: "site", T0: 0, rate: 3,
      cam(u) {
        const [deg, r, y, ty, fov] = K(u, [[0, 70, 112, 88, 0, 40], [1, 100, 84, 54, -2, 40]]);
        return { p: orbit(deg, r, y), t: [0, ty, 0], fov };
      },
    },
    {
      id: "site2", T0: 18, rate: 3,
      cam(u) {
        const [deg, r, y] = K(u, [[0, 105, 62, 40], [1, 116, 50, 32]]);
        return { p: orbit(deg, r, y), t: [0, -7, 0], fov: 42 };
      },
    },
    {
      id: "rig", T0: 27, rate: 1,
      cam(u) {
        const [x, y, z, ty, fov] = K(u, [[0, 20, 5.5, 33, 7, 50], [1, 9, 4, 26, 13, 58]]);
        return { p: [x, y, z], t: [3, ty, 0], fov };
      },
    },
    {
      id: "deck", T0: 36, rate: 1,
      cam(u) {
        const z = rigY() - 9, a = tip(A.heavy[0]);
        const [x, up, zz, fov] = K(u, [[0, 16, 8, 10.5, 60], [1, 11, 6.4, 11, 56]]);
        return { p: [x, z + up, zz], t: mix([0, z + 1, 0], a, .45), fov, track: 1.2 };
      },
    },
    {
      id: "night", T0: 41, rate: 1, scenario: NIGHT_WORK,
      pre() { A.nightLights.forEach((l) => (l.intensity = 620)); },
      cam(u) {
        const y = rigY();
        const [deg, r, up, fov] = K(u, [[0, 62, 66, 16, 44], [1, 86, 62, 10, 44]]);
        return { p: orbit(deg, r, y + up), t: [0, y - 14, 0], fov, track: 1.2 };
      },
    },
    {
      id: "climb", T0: 44.7, rate: 1,
      cam(u) {
        const y = rigY();
        const [x, dy, z, fov] = K(u, [[0, 48, 3, 38, 40], [1, 42, 6, 34, 42]]);
        return { p: [x, y + dy, z], t: [2, y - 13, 0], fov, track: 2 };
      },
    },
    {
      id: "lowarm", T0: 48.5, rate: 1,
      cam(u) {
        const a = A.light[0], ry = 15;
        const [x, dy, z, fov] = K(u, [[0, 0, 3.8, 17.5, 42], [1, -1.5, 2.8, 15.5, 48]]);
        return { p: [x, ry + dy, z], t: [-5.5, ry + .4, 9.5], fov };
      },
    },
    {
      id: "street", T0: 59, rate: 1,
      cam(u) {
        const [x, y, z, ty, fov] = K(u, [[0, -24, 1.62, 33, 6, 60], [.5, -15, 1.62, 31, 13, 62], [1, -4, 1.62, 30, 26, 64]]);
        return { p: [x, y, z], t: [2, ty, 0], fov };
      },
    },
    {
      id: "storm", T0: 65, rate: 0, scenario: STORM,
      pre() { s.scene.background = new (s.scene.fog.color.constructor)(0x59646c); s.scene.fog.near = 60; s.scene.fog.far = 420; },
      post(u) { exposure(1.5); A.net.scale.y = lerp(1, .12, sm(clamp((u - .1) / .6, 0, 1))); },
      cam(u) {
        const [deg, r, y, ty] = K(u, [[0, 74, 112, 58, 24], [1, 96, 106, 50, 26]]);
        return { p: orbit(deg, r, y), t: [0, ty, 0], fov: 44 };
      },
    },
    {
      id: "descend", T0: 56, rate: 3,
      cam(u) {
        const [deg, r, y, ty] = K(u, [[0, 30, 110, 66, 26], [1, 88, 104, 52, 18]]);
        return { p: orbit(deg, r, y), t: [0, ty, 0], fov: 40 };
      },
    },
    {
      id: "neighbor", T0: 90, rate: 0, scenario: DAY_END,
      cam(u) {
        const [x, ty] = K(u, [[0, -22, 13], [1, -10, 22]]);
        return { p: [x, 1.62, 33], t: [4, ty, 0], fov: 62 };
      },
    },
    {
      id: "finale", T0: 90, rate: 0, scenario: DAY_END,
      cam(u) {
        const [deg, r, y] = K(u, [[0, 96, 104, 6], [1, 84, 98, 5]]);
        return { p: orbit(deg, r, y), t: [0, 30, 0], fov: 42 };
      },
    },
    {
      id: "end", T0: 90, rate: 0, scenario: NIGHT_END,
      pre() { A.nightLights.forEach((l) => (l.intensity = 520)); },
      cam(u) {
        const [deg, r, y, ty] = K(u, [[0, 100, 104, 14, 22], [1, 84, 112, 34, 22]]);
        return { p: orbit(deg, r, y), t: [0, ty, 0], fov: 40 };
      },
    },
    {
      id: "factory", T0: 44, rate: 1,
      cam(u) {
        const P = s.D.meta.plant;
        const [dx, y, dz, tx, fov] = K(u, [[0, -34, 34, -68, 0, 44], [1, -16, 25, -60, 8, 46]]);
        return { p: [P[0] + dx, y, -P[1] + dz], t: [P[0] + tx, 3, -P[1] - 4], fov };
      },
    },
  ];

  window.__SHOTS.forEach((x) => (x.dur = DUR[x.id] ?? x.dur));
  const byId = (id) => window.__SHOTS.find((x) => x.id === id);
  const rig = window.__rig;
  const smooth = { p: new V(), t: new V(), init: false };
  const placeCam = (sh, u, dt) => {
    const c = sh.cam(u);
    if (c.track && smooth.init) {
      const k = 1 - Math.exp(-dt * c.track * 2);
      smooth.p.lerp(new V(...c.p), k); smooth.t.lerp(new V(...c.t), k);
    } else { smooth.p.set(...c.p); smooth.t.set(...c.t); smooth.init = true; }
    rig.p.copy(smooth.p); rig.t.copy(smooth.t); rig.fov = c.fov; rig.active = true;
  };

  window.__beginShot = (id) => {
    const sh = byId(id);
    s.runScenario(sh.scenario || { id: "none", name: "", T: Math.max(sh.T0 - sh.rate * 2, 0), fx: "day", cam: "overview", steps: [] });
    s.setTwin(!!sh.twin);
    A.nightLights.forEach((l) => (l.intensity = 900));
    sh.pre?.();
    rig.post = null;
    s.renderer.toneMappingExposure = .86;
    smooth.init = false;
    // 預跑兩秒讓手臂與鏡頭就位，鏡頭跟隨才不會從遠處滑入
    const pre = 60;
    for (let i = 0; i < pre; i++) {
      if (sh.rate) s.setT(sh.T0 - sh.rate * (pre - i) / 30);
      placeCam(sh, 0, 1 / 30);
      rig.post = sh.post ? () => sh.post(0) : null;
      window.__step(1000 / 30);
    }
  };

  window.__renderFrame = async (id, i, N, stride, fps) => {
    const sh = byId(id), dt = 1 / fps;
    for (let j = 0; j < stride; j++) {
      const f = i + j, u = f / Math.max(N - 1, 1);
      if (sh.rate) s.setT(sh.Tf ? sh.Tf(f / fps) : sh.T0 + sh.rate * f / fps);
      placeCam(sh, u, dt);
      rig.post = sh.post ? () => sh.post(u) : null;
      window.__step(1000 / fps);
    }
    const blob = await new Promise((r) => s.renderer.domElement.toBlob(r, "image/jpeg", .96));
    await fetch(`/frame?shot=${id}&i=${i}`, { method: "POST", body: blob });
  };
})();
