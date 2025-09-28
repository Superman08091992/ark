import fs from "node:fs";
import path from "node:path";
import fetch from "node-fetch";

const memFile = path.join("memory", "mem.jsonl");

function loadMemory() {
  if (!fs.existsSync(memFile)) return [];
  const lines = fs.readFileSync(memFile, "utf8").trim().split("\n");
  return lines.map(line => {
    try { return JSON.parse(line); } catch { return null; }
  }).filter(Boolean);
}

export async function run(prompt) {
  const memory = loadMemory();
  const context = memory.map(m => m.input).join("\n");
  const fullPrompt = `${context}\n\nUser: ${prompt}\nKyle:`;

  const res = await fetch(`${process.env.OPENAI_BASE_URL}/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: process.env.OPENAI_MODEL || "tinyllama",
      prompt: fullPrompt,
      max_tokens: 200,
      temperature: 0.7
    })
  });

  const data = await res.json();
  return data.choices?.[0]?.text?.trim() || "[No reply]";
}
