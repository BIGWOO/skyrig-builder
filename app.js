import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.170.0/+esm";
import { GLTFLoader } from "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/loaders/GLTFLoader.js/+esm";
import { OrbitControls } from "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/controls/OrbitControls.js/+esm";
import { PHASE_TEXT, LAYERS, SCENARIOS, CAMERAS, AI_STEPS, AI_CONFLICTS, TOUR, PLANT_PINS } from "./content.js";

const $ = (id) => document.getElementById(id);
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const lerp = (a, b, k) => a + (b - a) * k;
const ease = (k) => k * k * (3 - 2 * k);
const B = (x, y, z, v = new THREE.Vector3()) => v.set(x, z, -y);

const U = { uT: { value: 0 }, uQuake: { value: 0 }, uH: { value: 44 } };
const clipPlane = new THREE.Plane(new THREE.Vector3(0, 0, -1), 200);
const REVEAL = /* glsl */ `
  tMat = instanceMatrix;
  float rk = clamp((uT - aTime.x) / max(aTime.y, .0001), 0., 1.);
  float re = clamp((uT - aTime.z) / max(aTime.w, .0001), 0., 1.);
  float rm = aFrom.w;
  float rs = rk * rk * (3. - 2. * rk);
  if (rm < .5) tMat[1] *= max(rs, .001);
  else if (rm < 1.5) tMat[3].xyz += aFrom.xyz * (1. - rs);
  else { float q = max(rs, .001); tMat[0] *= q; tMat[1] *= q; tMat[2] *= q; }
  if (re > 0.) {
    if (rm < .5) tMat[1] *= max(1. - re, .001);
    else { float q = max(1. - re, .001); tMat[0] *= q; tMat[1] *= q; tMat[2] *= q; }
  }
  if (rk <= 0. || re >= 1.) { tMat[0] *= .00001; tMat[1] *= .00001; tMat[2] *= .00001; }
  float hh = max(tMat[3].y, 0.) / uH;
  tMat[3].x += uQuake * pow(hh, 1.2);
  tMat[1].x += uQuake * (1.2 / uH) * pow(max(hh, .001), .2) * tMat[1].y;
  #define instanceMatrix tMat
`;

function patch(mat) {
  mat.onBeforeCompile = (s) => {
    s.uniforms.uT = U.uT;
    s.uniforms.uQuake = U.uQuake;
    s.uniforms.uH = U.uH;
    s.vertexShader = `attribute vec4 aTime;\nattribute vec4 aFrom;\nuniform float uT;\nuniform float uQuake;\nuniform float uH;\nmat4 tMat;\n` +
      s.vertexShader.replace("void main() {", `void main() {\n${REVEAL}`);
  };
  mat.customProgramCacheKey = () => "reveal-v1";
  return mat;
}

let D, lib = {};
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(38, 1, .3, 900);
const canvas = $("view");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: "high-performance", preserveDrawingBuffer: true });
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = .86;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.localClippingEnabled = true;
let pixelRatio = Math.min(devicePixelRatio, 1.75);
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.maxPolarAngle = Math.PI * .52;
controls.minDistance = 3;
controls.maxDistance = 240;

const sun = new THREE.DirectionalLight(0xfff0dc, 2.6);
sun.position.set(-48, 90, 54);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -72, right: 72, top: 72, bottom: -72, near: 10, far: 220 });
sun.shadow.bias = -.0006;
sun.shadow.normalBias = .03;
sun.shadow.autoUpdate = false;
scene.add(sun);
const hemi = new THREE.HemisphereLight(0xcfe2f2, 0x8a8172, .55);
scene.add(hemi);
scene.fog = new THREE.Fog(0xcdd9df, 150, 620);

function makeSky(top, mid, low, cloud) {
  const c = document.createElement("canvas");
  c.width = 1024; c.height = 512;
  const g = c.getContext("2d");
  const grad = g.createLinearGradient(0, 0, 0, 512);
  grad.addColorStop(0, top); grad.addColorStop(.42, mid); grad.addColorStop(.5, low); grad.addColorStop(.52, "#6f716c"); grad.addColorStop(1, "#4d4c47");
  g.fillStyle = grad; g.fillRect(0, 0, 1024, 512);
  let seed = 9;
  const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  g.globalCompositeOperation = "lighter";
  for (let i = 0; i < 320; i++) {
    const x = rnd() * 1024, y = 60 + rnd() * 180, r = 14 + rnd() * 54;
    const f = g.createRadialGradient(x, y, 0, x, y, r);
    f.addColorStop(0, cloud); f.addColorStop(1, "rgba(0,0,0,0)");
    g.fillStyle = f; g.save(); g.translate(x, y); g.scale(2.2, .55); g.translate(-x, -y);
    g.fillRect(x - r, y - r, r * 2, r * 2); g.restore();
  }
  const t = new THREE.CanvasTexture(c);
  t.mapping = THREE.EquirectangularReflectionMapping;
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
const pmrem = new THREE.PMREMGenerator(renderer);
const SKY = {};
function skyOf(name) {
  if (SKY[name]) return SKY[name];
  const def = {
    day: ["#4f86b8", "#a9cbe0", "#e4e6df", "rgba(255,255,255,.05)"],
    storm: ["#39444e", "#66727b", "#8f9796", "rgba(190,195,200,.07)"],
    night: ["#070c18", "#121c30", "#2c3448", "rgba(70,80,110,.03)"],
  }[name];
  const bg = makeSky(...def);
  return (SKY[name] = { bg, env: pmrem.fromEquirectangular(bg).texture });
}

const layerMeshes = {};
const actorsByLayer = {};
function reg(layer, o) { (layerMeshes[layer] ||= []).push(o); return o; }

function loadLibrary(gltf) {
  gltf.scene.updateMatrixWorld(true);
  for (const node of gltf.scene.children) {
    const prims = [];
    node.traverse((m) => { if (m.isMesh) prims.push(m); });
    lib[node.name] = prims;
  }
  const seen = new Set();
  gltf.scene.traverse((m) => {
    if (!m.isMesh || seen.has(m.material)) return;
    seen.add(m.material);
    const M = m.material;
    M.envMapIntensity = 1;
    if (M.map) M.map.anisotropy = 8;
    const n = M.name;
    if (n === "glass") Object.assign(M, { transparent: true, opacity: .34, roughness: .05, metalness: .55, depthWrite: false });
    if (n === "etfe") Object.assign(M, { transparent: true, opacity: .42, side: THREE.DoubleSide, depthWrite: false });
    if (n === "net") {
      const c = document.createElement("canvas");
      c.width = c.height = 128;
      const g = c.getContext("2d");
      g.strokeStyle = "rgba(38,52,56,.72)";
      g.lineWidth = 4;
      g.strokeRect(0, 0, 128, 128);
      const t = new THREE.CanvasTexture(c);
      t.wrapS = t.wrapT = THREE.RepeatWrapping;
      t.colorSpace = THREE.SRGBColorSpace;
      t.anisotropy = 8;
      t.repeat.set(2, 2);
      Object.assign(M, { map: t, color: new THREE.Color(0xffffff), transparent: true, opacity: 1, side: THREE.DoubleSide, depthWrite: false, roughness: .6, metalness: .3 });
    }
    if (n === "lamp") { M.emissiveIntensity = .2; lampMats.push(M); }
  });
}
const lampMats = [];

const patched = new Map();
function patchedMat(m, clip) {
  const key = m.uuid + (clip ? "c" : "");
  if (patched.has(key)) return patched.get(key);
  const c = patch(m.clone());
  if (clip) c.clippingPlanes = [clipPlane];
  patched.set(key, c);
  return c;
}
const depthMat = patch(new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking }));

const partRange = [];
function buildItems() {
  const tmp = new THREE.Object3D();
  for (const [part, rows] of Object.entries(D.items)) {
    const info = D.parts[part];
    const prims = lib[part];
    if (!prims) { console.warn("missing part", part); continue; }
    const aTime = new Float32Array(rows.length * 4);
    const aFrom = new Float32Array(rows.length * 4);
    rows.forEach((r, i) => {
      aTime.set([r[7], r[8], r[9], r[10]], i * 4);
      aFrom.set([r[11], r[13], -r[12], r[14]], i * 4);
    });
    const tMin = Math.min(...rows.map((r) => r[7]));
    const tMax = Math.max(...rows.map((r) => r[9] + r[10]));
    for (const prim of prims) {
      const g = prim.geometry.clone();
      if (part === "led_screen") ledUV(g);
      g.setAttribute("aTime", new THREE.InstancedBufferAttribute(aTime, 4));
      g.setAttribute("aFrom", new THREE.InstancedBufferAttribute(aFrom, 4));
      const clip = info.layer !== "site" && info.layer !== "rig";
      const mesh = new THREE.InstancedMesh(g, patchedMat(prim.material, clip), rows.length);
      if (part === "led_screen") { mesh.material = ledMaterial(); }
      rows.forEach((r, i) => {
        tmp.position.set(r[0], r[2], -r[1]);
        tmp.rotation.set(0, r[3], 0);
        tmp.scale.set(r[4], r[6], r[5]);
        tmp.updateMatrix();
        mesh.setMatrixAt(i, tmp.matrix);
      });
      mesh.frustumCulled = false;
      const transparent = prim.material.transparent;
      mesh.castShadow = !transparent && info.layer !== "rebar";
      mesh.receiveShadow = !transparent;
      if (!transparent) mesh.customDepthMaterial = depthMat;
      mesh.userData = { part, rows };
      scene.add(mesh);
      reg(info.layer, mesh);
      partRange.push({ mesh, tMin, tMax });
      pickables.push(mesh);
    }
  }
}
const pickables = [];

let ledCanvas, ledCtx, ledTex;
function ledUV(g) {
  const p = g.attributes.position, uv = g.attributes.uv;
  for (let i = 0; i < p.count; i++) uv.setXY(i, (p.getX(i) + 5.1) / 10.2, (p.getY(i) - 3.2) / 3.6);
}
function ledMaterial() {
  ledCanvas = document.createElement("canvas");
  ledCanvas.width = 680; ledCanvas.height = 240;
  ledCtx = ledCanvas.getContext("2d");
  ledTex = new THREE.CanvasTexture(ledCanvas);
  ledTex.colorSpace = THREE.SRGBColorSpace;
  return patch(new THREE.MeshStandardMaterial({ color: 0x000000, emissive: 0xffffff, emissiveMap: ledTex, emissiveIntensity: 1.1, roughness: .4 }));
}
function drawLED(T) {
  if (!ledCtx) return;
  const g = ledCtx, st = currentStatus(T);
  g.fillStyle = "#050807"; g.fillRect(0, 0, 680, 240);
  g.fillStyle = "#f0b429"; g.font = "700 30px 'Noto Sans TC',sans-serif"; g.fillText("天架造樓 工程進度", 24, 46);
  g.fillStyle = "#fff"; g.font = "800 92px 'Big Shoulders Display',sans-serif"; g.fillText(`${Math.round(T / D.meta.T * 100)}%`, 24, 142);
  g.font = "600 34px 'Noto Sans TC',sans-serif"; g.fillText(`第 ${Math.floor(T)} 天 ${st.floor}`, 220, 112);
  g.fillStyle = "#9fe3c0"; g.font = "500 25px 'Noto Sans TC',sans-serif"; g.fillText("噪音 62 dB  PM2.5 14 μg/m³ 示意值", 24, 200);
  g.fillStyle = "#ddd"; g.fillText(st.text.slice(0, 18), 220, 152);
  ledTex.needsUpdate = true;
}

function clonePart(name, parent, opts = {}) {
  const g = new THREE.Group();
  g.name = name;
  for (const p of lib[name]) {
    const mat = p.material;
    const m = new THREE.Mesh(p.geometry, mat);
    m.castShadow = !mat.transparent && opts.shadow !== false;
    m.receiveShadow = !mat.transparent;
    m.userData.part = name;
    g.add(m);
  }
  parent?.add(g);
  return g;
}

function buildArm(prefix, L1, L2, shoulder, hang, parent) {
  const root = new THREE.Group();
  parent.add(root);
  if (hang) root.rotation.x = Math.PI;
  const yaw = new THREE.Group(); root.add(yaw);
  clonePart(`${prefix}_base`, yaw);
  const sh = new THREE.Group(); sh.position.y = shoulder; yaw.add(sh);
  clonePart(`${prefix}_upper`, sh);
  const el = new THREE.Group(); el.position.x = L1; sh.add(el);
  clonePart(`${prefix}_fore`, el);
  const wr = new THREE.Group(); wr.position.x = L2; el.add(wr);
  clonePart(`${prefix}_wrist`, wr);
  return { root, yaw, sh, el, wr, L1, L2, shoulder, hang };
}
const v0 = new THREE.Vector3(), v1 = new THREE.Vector3();
function solveArm(a, world) {
  a.root.updateWorldMatrix(true, false);
  const l = a.root.worldToLocal(v0.copy(world));
  a.yaw.rotation.y = Math.atan2(-l.z, l.x);
  const r = Math.hypot(l.x, l.z), h = l.y - a.shoulder;
  const d = clamp(Math.hypot(r, h), .4, a.L1 + a.L2 - .02);
  const base = Math.atan2(h, r);
  const q1 = Math.acos(clamp((a.L1 ** 2 + d ** 2 - a.L2 ** 2) / (2 * a.L1 * d), -1, 1));
  const q2 = Math.acos(clamp((a.L1 ** 2 + a.L2 ** 2 - d ** 2) / (2 * a.L1 * a.L2), -1, 1));
  a.sh.rotation.z = base + q1;
  a.el.rotation.z = -(Math.PI - q2);
  a.wr.rotation.z = -(a.sh.rotation.z + a.el.rotation.z) + (a.hang ? Math.PI : 0);
}

const A = {};
function buildActors() {
  const rig = A.rig = new THREE.Group(); scene.add(rig); reg("rig", rig);
  clonePart("ring_a", rig);
  A.arches = [];
  for (let i = 0; i < 7; i++) {
    const a = clonePart("roof_frame", rig);
    a.userData.x0 = -D.meta.ringX + i * 7;
    a.position.x = a.userData.x0;
    A.arches.push(a);
  }
  A.panels = [];
  for (let i = 0; i < 6; i++) {
    const p = clonePart("roof_panel", rig, { shadow: false });
    p.userData.closedX = -17.5 + i * 7;
    A.panels.push(p);
  }
  const net = A.net = new THREE.Group(); rig.add(net); reg("net", net);
  const { ringX: RX, ringY: RY } = D.meta;
  for (const [n, x, z, ry] of [["net_x", 0, RY + 1.05, 0], ["net_x", 0, -RY - 1.05, Math.PI], ["net_y", RX + 1.05, 0, Math.PI / 2], ["net_y", -RX - 1.05, 0, -Math.PI / 2]]) {
    const m = clonePart(n, net, { shadow: false });
    m.position.set(x, 0, z); m.rotation.y = ry;
  }
  A.heavy = [["H0", -1], ["H1", 1]].map(([id, dir]) => {
    const bridge = clonePart("bridge", rig);
    const trolley = clonePart("trolley", bridge);
    trolley.position.y = 0;
    const top = clonePart("tele_top", trolley);
    const tele = clonePart("tele", trolley);
    tele.position.y = -2;
    const mount = new THREE.Group(); trolley.add(mount);
    const arm = buildArm("arm_h", 3.4, 3.2, .9, true, mount);
    return { id, dir, bridge, trolley, tele, mount, arm, p: new THREE.Vector3(dir * 12, 8, 0), kind: -1 };
  });
  const rigB = A.rigB = new THREE.Group(); scene.add(rigB); reg("rig", rigB);
  clonePart("ring_b", rigB);
  const rail = RY - .95, railX = RX - .95;
  const sides = { S0: [0, 1], S1: [0, 1], N0: [0, -1], N1: [0, -1], E0: [1, 0], W0: [-1, 0] };
  A.light = Object.entries(sides).map(([id, [sx, sz]]) => {
    const car = clonePart("carriage", rigB);
    car.position.set(sx * railX, .28, sz * rail);
    const tele = clonePart("tele", car);
    tele.position.y = .3; tele.scale.set(.32, 1, .32); tele.rotation.x = Math.PI;
    const mount = new THREE.Group(); car.add(mount);
    const arm = buildArm("arm_l", 1.7, 1.6, .38, false, mount);
    return { id, sx, sz, car, tele, mount, arm, rail, railX, p: new THREE.Vector3(sx * 15, 6, sz * 9), kind: -1 };
  });
  A.hoist = clonePart("hoist_cage", scene);
  A.hoist.position.set(0, 0, -(RY + 2.1));
  reg("rig", A.hoist);

  const streamGeo = new THREE.CylinderGeometry(.12, .2, 1, 8);
  streamGeo.translate(0, -.5, 0);
  A.stream = A.heavy.map(() => { const m = new THREE.Mesh(streamGeo, new THREE.MeshStandardMaterial({ color: 0x8f918c, roughness: .4 })); m.visible = false; scene.add(m); return m; });

  const N = 120;
  A.sparkPos = new Float32Array(N * 3);
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(A.sparkPos, 3));
  A.sparks = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffc56b, size: .1, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
  A.sparks.frustumCulled = false;
  scene.add(A.sparks);

  A.pool = {};
  A.bots = [];
  const maxPer = {};
  for (const b of D.bots) maxPer[b[0]] = 0;
  for (const b of D.bots) {
    const n = D.bots.filter((o) => o[0] === b[0] && o[1] < b[2] && o[2] > b[1]).length;
    maxPer[b[0]] = Math.max(maxPer[b[0]], Math.min(n, 5));
  }
  for (const [name, n] of Object.entries(maxPer)) {
    A.pool[name] = [];
    for (let i = 0; i < n; i++) {
      const o = clonePart(name, scene);
      o.visible = false;
      reg("robot", o);
      if (name === "precast_truck") o.userData.load = clonePart("precast_load", o);
      A.pool[name].push(o);
    }
  }
  buildRoute();
  A.cars = Array.from({ length: 12 }, (_, i) => {
    const c = clonePart("car", scene);
    c.userData.lane = i % 2;
    c.userData.ph = i * 47;
    return c;
  });
  A.walk = [];
  for (let i = 0; i < 10; i++) {
    const p = clonePart(i % 2 ? "person_a" : "person_b", scene);
    p.userData.ph = i * 19;
    A.walk.push(p);
  }
}

function rigZ(T) {
  const k = D.rigKeys;
  if (T <= k[0][0]) return k[0][1];
  for (let i = 1; i < k.length; i++) if (T <= k[i][0]) return lerp(k[i - 1][1], k[i][1], (T - k[i - 1][0]) / Math.max(k[i][0] - k[i - 1][0], 1e-6));
  return k[k.length - 1][1];
}

// 預鑄運輸：工廠裝車 → 道路 → 進工地卸貨 → 倒車回到車道 → 回工廠。座標為藍圖座標
const TRUCK = { days: 7, end: 0, go: null, stub: null, ret: null };
function polyLen(pts) { let n = 0; for (let i = 1; i < pts.length; i++) n += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); return n; }
function polyAt(pts, d, out) {
  for (let i = 1; i < pts.length; i++) {
    const a = pts[i - 1], b = pts[i], n = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (d <= n || i === pts.length - 1) { const k = clamp(d / n, 0, 1); out.x = lerp(a[0], b[0], k); out.y = lerp(a[1], b[1], k); return out; }
    d -= n;
  }
  return out;
}
function buildRoute() {
  const [px, py] = D.meta.plant, G = px + 10, Y = py + 30;
  TRUCK.end = D.bots.find((b) => b[8] === 3)[2];
  TRUCK.go = [[G - 1.6, Y], [G - 1.6, -22.8], [23.7, -22.8], [23.7, -8]];
  TRUCK.stub = [[23.7, -8], [23.7, -20.2]];
  TRUCK.ret = [[23.7, -20.2], [G + 1.6, -20.2], [G + 1.6, Y], [G - 1.6, Y]];
  const pos = [], idx = [], v = { x: 0, y: 0 }, w = { x: 0, y: 0 };
  for (const path of [TRUCK.go, TRUCK.ret]) {
    const L = polyLen(path);
    for (let d = 2; d < L - 3; d += 6) {
      polyAt(path, d, v); polyAt(path, d + 3, w);
      const nx = -(w.y - v.y) / 3 * .3, ny = (w.x - v.x) / 3 * .3, n = pos.length / 3;
      pos.push(v.x + nx, .07, -(v.y + ny), v.x - nx, .07, -(v.y - ny), w.x - nx, .07, -(w.y - ny), w.x + nx, .07, -(w.y + ny));
      idx.push(n, n + 1, n + 2, n, n + 2, n + 3);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  g.setIndex(idx);
  A.route = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color: 0xf0b429, side: THREE.DoubleSide, transparent: true, opacity: .85, depthWrite: false }));
  A.route.frustumCulled = false;
  scene.add(A.route);
  const c = document.createElement("canvas"); c.width = 512; c.height = 128;
  const x = c.getContext("2d");
  x.fillStyle = "#1b2529"; x.fillRect(0, 0, 512, 128);
  x.fillStyle = "#f0b429"; x.fillRect(0, 0, 512, 10);
  x.fillStyle = "#eef0ea"; x.font = "700 62px 'Noto Sans TC','Microsoft JhengHei',sans-serif"; x.textAlign = "center"; x.fillText("預鑄工廠", 256, 92);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  A.plantLabel = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, fog: false }));
  A.plantLabel.position.set(px, 22, -py);
  A.plantLabel.scale.set(28, 7, 1);
  scene.add(A.plantLabel);
}
const tv2 = { x: 0, y: 0 };
function truckPose(s, out) {
  const go = polyLen(TRUCK.go), stub = polyLen(TRUCK.stub), ret = polyLen(TRUCK.ret);
  let hx, hy;
  if (s < .04) {
    // 回程到堆場時車頭朝西，出發前原地轉回朝北
    polyAt(TRUCK.go, 0, out); out.loaded = true;
    const a = lerp(Math.PI, Math.PI / 2, ease(s / .04));
    tv2.x = out.x + Math.cos(a); tv2.y = out.y + Math.sin(a);
  }
  else if (s < .46) { const d = ease((s - .04) / .42) * go; polyAt(TRUCK.go, d, out); polyAt(TRUCK.go, d + 5, tv2); out.loaded = true; if (d + 5 > go) { tv2.x = out.x; tv2.y = out.y + 5; } }
  else if (s < .58) { polyAt(TRUCK.go, go, out); tv2.x = out.x; tv2.y = out.y + 5; out.loaded = s < .54; }
  else if (s < .63) { const d = ease((s - .58) / .05) * stub; polyAt(TRUCK.stub, d, out); tv2.x = out.x; tv2.y = out.y + 5; out.loaded = false; }
  else { const d = ease((s - .63) / .37) * ret; polyAt(TRUCK.ret, d, out); polyAt(TRUCK.ret, d + 5, tv2); out.loaded = false; if (d + 5 > ret) { tv2.x = out.x - 5; tv2.y = out.y; } }
  hx = tv2.x - out.x; hy = tv2.y - out.y;
  out.rz = Math.atan2(hy, hx);
  return out;
}
let truckOff = 0;

const taskIdx = {};
function activeTask(id, T) {
  const list = D.tasks[id];
  let lo = 0, hi = list.length - 1, ans = -1;
  while (lo <= hi) { const m = (lo + hi) >> 1; if (list[m][0] <= T) { ans = m; lo = m + 1; } else hi = m - 1; }
  if (ans < 0) return null;
  const t = list[ans];
  return T < t[1] ? t : null;
}
const tv = new THREE.Vector3(), pk = new THREE.Vector3(), pl = new THREE.Vector3();
function armTarget(t, T, out) {
  B(t[2], t[3], t[4], pk); B(t[5], t[6], t[7], pl);
  const u = (T - t[0]) / Math.max(t[1] - t[0], 1e-6);
  if (t[8] === 0) {
    if (u < .25) out.copy(pk);
    else if (u < .85) out.copy(pk).lerp(pl, ease((u - .25) / .6));
    else out.copy(pl).lerp(pk, ease((u - .85) / .15));
  } else out.copy(pl);
  return out;
}

let override = { park: false, netRoll: 0, roof: null };
let dtFrame = .016, simTime = 0;
function updateActors(T) {
  const on = T >= D.meta.tRigOn && T <= D.meta.tRigOff;
  const z = rigZ(T);
  const layerRig = layerState.rig;
  A.rig.visible = on && layerRig;
  A.rigB.visible = on && layerRig && T > D.meta.tRingOn;
  A.hoist.visible = on && layerRig;
  A.rig.position.y = z;
  A.rigB.position.y = Math.max(z - 15.5, 1.5);
  A.net.scale.y = lerp(1, .12, override.netRoll);
  A.net.visible = layerState.net && T > D.meta.tRingOn && !twin.on;
  const roofOpen = override.roof != null ? 1 - override.roof : .94;
  // 頂棚要在天架下降前拆完：膜片先往兩端吊出，再放到地面；拱架由外而內逐支吊離
  const rOff = clamp((T - D.meta.tRoofOff0) / (D.meta.tRoofOff1 - D.meta.tRoofOff0), 0, 1);
  A.panels.forEach((p, i) => {
    const k = clamp((rOff - i * .06) / .4, 0, 1), dir = i > 2 ? 1 : -1;
    p.position.x = lerp(p.userData.closedX, -17.5 + (i > 2 ? 35 : 0) + i * .35 * (i > 2 ? -1 : 1), roofOpen) + dir * 14 * ease(Math.min(k / .35, 1));
    p.position.y = -z * ease(clamp((k - .35) / .65, 0, 1));
    p.visible = k < 1;
  });
  A.arches.forEach((a, i) => {
    const n = 3 - Math.abs(i - 3), k = clamp((rOff - .42 - n * .07) / .36, 0, 1), dir = i < 3 ? -1 : 1;
    const clear = D.meta.ringX + 7 + n * 2 - Math.abs(a.userData.x0);
    a.position.x = a.userData.x0 + dir * clear * ease(Math.min(k / .35, 1));
    a.position.y = -z * ease(clamp((k - .35) / .65, 0, 1));
    a.visible = k < 1;
  });
  A.route.visible = T < TRUCK.end + TRUCK.days && !twin.on;
  A.plantLabel.visible = !twin.on;
  const hoistSpan = Math.max(z - 5.5, 1);
  const cyc = (T * 6.4) % 1;
  A.hoist.position.y = on ? hoistSpan * (cyc < .5 ? ease(cyc * 2) : 1 - ease((cyc - .5) * 2)) : 0;

  let spark = null, stIdx = 0;
  if (!on || !layerRig) { A.stream.forEach((s) => (s.visible = false)); }
  else A.heavy.forEach((h, i) => {
    const off = T >= D.meta.tRoofOff0;
    const t = override.park || off ? null : activeTask(h.id, T);
    const home = off ? tv.set(h.dir * 22, z - 3.5, 0) : tv.set(h.dir * 15, z - 3.5, -h.dir * 4);
    if (t) armTarget(t, T, home);
    h.p.lerp(home, 1 - Math.exp(-dtFrame * 14));
    const dir = h.dir;
    const bx = clamp(h.p.x - dir * 2.3, -D.meta.ringX + 1.2, D.meta.ringX - 1.2);
    h.bridge.position.set(bx, 0, 0);
    const tz = clamp(h.p.z, -D.meta.ringY + 1.3, D.meta.ringY - 1.3);
    h.trolley.position.z = tz;
    const drop = clamp(z - h.p.y - 2.2, .2, 90);
    h.tele.scale.y = Math.max(drop - 2.1 - .3, .05) + 0;
    h.tele.position.y = -2;
    h.mount.position.y = 1.2 - (drop) ;
    solveArm(h.arm, h.p);
    const pouring = t && t[8] === 2;
    const st = A.stream[i];
    st.visible = !!pouring;
    if (pouring) { st.position.copy(h.p); st.position.y -= .4; st.scale.y = 2.9; }
  });
  let n = 0;
  if (on && layerRig) for (const l of A.light) {
    const t = override.park ? null : activeTask(l.id, T);
    const home = tv.set(l.sx * (l.railX - 2.2), A.rigB.position.y + 1.8, l.sz * (l.rail - 2.2));
    if (t) armTarget(t, T, home);
    l.p.lerp(home, 1 - Math.exp(-dtFrame * 16));
    const lift = clamp(l.p.y - A.rigB.position.y - 1.1, -9, 9);
    if (l.sz) l.car.position.x = clamp(l.p.x, -D.meta.ringX + 1, D.meta.ringX - 1);
    else l.car.position.z = clamp(l.p.z, -D.meta.ringY + 1, D.meta.ringY - 1);
    l.mount.position.y = lift;
    l.tele.visible = Math.abs(lift) > .2;
    l.tele.scale.y = Math.abs(lift);
    l.tele.rotation.x = lift > 0 ? Math.PI : 0;
    solveArm(l.arm, l.p);
    if (t && t[8] === 1) spark = l.p;
  }
  updateSparks(spark);
  updateBots(T);
}

function updateSparks(p) {
  const a = A.sparkPos;
  if (!p) { A.sparks.visible = false; return; }
  A.sparks.visible = true;
  for (let i = 0; i < a.length; i += 3) {
    const q = (simTime * 2 + i * .137) % 1;
    const ang = i * 2.4;
    a[i] = p.x + Math.cos(ang) * q * .7;
    a[i + 1] = p.y - .3 + .3 * q - 1.8 * q * q;
    a[i + 2] = p.z + Math.sin(ang) * q * .7;
  }
  A.sparks.geometry.attributes.position.needsUpdate = true;
}

const SWEEP_ROWS = 5;
function sweepAt(b, u, out) {
  const [, , , , x0, y0, x1, y1] = b;
  const rows = SWEEP_ROWS;
  const f = clamp(u, 0, 1) * rows;
  const r = Math.min(Math.floor(f), rows - 1);
  const q = f - r;
  out.x = lerp(x0, x1, r % 2 ? 1 - q : q);
  out.y = lerp(y0, y1, (r + (q > .94 ? (q - .94) / .06 : 0)) / rows);
}
const pa = { x: 0, y: 0 }, pb = { x: 0, y: 0 };
function updateBots(T) {
  const used = {};
  for (const k in A.pool) { used[k] = 0; for (const o of A.pool[k]) o.visible = false; }
  if (!layerState.robot) return;
  for (const b of D.bots) {
    if (T < b[1]) break;
    if (T > b[2] + (b[8] === 3 ? TRUCK.days : 0)) continue;
    const name = b[0], o = A.pool[name][used[name]];
    if (!o) continue;
    used[name]++;
    o.visible = true;
    if (b[8] === 3) {
      const c = (tour.on ? tour.clock : T + truckOff) / TRUCK.days + b[4];
      // 排程結束後不再發車，正在路上的車跑完這一趟才收
      if (T > b[2] && Math.floor(c) > Math.floor((b[2] + truckOff) / TRUCK.days + b[4])) { o.visible = false; continue; }
      const q = truckPose(((c % 1) + 1) % 1, pa);
      o.position.set(q.x, 0, -q.y);
      o.rotation.y = q.rz;
      o.userData.load.visible = q.loaded;
      continue;
    }
    const u = (T - b[1]) / Math.max(b[2] - b[1], 1e-6);
    const mode = b[8];
    if (mode === 2) { pa.x = b[4]; pa.y = b[5]; pb.x = pa.x + 1; pb.y = pa.y; if (name === "bot_humanoid") { pb.x = pa.x - 1; pb.y += Math.sin(simTime * 1.1 + b[1]) * .6; } }
    else if (mode === 1) {
      const q0 = ((T - b[1]) / b[9]) % 1, q1 = (q0 + .01) % 1;
      const f = (q) => (q < .5 ? ease(q * 2) : 1 - ease((q - .5) * 2));
      pa.x = lerp(b[4], b[6], f(q0)); pa.y = lerp(b[5], b[7], f(q0));
      pb.x = lerp(b[4], b[6], f(q1)); pb.y = lerp(b[5], b[7], f(q1));
    } else { sweepAt(b, u, pa); sweepAt(b, u + .004, pb); }
    const dx = pb.x - pa.x, dy = pb.y - pa.y;
    o.position.set(pa.x, b[3] + (name === "drone" ? Math.sin(simTime * 2) * .3 : .0), -pa.y);
    if (Math.hypot(dx, dy) > 1e-5) o.rotation.y = Math.atan2(dy, dx);
  }
}

function updateAmbient() {
  for (const c of A.cars) {
    const q = (simTime * 9 + c.userData.ph) % 570, east = c.userData.lane;
    c.position.set(east ? q - 110 : 460 - q, .02, east ? 28.6 : 26);
    c.rotation.y = east ? 0 : Math.PI;
  }
  for (const p of A.walk) {
    const x = ((simTime * 1.1 + p.userData.ph) % 120) - 102;
    p.position.set(x, .08, 16.9 + (p.userData.ph % 3) * .45);
    p.rotation.y = 0;
  }
}

function currentStatus(T) {
  const s = D.meta.storeys;
  let floor = "基地", text = "";
  for (const e of D.log) { if (T >= e[0] && T < e[1]) text = e[2]; if (e[0] > T) break; }
  const phase = D.phases.find((p) => T >= p.t0 && T < p.t1) || D.phases[D.phases.length - 1];
  for (const st of s) if (T >= st[3]) floor = st[0];
  if (T < s[0][3]) floor = T < 18 ? "地面層" : "地下開挖";
  if (T >= s[s.length - 1][3] + 2) floor = "全棟";
  return { floor, text: text || phase.name, phase };
}

const layerState = Object.fromEntries(LAYERS.map(([k]) => [k, true]));
let T = 0, playing = false, speed = 1, lastPhase = null, shadowTick = 0, currentScenario = null;

function applyLayers() {
  for (const [k, list] of Object.entries(layerMeshes)) {
    if (k === "rig" || k === "net" || k === "robot") continue;
    if (!(k in layerState)) continue;
    for (const m of list) m.userData.layerOn = layerState[k];
  }
  shadowDirty = true;
}
let shadowDirty = true;
function setT(next, fromUser) {
  T = clamp(next, 0, D.meta.T);
  U.uT.value = T;
  for (const r of partRange) {
    const on = r.mesh.userData.layerOn !== false;
    r.mesh.visible = on && T >= r.tMin && T <= r.tMax + 1;
  }
  shadowDirty = true;
  updateUI(fromUser);
}

function updateUI() {
  const st = currentStatus(T);
  $("day").textContent = `D+${String(Math.floor(T)).padStart(3, "0")}`;
  $("pct").textContent = `${Math.round(T / D.meta.T * 100)}%`;
  $("floor").textContent = st.floor;
  $("now").textContent = st.text;
  $("scrub").value = T;
  $("scrub").setAttribute("aria-valuetext", `第 ${Math.floor(T)} 天，${st.text}`);
  $("playhead").style.left = `${T / D.meta.T * 100}%`;
  if (st.phase !== lastPhase) { lastPhase = st.phase; renderPhase(st.phase); }
}

function renderPhase(p) {
  const c = PHASE_TEXT[p.id];
  $("phaseName").textContent = p.name;
  $("phaseSpan").textContent = `第 ${p.t0} 到 ${p.t1} 天`;
  $("phaseLead").textContent = c.lead;
  $("phaseAuto").innerHTML = c.auto.map(([a, b]) => `<li><b>${a}</b><span>${b}</span></li>`).join("");
  document.querySelectorAll(".seg").forEach((s) => s.classList.toggle("on", s.dataset.id === p.id));
}

const camTween = { active: false, t: 0, dur: 1.3, p0: new THREE.Vector3(), q0: new THREE.Vector3(), p1: new THREE.Vector3(), q1: new THREE.Vector3() };
function workZ() { return Math.max(rigZ(T) - 9, -4); }
function camSpec(id) {
  const z = workZ();
  switch (id) {
    case "street": return [[-20, 1.62, 31.5], [0, 13, 0], 64];
    case "deck": return [[17.5, z + 6.5, 12.5], [-1, z - .5, -1], 50];
    case "rig": return [[-34, z + 22, 34], [0, z + 5, 0], 38];
    case "inside": { const yy = 4.5 + 3.3 * clamp(Math.round((z - 16 - 4.5) / 3.3), 0, 10); return [[-17, yy + 1.5, 3.3], [10, yy + 1.1, 3.3], 62]; }
    case "pit": return [[30, 13, -20], [-3, -6, 1], 42];
    case "factory": return [[D.meta.plant[0] - 14, 27, -D.meta.plant[1] - 60], [D.meta.plant[0] + 8, 3, -D.meta.plant[1] - 8], 44];
    default: { const k = camera.aspect < 1 ? 1.7 : 1; return [[58 * k, 17 + 25 * k, 76 * k], [0, 17, 0], 38]; }
  }
}
function flyTo(id) {
  const [p, q, fov] = camSpec(id);
  camTween.active = true; camTween.t = 0;
  camTween.p0.copy(camera.position); camTween.q0.copy(controls.target);
  camTween.p1.set(...p); camTween.q1.set(...q);
  camTween.f0 = camera.fov; camTween.f1 = fov;
  document.querySelectorAll("#cams button").forEach((b) => b.classList.toggle("on", b.dataset.id === id));
  currentCam = id;
}
let currentCam = "overview";

// 數位孿生：材質改成發光線框，彩色的天架與機器人保留色相，結束後全部還原
const twin = { on: false, saved: new Map() };
function setTwin(on) {
  if (twin.on === on) return;
  twin.on = on;
  const mats = new Set();
  scene.traverse((o) => { if (o.isMesh) [].concat(o.material).forEach((m) => mats.add(m)); });
  const hsl = {};
  for (const m of mats) {
    if (!m.emissive) continue;
    if (on) {
      twin.saved.set(m, { color: m.color.clone(), emissive: m.emissive.clone(), ei: m.emissiveIntensity, wire: m.wireframe, tr: m.transparent, op: m.opacity, bl: m.blending, dw: m.depthWrite });
      m.color.getHSL(hsl);
      const vivid = hsl.s > .45;
      m.emissive.setHSL(vivid ? hsl.h : .55, vivid ? .9 : .85, vivid ? .55 : .62);
      m.emissiveIntensity = vivid ? .7 : .4;
      m.color.set(0);
      m.wireframe = true;
      m.transparent = true; m.opacity = vivid ? .16 : .045; m.blending = THREE.AdditiveBlending; m.depthWrite = false;
      m.needsUpdate = true;
    } else {
      const v = twin.saved.get(m);
      if (!v) continue;
      m.color.copy(v.color); m.emissive.copy(v.emissive); m.emissiveIntensity = v.ei; m.wireframe = v.wire;
      m.transparent = v.tr; m.opacity = v.op; m.blending = v.bl; m.depthWrite = v.dw; m.needsUpdate = true;
    }
  }
  if (on) {
    scene.background = new THREE.Color(0x061220); scene.environment = null;
    sun.intensity = 0; hemi.intensity = 0;
    scene.fog.color.set(0x061220); scene.fog.near = 170;
    fx.rain.visible = false;
  } else setWeather(fx.name);
  shadowDirty = true;
}

const AI_FLOW = { intro: 1.3, rate: 8, hold: 1.9 };
const ai = { on: false, step: -1, t: 0, next: 0, holding: 0 };
function aiStep(i) {
  ai.step = i;
  document.querySelectorAll("#aiSteps li").forEach((li, k) => { li.classList.toggle("on", k === i); li.classList.toggle("done", k < i); });
}
function aiFinding(html) {
  $("aiFinding").hidden = !html;
  $("aiFinding").innerHTML = html || "";
}
function startRehearsal() {
  endTour(false);
  clearScenario(true);
  playing = false;
  Object.assign(ai, { on: true, t: 0, next: 0, holding: 0 });
  setTwin(true);
  setT(0); syncPlay();
  aiStep(0); aiFinding("");
  flyTo("overview");
  $("aiRun").textContent = "結束預演";
}
function stopRehearsal(toStart) {
  if (!ai.on) return;
  ai.on = false;
  setTwin(false);
  $("pin").hidden = true;
  aiStep(-1); aiFinding("");
  $("aiRun").textContent = "開始預演";
  if (toStart) { setT(0); syncPlay(); }
}
function updateRehearsal() {
  if (!ai.on) return;
  ai.t += dtFrame;
  if (ai.t < AI_FLOW.intro) return;
  if (ai.t < AI_FLOW.intro * 2) { aiStep(1); return; }
  if (ai.holding > 0) {
    ai.holding -= dtFrame;
    if (ai.holding <= 0) { $("pin").hidden = true; aiFinding(""); aiStep(2); }
    return;
  }
  if (T >= D.meta.T) {
    if (ai.step !== 4) {
      aiStep(4);
      aiFinding(`<b>驗證通過</b>抓到並修正 ${AI_CONFLICTS.length} 個問題，腳本放行。`);
      $("aiRun").textContent = "進入實際施工";
    }
    return;
  }
  aiStep(2);
  const c = AI_CONFLICTS[ai.next];
  const nextT = T + dtFrame * AI_FLOW.rate;
  if (c && nextT >= c.T) {
    setT(c.T);
    ai.next++;
    ai.holding = AI_FLOW.hold;
    aiStep(3);
    pinWorld.copy(B(c.pin[0], c.pin[1], c.pin[2]));
    $("pin").hidden = false;
    $("pin").textContent = c.text;
    aiFinding(`<b>${c.text}</b>${c.fix}`);
    return;
  }
  setT(nextT);
}

let fx = { rain: null, level: 0, name: "day", quake: null };
function buildRain() {
  const N = 2600, pos = new Float32Array(N * 6);
  for (let i = 0; i < N; i++) {
    const x = (Math.random() - .5) * 150, y = Math.random() * 90, z = (Math.random() - .5) * 150;
    pos.set([x, y, z, x, y - 1.2, z], i * 6);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  const m = new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0xc8d6e0, transparent: true, opacity: .34 }));
  m.visible = false; m.frustumCulled = false;
  scene.add(m);
  fx.rain = m;
}
function setWeather(name) {
  fx.name = name;
  const key = name === "storm" || name === "rain" ? "storm" : name === "night" ? "night" : "day";
  const s = skyOf(key);
  scene.background = s.bg; scene.environment = s.env;
  scene.environmentIntensity = key === "day" ? .72 : key === "storm" ? .5 : .14;
  sun.intensity = key === "day" ? 2.6 : key === "storm" ? .5 : .08;
  hemi.intensity = key === "day" ? .55 : key === "storm" ? .5 : .1;
  scene.fog.color.set(key === "day" ? 0xcdd9df : key === "storm" ? 0x7f8a90 : 0x0c1220);
  scene.fog.near = key === "day" ? 150 : 90;
  fx.rain.visible = name === "storm" || name === "rain";
  lampMats.forEach((m) => (m.emissiveIntensity = key === "night" ? 2.4 : .2));
  A.nightLights.forEach((l) => (l.visible = key === "night"));
  shadowDirty = true;
}

function runScenario(sc) {
  endTour(false);
  stopRehearsal(false);
  clearScenario(false);
  currentScenario = sc;
  playing = false;
  setT(sc.T); syncPlay();
  override.park = !!sc.park;
  override.netRoll = sc.netRoll ? 1 : 0;
  override.roof = sc.roof ?? null;
  setWeather(sc.fx === "storm" ? "storm" : sc.fx === "rain" ? "rain" : sc.fx === "night" ? "night" : "day");
  flyTo(sc.cam);
  document.querySelectorAll("#scens button[data-id]").forEach((b) => b.classList.toggle("on", b.dataset.id === sc.id));
  const box = $("scenDetail");
  box.hidden = false;
  box.innerHTML = `<h3>${sc.name}</h3><ol>${sc.steps.map((s) => `<li>${s}</li>`).join("")}</ol>` +
    (sc.actions ? `<div class="row">${sc.actions.map(([n, id]) => `<button class="btn" data-q="${id}">${n}</button>`).join("")}</div><p id="quakeRead" class="fine"></p>` : "") +
    `<button class="btn ghost" id="scenExit">結束情境</button>`;
  box.querySelector("#scenExit").onclick = () => clearScenario(true);
  box.querySelectorAll("[data-q]").forEach((b) => (b.onclick = () => startQuake(b.dataset.q)));
  if (sc.pin) {
    const p = B(sc.pin[0], sc.pin[1], sc.pinFloor ? workZ() + .4 : sc.pin[2]);
    pinWorld.copy(p);
    $("pin").hidden = false;
    $("pin").textContent = sc.pinText;
  }
  if (sc.actions) setTimeout(() => { if (currentScenario === sc) startQuake("with"); }, 1400);
}
const pinWorld = new THREE.Vector3();
function clearScenario(reset) {
  currentScenario = null;
  override = { park: false, netRoll: 0, roof: null };
  fx.quake = null; U.uQuake.value = 0;
  $("pin").hidden = true;
  if (reset) {
    $("scenDetail").hidden = true;
    setWeather("day");
    document.querySelectorAll("#scens button[data-id]").forEach((b) => b.classList.remove("on"));
  }
}
function startQuake(mode) { fx.quake = { mode, t0: simTime }; }
function updateQuake() {
  if (!fx.quake) return;
  const t = simTime - fx.quake.t0;
  const with_ = fx.quake.mode === "with";
  const zeta = with_ ? .16 : .018, w = 4.2;
  const force = t < 2.2 ? Math.sin(t * 7) * .6 * Math.min(t / .4, 1) : 0;
  const a = (t < 2.2 ? 1 : Math.exp(-zeta * w * (t - 2.2))) * 1.1;
  const amp = force + a * Math.sin(w * t);
  U.uQuake.value = amp * Math.min(t / .3, 1);
  shadowDirty = true;
  const r = $("quakeRead");
  if (r) r.textContent = `${with_ ? "有阻尼器" : "沒有阻尼器"}：頂層位移 ${(Math.abs(U.uQuake.value) * 10).toFixed(0)} 公分（動畫放大示意）`;
  if (t > 16) { fx.quake = null; U.uQuake.value = 0; }
}

function resize() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  if (!w || !h) return;
  renderer.setPixelRatio(pixelRatio);
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
function syncPlay() {
  $("play").textContent = playing ? "暫停" : T >= D.meta.T ? "重播" : "播放";
  $("play").setAttribute("aria-pressed", playing);
}

function buildUI() {
  const bar = $("segs");
  D.phases.forEach((p, i) => {
    const b = document.createElement("button");
    b.className = "seg"; b.dataset.id = p.id;
    b.style.width = `${(p.t1 - p.t0) / D.meta.T * 100}%`;
    b.title = p.name;
    b.setAttribute("aria-label", `跳到${p.name}`);
    b.innerHTML = `<span>${p.t1 - p.t0 >= 30 ? p.name : ""}</span>`;
    b.onclick = () => { endTour(false); clearScenario(true); setT(p.t0 + .01); };
    bar.append(b);
  });
  $("scrub").max = D.meta.T;
  $("scrub").oninput = (e) => { endTour(false); setT(+e.target.value); syncPlay(); };
  $("play").onclick = () => {
    $("intro").hidden = true;
    stopRehearsal(false);
    if (T >= D.meta.T) setT(0);
    playing = !playing;
    if (playing && currentScenario) clearScenario(true);
    if (playing && !tour.on && guide && T < .5 && !matchMedia("(prefers-reduced-motion: reduce)").matches) startTour();
    syncPlay();
  };
  document.querySelectorAll("#speed button").forEach((b) => (b.onclick = () => {
    speed = +b.dataset.s;
    document.querySelectorAll("#speed button").forEach((o) => o.classList.toggle("on", o === b));
  }));
  const counts = { items: Object.values(D.items).reduce((a, v) => a + v.length, 0), tasks: Object.values(D.tasks).reduce((a, v) => a + v.length, 0), bots: D.bots.length, days: D.meta.T };
  $("aiSteps").innerHTML = AI_STEPS.map(([a, b]) => `<li><b>${a}</b><span>${b.replace(/\{(\w+)\}/g, (_, k) => counts[k].toLocaleString())}</span></li>`).join("");
  $("aiRun").onclick = () => {
    if (!ai.on) { startRehearsal(); return; }
    const verified = T >= D.meta.T;
    stopRehearsal(true);
    if (verified) $("play").click();
  };
  $("cams").innerHTML = CAMERAS.map(([id, n]) => `<button data-id="${id}">${n}</button>`).join("");
  document.querySelectorAll("#cams button").forEach((b) => (b.onclick = () => { endTour(false); flyTo(b.dataset.id); }));
  $("guide").onchange = (e) => { guide = e.target.checked; if (!guide) endTour(false); };
  $("tourSkip").onclick = () => endTour(true);
  PLANT_PINS.forEach((p) => {
    const el = document.createElement("div");
    el.className = "tpin"; el.hidden = true;
    el.innerHTML = `<b>${p.title}</b>${p.text}`;
    $("tpins").append(el); tpinEls.push(el);
  });
  $("layers").innerHTML = LAYERS.map(([k, n]) => `<label class="chip"><input type="checkbox" id="ly-${k}" checked data-k="${k}"><span>${n}</span></label>`).join("");
  $("layers").onchange = (e) => {
    layerState[e.target.dataset.k] = e.target.checked;
    applyLayers(); setT(T);
  };
  $("cut").oninput = (e) => {
    const v = +e.target.value;
    clipPlane.constant = v >= 100 ? 200 : lerp(-13, 13, v / 100);
    patched.forEach((m) => { m.side = v >= 100 && m.name !== "net" ? THREE.FrontSide : THREE.DoubleSide; m.needsUpdate = true; });
    $("cutVal").textContent = v >= 100 ? "關閉" : `${Math.round(100 - v)}%`;
  };
  $("scens").innerHTML = SCENARIOS.map((s) => `<button data-id="${s.id}">${s.name}</button>`).join("");
  document.querySelectorAll("#scens button").forEach((b) => (b.onclick = () => runScenario(SCENARIOS.find((s) => s.id === b.dataset.id))));
  document.querySelectorAll("[data-tab]").forEach((b) => (b.onclick = () => {
    const open = b.dataset.tab;
    document.querySelectorAll("[data-tab]").forEach((o) => o.classList.toggle("on", o === b));
    document.querySelectorAll(".pane").forEach((p) => (p.hidden = p.id !== `pane-${open}`));
    $("side").classList.add("open");
  }));
  $("sideToggle").onclick = () => $("side").classList.toggle("open");
  addEventListener("keydown", (e) => {
    if ($("vd").open) return;
    if (["INPUT", "SELECT"].includes(e.target.tagName) && e.target.type !== "range") return;
    if (e.code === "Space" && e.target.closest?.("#intro, #introOpen")) return;
    if (e.code === "Space") { e.preventDefault(); $("play").click(); }
    if (e.code === "ArrowRight") { endTour(false); setT(T + (e.shiftKey ? 2 : 1)); e.preventDefault(); }
    if (e.code === "ArrowLeft") { endTour(false); setT(T - (e.shiftKey ? 2 : 1)); e.preventDefault(); }
  });
  let down = null;
  canvas.addEventListener("pointerdown", (e) => { down = [e.clientX, e.clientY]; endTour(false); guide = false; $("guide").checked = false; camTween.active = false; });
  canvas.addEventListener("pointerup", (e) => { if (down && Math.hypot(e.clientX - down[0], e.clientY - down[1]) < 5) pick(e); });
  $("infoClose").onclick = () => ($("info").hidden = true);
  setupIntro();
  new ResizeObserver(resize).observe(canvas);
}

function setupIntro() {
  const key = "tianjia-intro-seen", d = $("vd"), v = $("vdVideo"), url = new URL("intro.mp4", document.baseURI).href;
  const dismiss = () => {
    $("intro").hidden = true;
    try { localStorage.setItem(key, "1"); } catch {}
  };
  let seen = false;
  try { seen = !!localStorage.getItem(key); } catch {}
  $("intro").hidden = seen;

  const say = (msg) => { $("vdMsg").textContent = msg; $("vdMsg").hidden = !msg; };
  const label = (title, lead) => { $("vdTitle").textContent = title; $("vdLead").textContent = lead; };
  const title0 = $("vdTitle").textContent, lead0 = $("vdLead").textContent;

  // 伺服器不支援分段讀取時，Chrome 不能拖進度、Safari 甚至不肯播，改用整檔載入後的本機網址
  let rangeOK = null, started = false, blobTried = false, resumeAt = 0;
  const probe = new AbortController();
  fetch(url, { headers: { Range: "bytes=0-0" }, signal: probe.signal })
    .then((r) => { rangeOK = r.status === 206; if (!rangeOK) probe.abort(); })
    .catch(() => {});
  const fail = () => say("影片載入失敗，請重新整理後再試一次。");
  const resume = () => {
    v.currentTime = resumeAt;
    say("");
    if (d.open) v.play().catch(() => {});
  };
  const loadBlob = async () => {
    blobTried = true;
    resumeAt = v.currentTime;
    say("影片載入中，請稍候…");
    try {
      const r = await fetch(url);
      if (!r.ok) throw new Error(r.status);
      v.src = URL.createObjectURL(await r.blob());
      resume();
    } catch { fail(); }
  };
  const open = () => {
    dismiss();
    d.showModal();
    v.focus();
    if (!started) {
      started = true;
      if (rangeOK === false) { loadBlob(); return; }
      v.src = url;
    }
    v.play().catch(() => {});
  };
  v.onerror = () => {
    if (v.src.startsWith("blob:")) { v.src = url; resume(); }
    else if (blobTried) fail();
    else loadBlob();
  };
  v.onplay = () => label(title0, lead0);
  v.onended = () => {
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
    if (v.webkitDisplayingFullscreen) v.webkitExitFullscreen();
    label("看完了，換你操作", "按下面的按鈕從開工看起，也可以拖曳視角、試情境演練，或跑一次 AI 預演。");
    $("vdGo").focus();
  };
  $("introOpen").onclick = $("introThumb").onclick = $("introPlay").onclick = open;
  $("introClose").onclick = dismiss;
  $("vdClose").onclick = () => d.close();
  $("vdGo").onclick = () => { d.close(); if (!playing) $("play").click(); };
  d.onclick = (e) => { if (e.target === d) d.close(); };
  d.onclose = () => v.pause();
}

const ray = new THREE.Raycaster(), ptr = new THREE.Vector2();
function pick(e) {
  const r = canvas.getBoundingClientRect();
  ptr.set((e.clientX - r.left) / r.width * 2 - 1, -(e.clientY - r.top) / r.height * 2 + 1);
  ray.setFromCamera(ptr, camera);
  const near = new THREE.Vector3();
  const list = pickables.filter((m) => m.visible);
  const hits = ray.intersectObjects([...list, A.rig, A.rigB, ...Object.values(A.pool).flat().filter((o) => o.visible)], true);
  for (const h of hits) {
    const part = h.object.userData.part;
    if (!part) continue;
    if (h.instanceId != null) {
      const r2 = h.object.userData.rows[h.instanceId];
      if (T < r2[7] || T > r2[9]) continue;
    }
    const info = D.parts[part];
    if (!info || ["ground", "road", "net_x", "net_y", "roof_panel"].includes(part)) { if (part === "ground" || part === "road") break; continue; }
    if (clipPlane.constant < 100 && clipPlane.distanceToPoint(h.point) < 0 && info.layer !== "rig") continue;
    $("infoName").textContent = info.zh;
    $("infoNote").textContent = info.note;
    $("info").hidden = false;
    return;
  }
}

let guide = true, guideCam = "overview", guidePhase = null;
const GUIDE = { prefab: "overview", survey: "street", dwall: "overview", piles: "overview", excavate: "pit", rig: "overview", raft: "pit", basement: "pit", tower: "deck", envelope: "rig", descend: "overview", interior: "overview", landscape: "overview" };
function updateGuide() {
  if (!guide || !playing || tour.on) return;
  const id = lastPhase?.id;
  if (id !== guidePhase) { guidePhase = id; guideCam = GUIDE[id]; flyTo(guideCam); }
  else if (!camTween.active && (guideCam === "deck")) {
    const [p, q] = camSpec("deck");
    camera.position.y += (p[1] - camera.position.y) * .02;
    controls.target.y += (q[1] - controls.target.y) * .02;
  }
}

// 開場導覽：從工地飛到工廠說明用途，再跟著運輸車回到工地，然後才開始施工
const TOUR_T = [3.4, 9, 15.5, 18];
const tour = { on: false, t: 0, clock: 0, stage: -1, p0: new THREE.Vector3(), q0: new THREE.Vector3(), p: new THREE.Vector3(), q: new THREE.Vector3() };
const tmpA = new THREE.Vector3(), tmpB = new THREE.Vector3();
function plantView(k) {
  const [px, py] = D.meta.plant;
  tmpA.set(px - 26 + 12 * k, 33 - 6 * k, -py - 68 + 8 * k);
  tmpB.set(px + 8, 3, -py - 8);
}
function tourCaption(i) {
  if (tour.stage === i) return;
  tour.stage = i;
  $("tour").hidden = false;
  $("tourT").textContent = TOUR[i][0];
  $("tourD").textContent = TOUR[i][1];
}
function startTour() {
  Object.assign(tour, { on: true, t: 0, clock: 0, stage: -1 });
  truckOff = 0;
  camTween.active = false;
  tour.p0.copy(camera.position); tour.q0.copy(controls.target);
  document.querySelectorAll("#cams button").forEach((b) => b.classList.remove("on"));
}
function endTour(toOverview) {
  if (!tour.on) return;
  tour.on = false;
  truckOff = tour.clock - T;
  $("tour").hidden = true;
  if (toOverview) flyTo("overview");
}
const tourTruck = { x: 0, y: 0 };
function updateTour() {
  if (!tour.on || !playing) return;
  tour.t += dtFrame;
  const t = tour.t, [t0, t1, t2, t3] = TOUR_T;
  setT(Math.min(t / t3 * 2, 2));
  if (t < t0) {
    tourCaption(0);
    const k = ease(t / t0);
    plantView(0);
    camera.position.lerpVectors(tour.p0, tmpA, k); camera.position.y += Math.sin(k * Math.PI) * 24;
    controls.target.lerpVectors(tour.q0, tmpB, k);
  } else if (t < t1) {
    tourCaption(1);
    plantView((t - t0) / (t1 - t0));
    camera.position.copy(tmpA); controls.target.copy(tmpB);
  } else if (t < t2) {
    tourCaption(2);
    tour.clock = (t - t1) / (t2 - t1) * .46 * TRUCK.days;
    const q = truckPose(tour.clock / TRUCK.days, tourTruck), ox = q.x, oz = -q.y, c = Math.cos(q.rz), s = Math.sin(q.rz);
    // 車還在廠區時鏡頭留在屋頂之外，上了路才跟車
    const [px] = D.meta.plant, inYard = ox > px - 6;
    if (inYard) tmpA.set(px - 34, 30, 2);
    else tmpA.set(ox - c * 26 + s * 12, 12, oz + s * 26 + c * 12);
    tmpB.set(ox + c * 10, 2, oz - s * 10);
    const k = 1 - Math.exp(-dtFrame * (inYard ? 1.6 : 2.6));
    camera.position.lerp(tmpA, k); controls.target.lerp(tmpB, k);
  } else if (t < t3) {
    if (tour.stage !== 3) { tour.p0.copy(camera.position); tour.q0.copy(controls.target); }
    tourCaption(3);
    const k = ease((t - t2) / (t3 - t2)), [p, q] = camSpec("overview");
    tmpA.set(...p); tmpB.set(...q);
    camera.position.lerpVectors(tour.p0, tmpA, k); controls.target.lerpVectors(tour.q0, tmpB, k);
  } else endTour(false);
  camera.fov = lerp(camera.fov, 42, 1 - Math.exp(-dtFrame * 3)); camera.updateProjectionMatrix();
}
const tpinEls = [];
function updateTourPins() {
  const near = (tour.on && tour.stage === 1) || (!tour.on && currentCam === "factory" && !camTween.active);
  const [px, py] = D.meta.plant;
  tpinEls.forEach((el, i) => {
    el.hidden = !near;
    if (!near) return;
    const a = PLANT_PINS[i].at, v = B(px + a[0], py + a[1], a[2], tmpA).project(camera);
    const x = (v.x + 1) / 2 * canvas.clientWidth, y = (1 - v.y) / 2 * canvas.clientHeight;
    el.style.left = `${clamp(x, 90, canvas.clientWidth - 90)}px`; el.style.top = `${y}px`;
    el.hidden = v.z > 1;
  });
}

const clock = new THREE.Clock();
let fpsAcc = 0, fpsN = 0, ledTick = 1;
function frame() {
  requestAnimationFrame(frame);
  dtFrame = Math.min(clock.getDelta(), .1);
  if ($("vd").open) return; // 看影片時模擬暫停，也把顯卡讓給影片
  simTime += dtFrame;
  if (playing && !tour.on) {
    setT(T + dtFrame * speed);
    if (T >= D.meta.T) { playing = false; syncPlay(); }
  }
  updateActors(T);
  updateAmbient();
  updateQuake();
  updateRehearsal();
  updateTour();
  updateGuide();
  if (camTween.active) {
    camTween.t += dtFrame / camTween.dur;
    const k = ease(Math.min(camTween.t, 1));
    camera.position.lerpVectors(camTween.p0, camTween.p1, k);
    controls.target.lerpVectors(camTween.q0, camTween.q1, k);
    camera.fov = lerp(camTween.f0, camTween.f1, k);
    camera.updateProjectionMatrix();
    if (camTween.t >= 1) camTween.active = false;
  }
  controls.update();
  if (fx.rain.visible) {
    fx.rain.position.y = -((simTime * (fx.name === "storm" ? 70 : 50)) % 40);
    fx.rain.rotation.z = fx.name === "storm" ? .3 : .05;
  }
  updateTourPins();
  if (!$("pin").hidden) {
    const v = pinWorld.clone().project(camera);
    const pin = $("pin");
    pin.style.left = `${(v.x + 1) / 2 * canvas.clientWidth}px`;
    pin.style.top = `${(1 - v.y) / 2 * canvas.clientHeight}px`;
  }
  if (shadowDirty && ++shadowTick >= (playing ? 5 : 1)) { sun.shadow.needsUpdate = true; shadowDirty = false; shadowTick = 0; }
  if ((ledTick += dtFrame) > .5) { ledTick = 0; drawLED(T); }
  renderer.render(scene, camera);
  fpsAcc += dtFrame; fpsN++;
  if (fpsAcc > 3) {
    if (fpsN / fpsAcc < 22 && pixelRatio > 1) { pixelRatio = 1; resize(); }
    fpsAcc = 0; fpsN = 0;
  }
}

async function main() {
  const prog = $("loadBar");
  try {
    renderer.getContext();
    const [sched, gltf] = await Promise.all([
      fetch(new URL("schedule.json", document.baseURI)).then((r) => r.json()),
      new Promise((ok, no) => {
        const loader = new GLTFLoader();
        loader.register((p) => { p.textureLoader = new THREE.TextureLoader(p.options.manager); return { name: "plain_texture_loader" }; });
        fetch(new URL("parts.glb.txt", document.baseURI)).then((r) => r.text()).then((b64) => { prog.style.width = "70%"; loader.parse(Uint8Array.from(atob(b64), (c) => c.charCodeAt(0)).buffer, "", ok, no); }).catch(no);
      }),
    ]);
    D = sched;
    U.uH.value = 44;
    loadLibrary(gltf);
    buildItems();
    buildActors();
    A.nightLights = [];
    for (const [x, z] of [[-22, 22], [22, 22], [22, -22], [-22, -22]]) {
      const l = new THREE.PointLight(0xffd9a0, 900, 90, 1.7);
      l.position.set(x, 26, z); l.visible = false;
      scene.add(l); A.nightLights.push(l);
    }
    buildRain();
    buildUI();
    applyLayers();
    setWeather("day");
    resize();
    { const [p, q] = camSpec("overview"); camera.position.set(...p); controls.target.set(...q); }
    setT(+(new URLSearchParams(location.search).get("t") ?? 0));
    syncPlay();
    $("loading").hidden = true;
    window.__sim = { look: (p, q) => { camTween.active = false; camera.position.set(...p); controls.target.set(...q); }, setT, flyTo, snap: (id) => { const [p, q, f] = camSpec(id); camTween.active = false; camera.position.set(...p); controls.target.set(...q); camera.fov = f; camera.updateProjectionMatrix(); }, runScenario, get T() { return T; }, A, D, scene, camera, renderer, SCENARIOS, setTwin, tour, truckPose, setGuide: (v) => (guide = v) };
    frame();
  } catch (err) {
    console.error(err);
    $("loadMsg").textContent = `載入失敗：${err.message}。請確認瀏覽器已啟用 WebGL，再重新整理。`;
  }
}
main();
