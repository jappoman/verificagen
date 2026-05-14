#!/usr/bin/env python3

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE_DIR = ROOT / "teaching-materials"
DEFAULT_OUTPUT_DIR = DEFAULT_SOURCE_DIR / "_extracted-text"
MIN_TEXT_CHARS_PER_PAGE = 80


class PreparationError(Exception):
    pass


def run_command(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def command_available(command: str) -> bool:
    return shutil.which(command) is not None


def slug_for(path: Path) -> str:
    safe = "".join(char if char.isalnum() else "-" for char in path.stem.lower())
    safe = "-".join(part for part in safe.split("-") if part)
    return safe or "materiale"


def page_count(pdf_path: Path) -> int:
    if not command_available("pdfinfo"):
        raise PreparationError("pdfinfo non trovato: installa poppler-utils.")

    result = run_command(["pdfinfo", str(pdf_path)])
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise PreparationError(f"Numero di pagine non trovato in {pdf_path.name}.")


def extract_pdf_page_text(pdf_path: Path, page_number: int) -> str:
    if not command_available("pdftotext"):
        raise PreparationError("pdftotext non trovato: installa poppler-utils.")

    result = run_command(
        [
            "pdftotext",
            "-layout",
            "-enc",
            "UTF-8",
            "-f",
            str(page_number),
            "-l",
            str(page_number),
            str(pdf_path),
            "-",
        ],
        check=False,
    )
    return result.stdout.strip()


def ocr_pdf_page(pdf_path: Path, page_number: int, language: str, dpi: int) -> str:
    if not command_available("pdftoppm"):
        raise PreparationError("pdftoppm non trovato: installa poppler-utils.")
    if not command_available("tesseract"):
        raise PreparationError("tesseract non trovato: installa tesseract e il pacchetto lingua italiano.")

    with tempfile.TemporaryDirectory(prefix="verificagen-ocr-") as tmp_dir:
        prefix = Path(tmp_dir) / "page"
        run_command(
            [
                "pdftoppm",
                "-r",
                str(dpi),
                "-png",
                "-f",
                str(page_number),
                "-singlefile",
                str(pdf_path),
                str(prefix),
            ]
        )
        image_path = prefix.with_suffix(".png")
        result = run_command(
            ["tesseract", str(image_path), "stdout", "-l", language],
            check=False,
        )
        if result.returncode != 0 and language != "ita":
            result = run_command(
                ["tesseract", str(image_path), "stdout", "-l", "ita"],
                check=False,
            )
        return result.stdout.strip()


def ocr_image(image_path: Path, language: str) -> str:
    if not command_available("tesseract"):
        raise PreparationError("tesseract non trovato: installa tesseract e il pacchetto lingua italiano.")

    result = run_command(["tesseract", str(image_path), "stdout", "-l", language], check=False)
    if result.returncode != 0 and language != "ita":
        result = run_command(["tesseract", str(image_path), "stdout", "-l", "ita"], check=False)
    return result.stdout.strip()


def write_markdown(output_path: Path, title: str, pages: list[tuple[int | None, str, str]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {title}", ""]

    for page_number, method, text in pages:
        heading = "Contenuto" if page_number is None else f"Pagina {page_number}"
        lines.extend([f"## {heading}", "", f"_Metodo: {method}_", ""])
        lines.append(text.strip() if text.strip() else "[Nessun testo estratto]")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def prepare_pdf(pdf_path: Path, output_dir: Path, language: str, dpi: int) -> tuple[Path, bool, list[str]]:
    pages_total = page_count(pdf_path)
    pages: list[tuple[int | None, str, str]] = []
    warnings: list[str] = []
    used_ocr = False

    for page_number in range(1, pages_total + 1):
        text = extract_pdf_page_text(pdf_path, page_number)
        method = "pdftotext"

        if len(text.strip()) < MIN_TEXT_CHARS_PER_PAGE:
            try:
                text = ocr_pdf_page(pdf_path, page_number, language, dpi)
                method = "OCR tesseract"
                used_ocr = True
            except PreparationError as error:
                method = "OCR non eseguito"
                warnings.append(f"{pdf_path.name}, pagina {page_number}: {error}")

        pages.append((page_number, method, text))

    output_path = output_dir / f"{slug_for(pdf_path)}.md"
    write_markdown(output_path, pdf_path.name, pages)
    return output_path, used_ocr, warnings


def prepare_plain_text(path: Path, output_dir: Path) -> tuple[Path, bool, list[str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    output_path = output_dir / f"{slug_for(path)}.md"
    write_markdown(output_path, path.name, [(None, "lettura diretta", text)])
    return output_path, False, []


def prepare_image(path: Path, output_dir: Path, language: str) -> tuple[Path, bool, list[str]]:
    warnings: list[str] = []
    try:
        text = ocr_image(path, language)
        method = "OCR tesseract"
        used_ocr = True
    except PreparationError as error:
        text = ""
        method = "OCR non eseguito"
        used_ocr = False
        warnings.append(f"{path.name}: {error}")

    output_path = output_dir / f"{slug_for(path)}.md"
    write_markdown(output_path, path.name, [(None, method, text)])
    return output_path, used_ocr, warnings


def iter_materials(source_dir: Path) -> list[Path]:
    ignored_dirs = {DEFAULT_OUTPUT_DIR.name}
    return [
        path
        for path in sorted(source_dir.iterdir())
        if path.is_file() and path.parent.name not in ignored_dirs and path.name != ".gitkeep"
    ]


def prepare_material(path: Path, output_dir: Path, language: str, dpi: int) -> tuple[Path, bool, list[str]]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return prepare_pdf(path, output_dir, language, dpi)
    if suffix in {".txt", ".md"}:
        return prepare_plain_text(path, output_dir)
    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}:
        return prepare_image(path, output_dir, language)

    output_path = output_dir / f"{slug_for(path)}.unsupported.md"
    write_markdown(
        output_path,
        path.name,
        [(None, "non supportato", f"Formato non supportato automaticamente: {path.suffix}")],
    )
    return output_path, False, [f"{path.name}: formato non supportato automaticamente."]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estrae testo dai materiali didattici e usa OCR per PDF o immagini scannerizzati."
    )
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="Cartella dei materiali didattici.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Cartella dei testi estratti.")
    parser.add_argument("--language", default="ita+eng", help="Lingue Tesseract, per esempio ita o ita+eng.")
    parser.add_argument("--dpi", type=int, default=300, help="Risoluzione usata per convertire le pagine PDF in immagini.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not source_dir.exists():
        print(f"Cartella materiali non trovata: {source_dir}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    materials = iter_materials(source_dir)

    if not materials:
        print(f"Nessun materiale trovato in {source_dir}.")
        return 0

    all_warnings: list[str] = []
    ocr_count = 0

    for material in materials:
        try:
            output_path, used_ocr, warnings = prepare_material(material, output_dir, args.language, args.dpi)
        except (PreparationError, subprocess.CalledProcessError) as error:
            all_warnings.append(f"{material.name}: {error}")
            continue

        if used_ocr:
            ocr_count += 1
        all_warnings.extend(warnings)
        print(f"Creato {output_path.relative_to(ROOT)}")

    print()
    print(f"Materiali elaborati: {len(materials)}")
    print(f"File con OCR: {ocr_count}")

    if all_warnings:
        print()
        print("Avvisi:")
        for warning in all_warnings:
            print(f"- {warning}")
        print()
        print("Se gli avvisi citano tesseract, installa Tesseract OCR e riesegui questo comando.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
