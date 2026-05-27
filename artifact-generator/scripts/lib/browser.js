import { chromium } from "playwright";

const CHANNELS = [
  { label: "Microsoft Edge", options: { channel: "msedge" } },
  { label: "Google Chrome", options: { channel: "chrome" } },
  { label: "Playwright Chromium", options: {} },
];

export async function launchReportBrowser() {
  const errors = [];

  for (const candidate of CHANNELS) {
    try {
      const browser = await chromium.launch({
        headless: true,
        args: ["--disable-dev-shm-usage"],
        ...candidate.options,
      });
      return { browser, mode: candidate.label };
    } catch (error) {
      errors.push(`${candidate.label}: ${error.message.split("\n")[0]}`);
    }
  }

  throw new Error(`Nao foi possivel iniciar Chromium. Tentativas: ${errors.join(" | ")}`);
}

export async function waitForReportReady(page) {
  await page.waitForSelector(".report-page", { timeout: 30000 });
  await page.evaluate(async () => {
    if ("fonts" in document) {
      await document.fonts.ready;
    }
  });
  await page.waitForTimeout(300);
}
