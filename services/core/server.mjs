import express from "express";
import cors from "cors";
import morgan from "morgan";
import fs from "node:fs";
import path from "node:path";
import { run as runKyle } from "../../agents/kyle/index.js";

const __dirname = path.resolve();
const PORT = process.env.PORT || 8787;
const app = express();

app.use(cors());
app.use(express.json());
app.use(morgan("dev"));

// ✅ Static UI folder
app.use(express.static(path.join(__dirname, "ui")));

// ✅ Serve index.html for root
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "ui", "index.html"));
});

// ✅ Health endpoint
app.get("/health", (req, res) => res.status(200).send("OK"));

// ✅ Version endpoint
app.get("/version", (req, res) => {
  res.status(200).json({
    service: "ark-core",
    version: "1.0.0",
    status: "active",
    time: new Date().toISOString()
  });
});

// ✅ POST /chat
app.post("/chat", async (req, res) => {
  const { prompt } = req.body;
  if (!prompt) return res.status(400).json({ error: "Missing prompt" });

  try {
    const reply = await runKyle(prompt);
    res.status(200).json({ reply });
  } catch (err) {
    console.error("Kyle error:", err);
    res.status(500).json({ error: "Kyle failure", detail: err.message });
  }
});

// ✅ GET /memory
app.get("/memory", (req, res) => {
  const file = "memory/mem.jsonl";
  if (!fs.existsSync(file)) return res.json([]);
  const lines = fs.readFileSync(file, "utf8").trim().split("\n").slice(-50).map(l => {
    try { return JSON.parse(l); } catch { return null; }
  }).filter(Boolean);
  res.json(lines);
});

// ✅ POST /memory/reset
app.post("/memory/reset", (req, res) => {
  const file = "memory/mem.jsonl";
  try {
    fs.writeFileSync(file, "");
    res.json({ status: "cleared" });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ❌ 404 fallback
app.use((req, res) => {
  res.status(404).json({ error: "Not Found", path: req.originalUrl });
});

// ❌ Error handler
app.use((err, req, res, next) => {
  console.error("Unhandled error:", err);
  res.status(500).json({ error: "Internal Server Error" });
});

// ✅ Start server
app.listen(PORT, () => {
  console.log(`🚀 ARK Core (Express) running at http://localhost:${PORT}`);
});
