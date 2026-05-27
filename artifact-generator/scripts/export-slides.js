import fs from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { DECK_PATH } from "./generate-deck.js";

const __filename = fileURLToPath(import.meta.url);
const ROOT = path.resolve(path.dirname(__filename), "..");
const DIST = path.join(ROOT, "dist");
const SCREENSHOTS_DIR = path.join(DIST, "screenshots");

export const SLIDES_PDF_PATH = path.join(
  DIST,
  "LLM_Trust_Safety_Framework_Apresentacao_Final_Premium.pdf",
);

export async function exportSlides({ quiet = false } = {}) {
  await fs.access(DECK_PATH);
  await fs.mkdir(SCREENSHOTS_DIR, { recursive: true });

  for (const file of await fs.readdir(SCREENSHOTS_DIR)) {
    if (/^slide-\d+\.png$/i.test(file)) {
      await fs.rm(path.join(SCREENSHOTS_DIR, file), { force: true });
    }
  }

  const script = `
$ErrorActionPreference = "Stop"
$pptxPath = ${JSON.stringify(DECK_PATH)}
$pdfPath = ${JSON.stringify(SLIDES_PDF_PATH)}
$screensDir = ${JSON.stringify(SCREENSHOTS_DIR)}
$powerpoint = New-Object -ComObject PowerPoint.Application
$presentation = $null
try {
  $presentation = $powerpoint.Presentations.Open($pptxPath, $true, $false, $false)
  $presentation.SaveAs($pdfPath, 32)
  $count = $presentation.Slides.Count
  for ($i = 1; $i -le $count; $i++) {
    $file = Join-Path $screensDir ("slide-{0:D2}.png" -f $i)
    $presentation.Slides.Item($i).Export($file, "PNG", 1920, 1080)
  }
  Write-Output ("SLIDE_COUNT=" + $count)
}
finally {
  if ($presentation -ne $null) {
    $presentation.Close()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($presentation)
  }
  if ($powerpoint -ne $null) {
    $powerpoint.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($powerpoint)
  }
  [GC]::Collect()
  [GC]::WaitForPendingFinalizers()
}
`;

  const result = spawnSync(
    "powershell",
    ["-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
    { encoding: "utf8", windowsHide: true },
  );

  if (result.status !== 0) {
    throw new Error(
      `Falha ao exportar via PowerPoint.\nSTDOUT:\n${result.stdout}\nSTDERR:\n${result.stderr}`,
    );
  }

  const slideCountMatch = result.stdout.match(/SLIDE_COUNT=(\d+)/);
  const slideCount = slideCountMatch ? Number(slideCountMatch[1]) : 0;
  const pdfStats = await fs.stat(SLIDES_PDF_PATH);
  const screenshots = (await fs.readdir(SCREENSHOTS_DIR)).filter((file) =>
    /^slide-\d+\.png$/i.test(file),
  );

  await writePreviewHtml(screenshots);

  if (!quiet) {
    console.log(`PDF exportado: ${SLIDES_PDF_PATH}`);
    console.log(`Screenshots: ${screenshots.length}`);
  }

  return {
    pdfPath: SLIDES_PDF_PATH,
    screenshotsDir: SCREENSHOTS_DIR,
    slideCount,
    screenshotCount: screenshots.length,
    pdfSizeBytes: pdfStats.size,
  };
}

async function writePreviewHtml(files) {
  const cards = files
    .sort()
    .map(
      (file) => `
        <article>
          <img src="screenshots/${file}" alt="${file}" />
          <span>${file}</span>
        </article>`,
    )
    .join("\n");
  const html = `<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Preview Slides - LLM Trust</title>
  <style>
    body { margin: 0; font-family: Inter, Segoe UI, Arial, sans-serif; background: #06111F; color: #F8FAFC; }
    header { position: sticky; top: 0; padding: 18px 24px; background: rgba(6,17,31,.92); border-bottom: 1px solid rgba(0,212,255,.28); z-index: 2; }
    h1 { margin: 0; font-size: 18px; }
    main { display: grid; gap: 22px; padding: 24px; max-width: 1180px; margin: 0 auto; }
    article { background: rgba(248,250,252,.06); border: 1px solid rgba(203,213,225,.18); border-radius: 8px; padding: 12px; }
    img { display: block; width: 100%; border-radius: 6px; }
    span { display: block; margin-top: 8px; color: #CBD5E1; font-size: 13px; font-weight: 700; }
  </style>
</head>
<body>
  <header><h1>LLM Trust & Safety Framework - Preview dos Slides</h1></header>
  <main>${cards}</main>
</body>
</html>`;
  await fs.writeFile(path.join(DIST, "slides-preview.html"), html, "utf8");
}

if (process.argv[1] && path.resolve(process.argv[1]) === __filename) {
  exportSlides().catch((error) => {
    console.error(error);
    process.exit(1);
  });
}
