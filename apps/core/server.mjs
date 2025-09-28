import "dotenv/config";
import "dotenv/config";
import express from "express";
import cors from "cors";
import morgan from "morgan";
import { log, cfg } from "@ark/shared-node";

const app = express();
app.use(cors());
app.use(express.json());
app.use(morgan("dev"));

app.get("/health", (_req,res)=>res.status(200).send("OK"));
app.post("/ask", async (req,res)=> {
  const q = req.body?.q ?? req.body?.prompt ?? "";
  res.json({ ok:true, result: { backend:"echo", reply:`echo: ${q}` } });
});

app.use((_,res)=>res.status(404).json({ error:"Not Found" }));
app.listen(cfg.PORT, ()=>log.info(`core :${cfg.PORT}`));
