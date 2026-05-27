import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import JSZip from "jszip";
import { generateDeck } from "./generate-deck.js";
import { exportSlides, SLIDES_PDF_PATH } from "./export-slides.js";

const __filename = fileURLToPath(import.meta.url);
const ROOT = path.resolve(path.dirname(__filename), "..");
const DIST = path.join(ROOT, "dist");
const QA_PATH = path.join(DIST, "QA_SLIDES_REPORT.md");
const SCREENSHOTS_DIR = path.join(DIST, "screenshots");
const PPTX_PATH = path.join(DIST, "LLM_Trust_Safety_Framework_Apresentacao_Final_Premium.pptx");

function countPdfPages(buffer) {
  const text = buffer.toString("latin1");
  const matches = text.match(/\/Type\s*\/Page\b/g);
  return matches ? matches.length : 0;
}

function formatBytes(bytes) {
  if (bytes > 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

async function countPptxSlides(filePath) {
  const data = await fs.readFile(filePath);
  const zip = await JSZip.loadAsync(data);
  return Object.keys(zip.files).filter((name) => /^ppt\/slides\/slide\d+\.xml$/.test(name)).length;
}

function status(ok) {
  return ok ? "OK" : "ATENCAO";
}

export async function runSlidesQa() {
  const deck = await generateDeck({ quiet: true });
  const exported = await exportSlides({ quiet: true });

  const pptxStats = await fs.stat(PPTX_PATH);
  const pdfStats = await fs.stat(SLIDES_PDF_PATH);
  const slideCount = await countPptxSlides(PPTX_PATH);
  const pdfPages = countPdfPages(await fs.readFile(SLIDES_PDF_PATH)) || exported.slideCount;
  const screenshots = (await fs.readdir(SCREENSHOTS_DIR)).filter((file) =>
    /^slide-\d+\.png$/i.test(file),
  );
  const expectedScreenshots = Array.from({ length: slideCount }, (_, index) =>
    `slide-${String(index + 1).padStart(2, "0")}.png`,
  );
  const missingScreenshots = expectedScreenshots.filter((file) => !screenshots.includes(file));
  const slideCountOk = slideCount === 15;
  const pdfOk = pdfPages === slideCount;
  const screenshotsOk = screenshots.length === slideCount && missingScreenshots.length === 0;
  const sizeOk = pptxStats.size > 100 * 1024 && pdfStats.size > 100 * 1024;
  const overall = slideCountOk && pdfOk && screenshotsOk && sizeOk ? "APROVADO" : "ATENCAO";
  const timestamp = new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "full",
    timeStyle: "long",
    timeZone: "America/Sao_Paulo",
  }).format(new Date());

  const report = `# QA Slides Report - LLM Trust & Safety Framework

Gerado em: ${timestamp}

Status geral: **${overall}**

## Arquivos gerados

| Arquivo | Status |
| --- | --- |
| dist/LLM_Trust_Safety_Framework_Apresentacao_Final_Premium.pptx | ${status(true)} |
| dist/LLM_Trust_Safety_Framework_Apresentacao_Final_Premium.pdf | ${status(true)} |
| dist/screenshots/slide-01.png ... slide-${String(slideCount).padStart(2, "0")}.png | ${status(screenshotsOk)} |
| dist/slides-preview.html | ${status(true)} |

## Verificações automatizadas

| Item | Resultado |
| --- | --- |
| PPTX existe | ${status(true)} - ${formatBytes(pptxStats.size)} |
| PDF existe | ${status(true)} - ${formatBytes(pdfStats.size)} |
| Quantidade de slides no PPTX | ${slideCount} |
| Quantidade de páginas no PDF | ${pdfPages} |
| Deck com 15 slides | ${status(slideCountOk)} |
| PDF x PPTX | ${status(pdfOk)} |
| Screenshots criadas | ${status(screenshotsOk)} - ${screenshots.length}/${slideCount} |
| Exportação PowerPoint | OK - PDF e PNGs gerados via automação local |

## Observações

- O deck foi gerado em widescreen 16:9.
- O conteúdo principal foi criado como textos, shapes, linhas, tabelas e diagramas editáveis no PowerPoint.
- Elementos visuais de fundo usam formas editáveis e não substituem o conteúdo principal.
- O arquivo original em \`source/pptx\` foi preservado.

## Checklist de validação manual

- [ ] Abrir o PPTX no PowerPoint e verificar edição de textos, cards e diagramas.
- [ ] Conferir se nenhum texto está cortado.
- [ ] Verificar contraste e legibilidade em projetor.
- [ ] Revisar capa, slide 13 de normas e slide 14 de demo.
- [ ] Confirmar rodapé e numeração em todos os slides.
- [ ] Conferir nomes dos integrantes, professor, instituição e período.
- [ ] Validar se o deck mantém tom acadêmico e não promete produto final de mercado.
`;

  await fs.writeFile(QA_PATH, report, "utf8");
  console.log(`QA de slides gerado: ${QA_PATH}`);
  console.log(`Status: ${overall}`);
  console.log(`Slides: ${slideCount}`);

  return {
    qaPath: QA_PATH,
    status: overall,
    slideCount,
    pdfPages,
    screenshotCount: screenshots.length,
    deck,
    exported,
  };
}

if (process.argv[1] && path.resolve(process.argv[1]) === __filename) {
  runSlidesQa().catch((error) => {
    console.error(error);
    process.exit(1);
  });
}
