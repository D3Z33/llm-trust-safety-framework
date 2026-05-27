import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { launchReportBrowser, waitForReportReady } from "./lib/browser.js";
import { startStaticServer } from "./lib/static-server.js";

const __filename = fileURLToPath(import.meta.url);
const ROOT = path.resolve(path.dirname(__filename), "..");
const DIST = path.join(ROOT, "dist");
const PDF_PATH = path.join(DIST, "LLM_Trust_Safety_Framework_Relatorio_Final.pdf");

export async function generatePdf({ quiet = false } = {}) {
  const indexPath = path.join(DIST, "index.html");
  await fs.access(indexPath);
  await fs.mkdir(DIST, { recursive: true });

  const server = await startStaticServer(DIST);
  let browser;
  let mode = "unknown";

  try {
    const launched = await launchReportBrowser();
    browser = launched.browser;
    mode = launched.mode;

    const context = await browser.newContext({
      viewport: { width: 1240, height: 1754 },
      deviceScaleFactor: 1,
    });
    const page = await context.newPage();
    await page.goto(server.url, { waitUntil: "networkidle" });
    await waitForReportReady(page);

    const domPageCount = await page.locator(".report-page").count();
    await page.emulateMedia({ media: "print" });
    await page.pdf({
      path: PDF_PATH,
      format: "A4",
      printBackground: true,
      preferCSSPageSize: true,
      margin: { top: "0mm", right: "0mm", bottom: "0mm", left: "0mm" },
    });

    const stats = await fs.stat(PDF_PATH);
    const result = {
      pdfPath: PDF_PATH,
      sizeBytes: stats.size,
      domPageCount,
      browserMode: mode,
      url: server.url,
    };

    if (!quiet) {
      console.log(`PDF gerado: ${PDF_PATH}`);
      console.log(`Paginas HTML: ${domPageCount}`);
      console.log(`Navegador: ${mode}`);
      console.log(`Tamanho: ${stats.size} bytes`);
    }

    return result;
  } finally {
    if (browser) {
      await browser.close();
    }
    await server.close();
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === __filename) {
  generatePdf().catch((error) => {
    console.error(error);
    process.exit(1);
  });
}
