import path from "node:path";
import { fileURLToPath } from "node:url";
import { startStaticServer } from "./lib/static-server.js";

const __filename = fileURLToPath(import.meta.url);
const ROOT = path.resolve(path.dirname(__filename), "..");
const DIST = path.join(ROOT, "dist");

const server = await startStaticServer(DIST);
console.log(`Preview dos slides: ${server.url}slides-preview.html`);
console.log("Pressione Ctrl+C para encerrar.");
