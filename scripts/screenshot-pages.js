import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { launchReportBrowser, waitForReportReady } from "./lib/browser.js";
import { collectLayoutDiagnostics } from "./lib/diagnostics.js";
import { startStaticServer } from "./lib/static-server.js";

const __filename = fileURLToPath(import.meta.url);
const ROOT = path.resolve(path.dirname(__filename), "..");
const DIST = path.join(ROOT, "dist");
const SCREENSHOTS_DIR = path.join(DIST, "screenshots");

export async function screenshotPages({ quiet = false } = {}) {
  await fs.access(path.join(DIST, "index.html"));
  await fs.rm(SCREENSHOTS_DIR, { recursive: true, force: true });
  await fs.mkdir(SCREENSHOTS_DIR, { recursive: true });

  const server = await startStaticServer(DIST);
  let browser;
  let mode = "unknown";

  try {
    const launched = await launchReportBrowser();
    browser = launched.browser;
    mode = launched.mode;

    const context = await browser.newContext({
      viewport: { width: 1280, height: 1800 },
      deviceScaleFactor: 2,
    });
    const page = await context.newPage();
    await page.goto(server.url, { waitUntil: "networkidle" });
    await waitForReportReady(page);

    const pages = page.locator(".report-page");
    const count = await pages.count();
    const files = [];

    for (let index = 0; index < count; index += 1) {
      const pageNumber = String(index + 1).padStart(2, "0");
      const filePath = path.join(SCREENSHOTS_DIR, `page-${pageNumber}.png`);
      await pages.nth(index).screenshot({ path: filePath, animations: "disabled" });
      files.push(filePath);
      if (!quiet) {
        console.log(`Screenshot gerado: ${filePath}`);
      }
    }

    const diagnostics = await collectLayoutDiagnostics(page);
    await fs.writeFile(
      path.join(SCREENSHOTS_DIR, "_diagnostics.json"),
      JSON.stringify(diagnostics, null, 2),
      "utf8",
    );

    return {
      count,
      files,
      diagnostics,
      browserMode: mode,
      screenshotsDir: SCREENSHOTS_DIR,
    };
  } finally {
    if (browser) {
      await browser.close();
    }
    await server.close();
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === __filename) {
  screenshotPages().catch((error) => {
    console.error(error);
    process.exit(1);
  });
}
