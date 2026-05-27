import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import mammoth from "mammoth";

const __filename = fileURLToPath(import.meta.url);
const ROOT = path.resolve(path.dirname(__filename), "..");
const SOURCE = path.join(ROOT, "source", "docx", "LLM Trust.docx");
const OUTPUT = path.join(ROOT, "work", "docx", "extracted-docx.txt");

async function extractDocx() {
  const result = await mammoth.extractRawText({ path: SOURCE });
  await fs.mkdir(path.dirname(OUTPUT), { recursive: true });
  await fs.writeFile(OUTPUT, result.value, "utf8");

  if (result.messages.length > 0) {
    console.warn("Avisos do mammoth:");
    for (const message of result.messages) {
      console.warn(`- ${message.message}`);
    }
  }

  console.log(`Conteudo extraido: ${OUTPUT}`);
}

extractDocx().catch((error) => {
  console.error(error);
  process.exit(1);
});
