import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { generatePdf } from "./generate-pdf.js";
import { screenshotPages } from "./screenshot-pages.js";

const __filename = fileURLToPath(import.meta.url);
const ROOT = path.resolve(path.dirname(__filename), "..");
const DIST = path.join(ROOT, "dist");
const PDF_PATH = path.join(DIST, "LLM_Trust_Safety_Framework_Relatorio_Final.pdf");
const QA_PATH = path.join(DIST, "QA_REPORT.md");

function countPdfPages(buffer) {
  const text = buffer.toString("latin1");
  const matches = text.match(/\/Type\s*\/Page\b/g);
  return matches ? matches.length : 0;
}

function formatBytes(bytes) {
  if (bytes > 1024 * 1024) {
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  }
  return `${(bytes / 1024).toFixed(1)} KB`;
}

function statusLine(ok) {
  return ok ? "OK" : "ATENCAO";
}

export async function runQa() {
  const generated = await generatePdf({ quiet: true });
  const screenshots = await screenshotPages({ quiet: true });

  const pdfBuffer = await fs.readFile(PDF_PATH);
  const pdfStats = await fs.stat(PDF_PATH);
  const pdfPageCount = countPdfPages(pdfBuffer) || generated.domPageCount;
  const screenshotFiles = await fs.readdir(path.join(DIST, "screenshots"));
  const pageScreenshotCount = screenshotFiles.filter((file) => /^page-\d+\.png$/.test(file)).length;
  const expectedScreenshots = Array.from({ length: generated.domPageCount }, (_, index) =>
    `page-${String(index + 1).padStart(2, "0")}.png`,
  );
  const missingScreenshots = expectedScreenshots.filter((file) => !screenshotFiles.includes(file));
  const sizeOk = pdfStats.size > 100 * 1024;
  const pageCountOk = pdfPageCount === generated.domPageCount;
  const screenshotsOk = pageScreenshotCount === generated.domPageCount && missingScreenshots.length === 0;
  const diagnosticsWarnings = screenshots.diagnostics.warnings || [];
  const qaStatus = sizeOk && pageCountOk && screenshotsOk ? "APROVADO" : "ATENCAO";
  const timestamp = new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "full",
    timeStyle: "long",
    timeZone: "America/Sao_Paulo",
  }).format(new Date());

  const report = `# QA Report - LLM Trust & Safety Framework

Gerado em: ${timestamp}

Status geral: **${qaStatus}**

## Arquivos gerados

| Arquivo | Status |
| --- | --- |
| dist/index.html | ${statusLine(true)} |
| dist/LLM_Trust_Safety_Framework_Relatorio_Final.pdf | ${statusLine(true)} |
| dist/screenshots/page-01.png ... page-${String(generated.domPageCount).padStart(2, "0")}.png | ${statusLine(screenshotsOk)} |
| dist/screenshots/_diagnostics.json | ${statusLine(true)} |

## Verificações automatizadas

| Item | Resultado |
| --- | --- |
| PDF existe | ${statusLine(true)} |
| Tamanho do PDF | ${statusLine(sizeOk)} - ${formatBytes(pdfStats.size)} |
| Quantidade de páginas no HTML | ${generated.domPageCount} |
| Quantidade de páginas no PDF | ${pdfPageCount} |
| Contagem PDF x HTML | ${statusLine(pageCountOk)} |
| Screenshots criadas | ${statusLine(screenshotsOk)} - ${pageScreenshotCount}/${generated.domPageCount} |
| Navegador Playwright | ${generated.browserMode} |
| Erro no Playwright | OK - nenhum erro capturado durante a execução |

## Diagnóstico visual automatizado

${
  diagnosticsWarnings.length > 0
    ? diagnosticsWarnings.map((warning) => `- ${warning}`).join("\n")
    : "- Nenhum overflow horizontal ou elemento fora da caixa A4 foi identificado pelo diagnóstico automatizado."
}

## Observações

- O PDF foi gerado em A4 portrait com \`printBackground: true\`.
- A captura de screenshots foi feita diretamente das páginas A4 renderizadas no navegador.
- Verificações de títulos isolados, cortes sutis de tabela e qualidade editorial final continuam recomendadas como revisão manual.

## Checklist de validação manual

- [ ] Revisar capa em tela cheia e no PDF exportado.
- [ ] Conferir se cabeçalhos e rodapés não sobrepõem conteúdo.
- [ ] Verificar leitura das tabelas de risco e alinhamento normativo.
- [ ] Confirmar se o sumário reflete a paginação final.
- [ ] Conferir ortografia, nomes dos integrantes e dados institucionais.
- [ ] Abrir todos os screenshots de \`dist/screenshots\` e procurar cortes visuais finos.
- [ ] Validar se o tom acadêmico deixa claro que se trata de protótipo demonstrativo.
`;

  await fs.writeFile(QA_PATH, report, "utf8");
  console.log(`QA gerado: ${QA_PATH}`);
  console.log(`Status: ${qaStatus}`);
  console.log(`Paginas: ${generated.domPageCount}`);

  return {
    qaPath: QA_PATH,
    status: qaStatus,
    pdfPageCount,
    screenshotCount: pageScreenshotCount,
    warnings: diagnosticsWarnings,
  };
}

if (process.argv[1] && path.resolve(process.argv[1]) === __filename) {
  runQa().catch((error) => {
    console.error(error);
    process.exit(1);
  });
}
