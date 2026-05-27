from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "docs/report/final/llm_trust_safety_framework_relatorio_final.pdf",
    "slides/final/llm_trust_safety_framework_apresentacao_final.pptx",
    "video/roteiro/roteiro_video_final.md",
    "README.md",
    "DELIVERY_CHECKLIST.md",
    "ARTIFACT_MANIFEST.md",
]

RECOMMENDED = [
    "slides/final/llm_trust_safety_framework_apresentacao_final.pdf",
    "PROJECT_OVERVIEW.md",
    "docs/report/qa/qa_report.md",
    "slides/qa/qa_slides_report.md",
    "video/roteiro/andrey.txt",
    "video/roteiro/paulo.txt",
    "video/roteiro/renes.txt",
    "video/roteiro/renan.txt",
]


def status_line(label: str, relative_path: str) -> bool:
    path = ROOT / relative_path
    exists = path.exists()
    status = "OK" if exists else "ERRO"
    print(f"[{status}] {label}: {relative_path}")
    return exists


def main() -> int:
    print("Validacao de artefatos - LLM Trust & Safety Framework\n")

    missing_required = []
    for item in REQUIRED:
        if not status_line("essencial", item):
            missing_required.append(item)

    print("\nItens recomendados")
    for item in RECOMMENDED:
        status_line("recomendado", item)

    if missing_required:
        print("\nResultado: ERRO")
        print("Arquivos essenciais ausentes:")
        for item in missing_required:
            print(f"- {item}")
        return 1

    print("\nResultado: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

