#!/usr/bin/env node
// /generate runner: routes an image/video job to the cheapest configured provider
// (kie.ai, fal.ai, WaveSpeed), enforces a budget, downloads outputs and logs every prompt.
// No dependencies; needs Node 18+ (global fetch).
//
//   node .claude/skills/generate/scripts/generate.mjs --model nano-banana --prompt "..." [options]
//   node .claude/skills/generate/scripts/generate.mjs --list
//   node .claude/skills/generate/scripts/generate.mjs --spent [--session name]

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SKILL_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const ROOT = process.cwd();
const CATALOG = JSON.parse(fs.readFileSync(path.join(SKILL_DIR, "models.json"), "utf8")).models;
const ORDER = ["kie", "fal", "wavespeed"];
const KEY_VARS = { kie: "KIE_API_KEY", fal: "FAL_KEY", wavespeed: "WAVESPEED_API_KEY" };

// ---------- args ----------
function parseArgs(argv) {
  const a = { ref: [], param: [], count: 1 };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    const v = () => argv[++i];
    switch (k) {
      case "--model": a.model = v(); break;
      case "--prompt": a.prompt = v(); break;
      case "--prompt-file": a.prompt = fs.readFileSync(v(), "utf8").trim(); break;
      case "--provider": a.provider = v(); break;
      case "--ref": a.ref.push(v()); break;
      case "--aspect": a.aspect = v(); break;
      case "--resolution": a.resolution = v(); break;
      case "--duration": a.duration = v(); break;
      case "--count": a.count = Number(v()); break;
      case "--param": a.param.push(v()); break;
      case "--budget": a.budget = Number(v()); break;
      case "--session": a.session = v(); break;
      case "--name": a.name = v(); break;
      case "--out": a.out = v(); break;
      case "--dry-run": a.dryRun = true; break;
      case "--yes": a.yes = true; break;
      case "--list": a.list = true; break;
      case "--spent": a.spent = true; break;
      default: throw new Error(`Unknown argument: ${k}`);
    }
  }
  return a;
}

// ---------- env ----------
function loadEnv() {
  for (const f of [".env.local", ".env"]) {
    const p = path.join(ROOT, f);
    if (!fs.existsSync(p)) continue;
    for (const line of fs.readFileSync(p, "utf8").split("\n")) {
      const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
      if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^["']|["']$/g, "");
    }
  }
}
const hasKey = (p) => Boolean(process.env[KEY_VARS[p]]);

// ---------- log / budget ----------
const outDir = (a) => path.resolve(ROOT, a.out || "generations");
const logPath = (a) => path.join(outDir(a), "log.jsonl");

function readLog(a) {
  if (!fs.existsSync(logPath(a))) return [];
  return fs.readFileSync(logPath(a), "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l));
}
function spent(a) {
  return readLog(a)
    .filter((e) => e.status === "ok" && (!a.session || e.session === a.session))
    .reduce((s, e) => s + (e.est_usd || 0), 0);
}
function appendLog(a, entry) {
  fs.mkdirSync(outDir(a), { recursive: true });
  fs.appendFileSync(logPath(a), JSON.stringify(entry) + "\n");
}

// ---------- routing ----------
function priceFor(cfg, a) {
  return (a.resolution && cfg.est_usd_by_resolution?.[a.resolution]) ?? cfg.est_usd;
}
function route(model, a) {
  const entries = Object.entries(model.providers);
  if (a.provider && a.provider !== "auto") {
    const cfg = model.providers[a.provider];
    if (!cfg) throw new Error(`Model ${a.model} is not configured for provider ${a.provider}`);
    return [[a.provider, cfg]];
  }
  return entries
    .filter(([p]) => hasKey(p))
    .sort(([pa, ca], [pb, cb]) => priceFor(ca, a) - priceFor(cb, a) || ORDER.indexOf(pa) - ORDER.indexOf(pb));
}

// ---------- refs ----------
function refToUrl(ref, provider) {
  if (/^https?:\/\//.test(ref)) return ref;
  const p = path.resolve(ROOT, ref);
  if (!fs.existsSync(p)) throw new Error(`Reference not found: ${ref}`);
  if (provider === "kie") {
    // kie.ai only takes hosted URLs; skip it so routing falls through to fal/wavespeed.
    throw Object.assign(new Error("kie.ai needs public URLs for references, local file given"), { skip: true });
  }
  const ext = path.extname(p).slice(1).toLowerCase().replace("jpg", "jpeg");
  return `data:image/${ext};base64,${fs.readFileSync(p).toString("base64")}`;
}

function buildInput(provider, cfg, model, a) {
  const input = { prompt: a.prompt };
  if (a.aspect) input.aspect_ratio = a.aspect;
  if (a.resolution) input.resolution = a.resolution;
  if (a.duration) input.duration = model.type === "video" && provider === "fal" ? String(a.duration) : Number(a.duration);
  if (a.count > 1 && model.type === "image") input[provider === "kie" ? "n" : "num_images"] = a.count;
  if (a.ref.length) {
    const urls = a.ref.map((r) => refToUrl(r, provider));
    input[cfg.ref_field] = cfg.ref_single ? urls[0] : urls;
  }
  for (const kv of a.param) {
    const i = kv.indexOf("=");
    const raw = kv.slice(i + 1);
    let val = raw;
    try { val = JSON.parse(raw); } catch { /* keep string */ }
    input[kv.slice(0, i)] = val;
  }
  return input;
}

// ---------- providers ----------
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function http(url, opts = {}) {
  const res = await fetch(url, opts);
  const text = await res.text();
  let body;
  try { body = JSON.parse(text); } catch { body = text; }
  if (!res.ok) throw new Error(`${opts.method || "GET"} ${url} -> ${res.status}: ${text.slice(0, 500)}`);
  return body;
}
async function poll(fn, { every = 3000, timeout = 15 * 60 * 1000 } = {}) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    const r = await fn();
    if (r) return r;
    await sleep(every);
  }
  throw new Error("Timed out waiting for result");
}

const PROVIDERS = {
  async fal(modelId, input) {
    const headers = { Authorization: `Key ${process.env.FAL_KEY}`, "Content-Type": "application/json" };
    const sub = await http(`https://queue.fal.run/${modelId}`, { method: "POST", headers, body: JSON.stringify(input) });
    const done = await poll(async () => {
      const s = await http(sub.status_url, { headers });
      if (s.status === "COMPLETED") return s;
      if (s.status === "FAILED" || s.error) throw new Error(`fal job failed: ${JSON.stringify(s).slice(0, 500)}`);
    });
    const out = await http(sub.response_url, { headers });
    const urls = [...(out.images || []).map((i) => i.url), ...(out.video ? [out.video.url] : [])];
    return { id: sub.request_id, urls, raw: done };
  },

  async kie(modelId, input) {
    const headers = { Authorization: `Bearer ${process.env.KIE_API_KEY}`, "Content-Type": "application/json" };
    const sub = await http("https://api.kie.ai/api/v1/jobs/createTask", {
      method: "POST", headers, body: JSON.stringify({ model: modelId, input }),
    });
    if (sub.code !== 200 || !sub.data?.taskId) throw new Error(`kie createTask failed: ${JSON.stringify(sub).slice(0, 500)}`);
    const taskId = sub.data.taskId;
    const rec = await poll(async () => {
      const r = await http(`https://api.kie.ai/api/v1/jobs/recordInfo?taskId=${taskId}`, { headers });
      const st = r.data?.state;
      if (st === "success") return r.data;
      if (st === "fail") throw new Error(`kie job failed: ${r.data?.failMsg || JSON.stringify(r).slice(0, 500)}`);
    });
    const result = typeof rec.resultJson === "string" ? JSON.parse(rec.resultJson) : rec.resultJson;
    return { id: taskId, urls: result?.resultUrls || [] };
  },

  async wavespeed(modelId, input) {
    const headers = { Authorization: `Bearer ${process.env.WAVESPEED_API_KEY}`, "Content-Type": "application/json" };
    const sub = await http(`https://api.wavespeed.ai/api/v3/${modelId}`, { method: "POST", headers, body: JSON.stringify(input) });
    const id = sub.data?.id;
    if (!id) throw new Error(`wavespeed submit failed: ${JSON.stringify(sub).slice(0, 500)}`);
    const data = await poll(async () => {
      const r = await http(`https://api.wavespeed.ai/api/v3/predictions/${id}/result`, { headers });
      const st = r.data?.status;
      if (st === "completed") return r.data;
      if (["failed", "cancelled", "timeout"].includes(st)) throw new Error(`wavespeed job ${st}: ${r.data?.error || ""}`);
    });
    return { id, urls: data.outputs || [] };
  },
};

async function download(url, dest) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Download failed ${res.status}: ${url}`);
  fs.writeFileSync(dest, Buffer.from(await res.arrayBuffer()));
}
function extFrom(url, type) {
  const m = new URL(url).pathname.match(/\.(png|jpe?g|webp|gif|mp4|webm|mov)$/i);
  return m ? m[1].toLowerCase() : type === "video" ? "mp4" : "png";
}
const slug = (s) => s.toLowerCase().normalize("NFKD").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40) || "gen";

// ---------- main ----------
async function main() {
  loadEnv();
  const a = parseArgs(process.argv.slice(2));

  if (a.list) {
    for (const [k, m] of Object.entries(CATALOG)) {
      const ps = Object.entries(m.providers)
        .map(([p, c]) => `${p}${hasKey(p) ? "" : "(no key)"} $${c.est_usd}${c.verify ? "?" : ""}`)
        .join(", ");
      console.log(`${k.padEnd(16)} ${m.type.padEnd(6)} ${ps}`);
    }
    console.log("\n'?' = provider id/price not yet verified against live docs.");
    return;
  }
  if (a.spent) {
    console.log(`Spent (est.)${a.session ? ` in session "${a.session}"` : ""}: $${spent(a).toFixed(3)}`);
    return;
  }

  if (!a.model || !a.prompt) throw new Error("--model and --prompt are required (see --list)");
  const model = CATALOG[a.model];
  if (!model) throw new Error(`Unknown model "${a.model}". Run --list.`);
  if (model.requires_ref && !a.ref.length) throw new Error(`${a.model} needs --ref <image>`);

  const candidates = route(model, a);
  if (!candidates.length) {
    throw new Error(`No API key for any provider of ${a.model}. Set one of: ${Object.keys(model.providers).map((p) => KEY_VARS[p]).join(", ")} in .env.local`);
  }

  const [firstProvider, firstCfg] = candidates[0];
  const quote = priceFor(firstCfg, a) * (model.type === "image" ? a.count : 1);
  const already = spent(a);
  console.log(`Quote: ${a.model} via ${firstProvider} ≈ $${quote.toFixed(3)}${firstCfg.verify ? " (unverified price)" : ""}; spent so far $${already.toFixed(3)}${a.budget ? ` of $${a.budget}` : ""}`);
  if (a.budget && already + quote > a.budget) {
    throw new Error(`Budget exceeded: $${already.toFixed(3)} + $${quote.toFixed(3)} > $${a.budget}. Not submitting.`);
  }
  if (a.dryRun) {
    console.log("Dry run, nothing submitted. Fallback order:", candidates.map(([p]) => p).join(" → "));
    return;
  }

  const day = new Date().toISOString().slice(0, 10);
  const dir = path.join(outDir(a), day);
  fs.mkdirSync(dir, { recursive: true });
  const base = `${Date.now()}-${slug(a.name || a.prompt)}`;

  const errors = [];
  for (const [provider, cfg] of candidates) {
    let input;
    try {
      input = buildInput(provider, cfg, model, a);
    } catch (e) {
      if (e.skip) { errors.push(`${provider}: ${e.message}`); continue; }
      throw e;
    }
    const modelId = a.ref.length && cfg.edit_id ? cfg.edit_id : cfg.id;
    const cost = priceFor(cfg, a) * (model.type === "image" ? a.count : 1);
    console.log(`→ ${provider} ${modelId}`);
    const started = Date.now();
    try {
      const r = await PROVIDERS[provider](modelId, input);
      if (!r.urls.length) throw new Error("Job finished with no outputs");
      const files = [];
      for (const [i, u] of r.urls.entries()) {
        const f = path.join(dir, `${base}${r.urls.length > 1 ? `-${i + 1}` : ""}.${extFrom(u, model.type)}`);
        await download(u, f);
        files.push(path.relative(ROOT, f));
      }
      fs.writeFileSync(path.join(dir, `${base}.prompt.txt`), a.prompt + "\n");
      appendLog(a, {
        ts: new Date().toISOString(), status: "ok", session: a.session || null,
        model: a.model, provider, provider_model: modelId, prompt: a.prompt,
        refs: a.ref, params: { ...input, prompt: undefined, [cfg.ref_field]: undefined },
        est_usd: cost, seconds: Math.round((Date.now() - started) / 1000), job_id: r.id, files,
      });
      console.log(JSON.stringify({ ok: true, provider, est_usd: cost, files }, null, 2));
      return;
    } catch (e) {
      errors.push(`${provider}: ${e.message}`);
      appendLog(a, { ts: new Date().toISOString(), status: "error", session: a.session || null, model: a.model, provider, prompt: a.prompt, error: e.message });
      console.error(`✗ ${provider} failed, trying next provider. ${e.message}`);
    }
  }
  throw new Error(`All providers failed:\n  ${errors.join("\n  ")}`);
}

main().catch((e) => {
  console.error(`Error: ${e.message}`);
  process.exit(1);
});
