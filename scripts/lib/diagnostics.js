export async function collectLayoutDiagnostics(page) {
  return page.evaluate(() => {
    const pages = [...document.querySelectorAll(".report-page")];
    const warnings = [];
    const pageSummaries = pages.map((reportPage, index) => {
      const pageNumber = String(index + 1).padStart(2, "0");
      const pageRect = reportPage.getBoundingClientRect();
      const textLength = reportPage.innerText.trim().length;
      const overflowElements = [];
      const scrollOverflowElements = [];

      if (textLength < 90) {
        warnings.push(`Pagina ${pageNumber}: conteudo textual muito curto; revisar possivel pagina em branco.`);
      }

      for (const element of reportPage.querySelectorAll("*")) {
        const style = window.getComputedStyle(element);
        if (style.display === "none" || style.visibility === "hidden") {
          continue;
        }

        const rect = element.getBoundingClientRect();
        if (rect.width === 0 && rect.height === 0) {
          continue;
        }

        const className =
          typeof element.className === "string"
            ? element.className
            : String(element.getAttribute("class") || "");
        const tag = element.tagName.toLowerCase();
        const tolerance = 2;

        if (
          rect.left < pageRect.left - tolerance ||
          rect.right > pageRect.right + tolerance ||
          rect.top < pageRect.top - tolerance ||
          rect.bottom > pageRect.bottom + tolerance
        ) {
          overflowElements.push({
            tag,
            className,
            left: Math.round(rect.left - pageRect.left),
            right: Math.round(rect.right - pageRect.left),
            bottom: Math.round(rect.bottom - pageRect.top),
          });
        }

        const hasMeaningfulText = element.children.length === 0 && element.textContent.trim().length > 0;
        const clipsOwnContent = !["visible", "clip"].includes(style.overflowX);
        if (hasMeaningfulText && clipsOwnContent && element.scrollWidth > element.clientWidth + 2) {
          scrollOverflowElements.push({ tag, className });
        }
      }

      if (overflowElements.length > 0) {
        warnings.push(
          `Pagina ${pageNumber}: ${overflowElements.length} elemento(s) fora da caixa A4.`,
        );
      }

      if (scrollOverflowElements.length > 0) {
        warnings.push(
          `Pagina ${pageNumber}: ${scrollOverflowElements.length} elemento(s) com overflow horizontal interno.`,
        );
      }

      return {
        page: pageNumber,
        textLength,
        overflowElements: overflowElements.slice(0, 5),
        scrollOverflowElements: scrollOverflowElements.slice(0, 5),
      };
    });

    return {
      pageCount: pages.length,
      warnings,
      pageSummaries,
      documentWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
    };
  });
}
