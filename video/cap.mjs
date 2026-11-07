// 逐幀錄製：虛擬時鐘接管頁面，每幀由 shots.js 決定 T、鏡頭與情境。
// node cap.mjs --web <dir> --out <dir> [--only a,b] [--stride 30] [--res 360x640] [--final]
import { chromium } from "playwright-core";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";

const arg = (k, d) => { const i = process.argv.indexOf(`--${k}`); return i < 0 ? d : process.argv[i + 1] ?? true; };
const WEB = arg("web"), OUT = arg("out"), FINAL = process.argv.includes("--final");
const ONLY = arg("only", "") ? arg("only").split(",") : null;
const STRIDE = +arg("stride", FINAL ? 1 : 30);
const [W, H] = arg("res", FINAL ? "1080x1920" : "360x640").split("x").map(Number);
const PR = +arg("pr", FINAL ? 1.5 : 1), FPS = 30;
fs.mkdirSync(OUT, { recursive: true });

const MIME = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".json": "application/json", ".txt": "text/plain; charset=utf-8" };
let sink = null;
const server = http.createServer((req, res) => {
  const url = new URL(req.url, "http://x");
  if (req.method === "POST" && url.pathname === "/frame") {
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", async () => {
      const buf = Buffer.concat(chunks);
      if (sink) { if (!sink.write(buf)) await new Promise((r) => sink.once("drain", r)); }
      else fs.writeFileSync(path.join(OUT, `${url.searchParams.get("shot")}_${url.searchParams.get("i").padStart(5, "0")}.jpg`), buf);
      res.writeHead(204).end();
    });
    return;
  }
  const file = url.pathname === "/shots.js" ? path.join(import.meta.dirname, "shots.js") : path.join(WEB, url.pathname === "/" ? "index.html" : url.pathname);
  fs.readFile(file, (e, b) => {
    if (e) return res.writeHead(404).end();
    res.writeHead(200, { "content-type": MIME[path.extname(file)] || "application/octet-stream" }).end(b);
  });
});
await new Promise((r) => server.listen(8799, r));

const browser = await chromium.launch({
  channel: "chrome", headless: true,
  args: ["--use-angle=d3d11", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--enable-webgl", "--disable-background-timer-throttling", "--disable-renderer-backgrounding", "--disable-backgrounding-occluded-windows"],
});
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
page.on("console", (m) => { if (m.type() === "error") console.log("[page]", m.text()); });
page.on("pageerror", (e) => console.log("[pageerror]", e.message));

await page.addInitScript(() => {
  let now = 0;
  const q = [];
  performance.now = () => now;
  window.requestAnimationFrame = (cb) => { q.push(cb); return q.length; };
  const timers = [];
  window.__useVirtualTimers = () => { window.setTimeout = (cb, ms) => { timers.push([now + ms, cb]); return timers.length; }; };
  window.__step = (ms) => {
    now += ms;
    for (let i = timers.length - 1; i >= 0; i--) if (timers[i][0] <= now) timers.splice(i, 1)[0][1]();
    q.splice(0).forEach((cb) => cb(now));
  };
});
await page.goto("http://localhost:8799/");
await page.waitForFunction(() => window.__sim, null, { timeout: 120000 });
const info = await page.evaluate(({ W, H, PR }) => {
  const s = window.__sim, gl = s.renderer.getContext();
  const dbg = gl.getExtension("WEBGL_debug_renderer_info");
  const c = s.renderer.domElement;
  Object.assign(c.style, { position: "fixed", inset: 0, width: `${W}px`, height: `${H}px`, zIndex: 99999 });
  window.__useVirtualTimers();
  s.renderer.setPixelRatio(PR);
  s.renderer.setSize(W, H, false);
  s.camera.aspect = W / H;
  s.scene.traverse((o) => {
    if (o.isDirectionalLight && o.castShadow) { o.shadow.mapSize.set(4096, 4096); o.shadow.map?.dispose(); o.shadow.map = null; o.shadow.bias = -.00012; }
  });
  s.setGuide(false);
  window.__rig = { p: new s.camera.position.constructor(), t: new s.camera.position.constructor(), fov: 38, active: false, post: null };
  const r = s.renderer.render.bind(s.renderer);
  s.renderer.render = (scene, cam) => {
    const k = window.__rig;
    if (k.active) {
      cam.position.copy(k.p); cam.fov = k.fov; cam.aspect = W / H; cam.updateProjectionMatrix(); cam.lookAt(k.t);
      k.post?.();
    }
    r(scene, cam);
  };
  return { renderer: gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL), size: [c.width, c.height] };
}, { W, H, PR });
console.log(JSON.stringify(info));
await page.addScriptTag({ url: "/shots.js" });

const EVALFILE = arg("eval", "");
if (EVALFILE) { console.log(JSON.stringify(await page.evaluate(fs.readFileSync(EVALFILE, "utf8")))); await browser.close(); server.close(); process.exit(0); }
const shots = await page.evaluate(() => window.__SHOTS.map((s) => ({ id: s.id, dur: s.dur })));
const wanted = shots.filter((s) => !ONLY || ONLY.includes(s.id));
const total = wanted.reduce((a, s) => a + Math.round(s.dur * FPS), 0);
console.log(`shots ${wanted.length}, frames ${total}, stride ${STRIDE}`);
const t00 = Date.now();

for (const s of wanted) {
  let ff = null;
  if (FINAL) {
    ff = spawn("ffmpeg", ["-y", "-hide_banner", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(FPS), "-c:v", "mjpeg", "-i", "-",
      "-vf", `scale=${W}:${H}:flags=lanczos`, "-c:v", "h264_nvenc", "-preset", "p6", "-rc", "vbr", "-cq", "16", "-b:v", "0", "-pix_fmt", "yuv420p", path.join(OUT, `${s.id}.mp4`)], { stdio: ["pipe", "inherit", "inherit"] });
    sink = ff.stdin;
  }
  await page.evaluate((id) => window.__beginShot(id), s.id);
  const N = Math.round(s.dur * FPS);
  for (let i = 0; i < N; i += STRIDE) {
    await page.evaluate(({ id, i, N, STRIDE, FPS }) => window.__renderFrame(id, i, N, STRIDE, FPS), { id: s.id, i, N, STRIDE, FPS });
    if (i % 90 === 0) console.log(`${s.id} ${i}/${N} ${((Date.now() - t00) / 1000).toFixed(0)}s`);
  }
  if (ff) { sink = null; ff.stdin.end(); await new Promise((r) => ff.on("close", r)); }
}
await browser.close();
server.close();
console.log("done", ((Date.now() - t00) / 1000).toFixed(0), "s");
