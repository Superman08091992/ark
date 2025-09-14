import pino from "pino";
export const log = pino({ level: process.env.LOG_LEVEL || "info" });
export const cfg = { PORT: Number(process.env.PORT || 3001) };
