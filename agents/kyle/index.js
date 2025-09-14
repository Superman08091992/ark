import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const MEM_DIR = path.resolve("memory");
const MEM_FILE = path.join(MEM_DIR, "mem.jsonl");
if (!fs.existsSync(MEM_DIR)) fs.mkdirSync(MEM_DIR, { recursive: true });

function remember(entry) {
  const row = { ts: Date.now(), ...entry };
  fs.appendFileSync(MEM_FILE, JSON.stringify(row) + "\n");
  return row;
}

function recall({ q = "", agent = "", limit = 5 } = {}) {
  if (!fs.existsSync(MEM_FILE)) return [];
  const lines = fs.readFileSync(MEM_FILE, "utf8").trim().split("\n").filter(Boolean).map(JSON.parse);
  const words = new Set(q.toLowerCase().split(/\W+/).filter(Boolean));
  const score = (t) => {
    const bag = (t || "").toLowerCase().split(/\W+/);
    let s = 0; for (const w of bag) if (words.has(w)) s++;
    return s;
  };
  return lines
    .map(r => ({ ...r, _score: score((r.input || "") + " " + (r.output || "")) + (agent && r.agent === agent ? 0.5 : 0) }))
    .sort((a, b) => b._score - a._score)
    .slice(0, limit);
}

const ROLE = `
You are Kyle, ARK’s orchestrator.

- Be terse. Max 220 tokens.
- Use markdown sections: Intent, Signals, Analysis, Answer, Next, Confidence, Risks, MEMO.
`.trim();

const BASE_URL = process.env.OPENAI_BASE_URL || "http://127.0.0.1:11434/v1";
const MODEL    = process.env.OPENAI_MODEL     || "tinyllama";

async function chat(prompt, context = []) {
  const messages = [{ role: "system", content: ROLE }];
  if (context.length) messages.push({ role: "system", content: context.join("\n\n") });
  messages.push({ role: "user", content: prompt });

  const body = {
    model: MODEL,
    messages,
    temperature: 0.1,
    max_tokens: 180,
    stop: ["\nMEMO:", "\n\n\n"]
  };

  const r = await fetch(`${BASE_URL}/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const j = await r.json();
  return j?.choices?.[0]?.message?.content?.trim() || "";
}

export async function run(userPrompt) {
  const memHits = recall({ q: userPrompt, limit: 5 }).map((x, i) => `[mem#${i + 1}] ${new Date(x.ts).toISOString()} :: ${x.agent} :: ${x.summary ?? (x.output || "").slice(0, 160)}`);
  const context = memHits.length ? [`Memory:\n${memHits.join("\n")}`] : [];
  const output = await chat(userPrompt, context);
  const memoMatch = output.split("\n").reverse().find(l => /^MEMO:\s*/i.test(l));
  const memo = (memoMatch || "MEMO: response stored").trim();
  remember({ agent: "Kyle", input: userPrompt, output, summary: memo.replace(/^MEMO:\s*/i, ""), tags: ["final"] });
  console.log(output);
  return output;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const prompt = process.argv.slice(2).join(" ");
  if (!prompt) { console.log('Usage: node agents/kyle/index.js "task"'); process.exit(0); }
  run(prompt).catch(e => { console.error("Kyle error:", e?.message); process.exit(1); });
}
