from datetime import datetime
from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "ARTIFACT_MANIFEST.md"
SCAN_DIRS = ["docs", "slides", "video", "archive/original_files"]
HASH_EXTENSIONS = {".pdf", ".pptx", ".docx"}


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_type(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return "PDF"
    if suffix == ".pptx":
        return "PPTX"
    if suffix == ".docx":
        return "DOCX"
    if suffix == ".png":
        return "Screenshot"
    if suffix in {".md", ".txt"} and relative.startswith("video/"):
        return "Roteiro"
    if suffix in {".md", ".txt"}:
        return "Documento"
    if suffix == ".js":
        return "Script"
    return "Arquivo"


def observation(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    if "report/final" in relative:
        return "Relatorio final"
    if "slides/final" in relative:
        return "Apresentacao final"
    if "screenshots" in relative:
        return "Evidencia de QA visual"
    if "archive/original_files" in relative:
        return "Copia preservada do original"
    if "roteiro" in relative:
        return "Material de video"
    if "qa" in relative:
        return "Relatorio de QA"
    return "Arquivo de apoio"


def iter_artifacts():
    for directory in SCAN_DIRS:
        base = ROOT / directory
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file():
                yield path


def build_manifest(paths):
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Manifesto de Artefatos",
        "",
        f"Gerado em: {generated_at}",
        "",
        "| Tipo | Arquivo | Caminho | Status | Observacao | SHA256 |",
        "|---|---|---|---|---|---|",
    ]

    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        checksum = sha256_file(path) if path.suffix.lower() in HASH_EXTENSIONS else "-"
        lines.append(
            f"| {artifact_type(path)} | {path.name} | `{relative}` | OK | {observation(path)} | `{checksum}` |"
        )

    lines.extend(
        [
            "",
            "## Arquivos principais",
            "",
            "- Relatorio final: `docs/report/final/llm_trust_safety_framework_relatorio_final.pdf`",
            "- Apresentacao final: `slides/final/llm_trust_safety_framework_apresentacao_final.pptx`",
            "- Apresentacao em PDF: `slides/final/llm_trust_safety_framework_apresentacao_final.pdf`",
            "- Roteiro consolidado: `video/roteiro/roteiro_video_final.md`",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> int:
    paths = list(iter_artifacts())
    MANIFEST.write_text(build_manifest(paths), encoding="utf-8")

    print("Manifesto gerado com sucesso.")
    print(f"Arquivo: {MANIFEST.relative_to(ROOT)}")
    print(f"Artefatos listados: {len(paths)}")

    hashed = [path for path in paths if path.suffix.lower() in HASH_EXTENSIONS]
    print(f"Arquivos com SHA256: {len(hashed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

