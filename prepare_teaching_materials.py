#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE_DIR = ROOT / "teaching-materials"
DEFAULT_OUTPUT_DIR = DEFAULT_SOURCE_DIR / "_extracted-text"
MIN_TEXT_CHARS_PER_PAGE = 80
MIN_CACHED_TEXT_CHARS = 500
DEFAULT_OCR_WORKERS = 4


class PreparationError(Exception):
    pass


def run_command(
    command: list[str],
    *,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )


def command_available(command: str) -> bool:
    return shutil.which(command) is not None


def slug_for(path: Path) -> str:
    safe = "".join(char if char.isalnum() else "-" for char in path.stem.lower())
    safe = "-".join(part for part in safe.split("-") if part)
    return safe or "materiale"


def output_path_for(path: Path, output_dir: Path) -> Path:
    supported = {".pdf", ".txt", ".md", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
    suffix = ".md" if path.suffix.lower() in supported else ".unsupported.md"
    return output_dir / f"{slug_for(path)}{suffix}"


def extracted_text_char_count(markdown: str) -> int:
    ignored_prefixes = ("#", "_Metodo:")
    ignored_lines = {"[Nessun testo estratto]"}
    count = 0
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(ignored_prefixes) or line in ignored_lines:
            continue
        count += len(line)
    return count


def cached_output_is_usable(source_path: Path, output_path: Path, min_chars: int) -> bool:
    if not output_path.exists():
        return False
    if output_path.stat().st_mtime < source_path.stat().st_mtime:
        return False
    markdown = output_path.read_text(encoding="utf-8", errors="replace")
    return extracted_text_char_count(markdown) >= min_chars


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
        tesseract_env = os.environ.copy()
        tesseract_env.setdefault("OMP_THREAD_LIMIT", "1")
        result = run_command(
            ["tesseract", str(image_path), "stdout", "-l", language],
            check=False,
            env=tesseract_env,
        )
        if result.returncode != 0 and language != "ita":
            result = run_command(
                ["tesseract", str(image_path), "stdout", "-l", "ita"],
                check=False,
                env=tesseract_env,
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


def ocr_pdf_page_result(pdf_path: Path, page_number: int, language: str, dpi: int) -> tuple[int, str, str | None]:
    try:
        return page_number, ocr_pdf_page(pdf_path, page_number, language, dpi), None
    except PreparationError as error:
        return page_number, "", str(error)


def prepare_pdf(
    pdf_path: Path,
    output_dir: Path,
    language: str,
    dpi: int,
    ocr_workers: int,
) -> tuple[Path, bool, list[str]]:
    pages_total = page_count(pdf_path)
    pages: list[tuple[int | None, str, str] | None] = [None] * pages_total
    ocr_page_numbers: list[int] = []
    warnings: list[str] = []
    used_ocr = False

    for page_number in range(1, pages_total + 1):
        text = extract_pdf_page_text(pdf_path, page_number)
        method = "pdftotext"

        if len(text.strip()) < MIN_TEXT_CHARS_PER_PAGE:
            ocr_page_numbers.append(page_number)
        else:
            pages[page_number - 1] = (page_number, method, text)

    if ocr_page_numbers:
        used_ocr = True
        if ocr_workers <= 1 or len(ocr_page_numbers) == 1:
            for page_number in ocr_page_numbers:
                page_number, text, error = ocr_pdf_page_result(pdf_path, page_number, language, dpi)
                if error:
                    pages[page_number - 1] = (page_number, "OCR non eseguito", "")
                    warnings.append(f"{pdf_path.name}, pagina {page_number}: {error}")
                else:
                    pages[page_number - 1] = (page_number, "OCR tesseract", text)
        else:
            workers = min(ocr_workers, len(ocr_page_numbers))
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [
                    executor.submit(ocr_pdf_page_result, pdf_path, page_number, language, dpi)
                    for page_number in ocr_page_numbers
                ]
                for future in as_completed(futures):
                    page_number, text, error = future.result()
                    if error:
                        pages[page_number - 1] = (page_number, "OCR non eseguito", "")
                        warnings.append(f"{pdf_path.name}, pagina {page_number}: {error}")
                    else:
                        pages[page_number - 1] = (page_number, "OCR tesseract", text)

    output_path = output_path_for(pdf_path, output_dir)
    write_markdown(output_path, pdf_path.name, [page for page in pages if page is not None])
    return output_path, used_ocr, warnings


def prepare_plain_text(path: Path, output_dir: Path) -> tuple[Path, bool, list[str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    output_path = output_path_for(path, output_dir)
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

    output_path = output_path_for(path, output_dir)
    write_markdown(output_path, path.name, [(None, method, text)])
    return output_path, used_ocr, warnings


def iter_materials(source_dir: Path) -> list[Path]:
    ignored_dirs = {DEFAULT_OUTPUT_DIR.name}
    return [
        path
        for path in sorted(source_dir.iterdir())
        if path.is_file() and path.parent.name not in ignored_dirs and path.name != ".gitkeep"
    ]


def prepare_material(
    path: Path,
    output_dir: Path,
    language: str,
    dpi: int,
    ocr_workers: int,
    force: bool,
    min_cached_chars: int,
) -> tuple[Path, bool, list[str]]:
    output_path = output_path_for(path, output_dir)
    if not force and cached_output_is_usable(path, output_path, min_cached_chars):
        return output_path, False, []

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return prepare_pdf(path, output_dir, language, dpi, ocr_workers)
    if suffix in {".txt", ".md"}:
        return prepare_plain_text(path, output_dir)
    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}:
        return prepare_image(path, output_dir, language)

    output_path = output_path_for(path, output_dir)
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
    parser.add_argument(
        "--ocr-workers",
        type=int,
        default=DEFAULT_OCR_WORKERS,
        help="Numero di pagine OCR da elaborare in parallelo per ciascun PDF.",
    )
    parser.add_argument(
        "--min-cached-chars",
        type=int,
        default=MIN_CACHED_TEXT_CHARS,
        help="Numero minimo di caratteri reali per riusare un Markdown già estratto.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rigenera gli output anche quando esistono già file Markdown corposi e aggiornati.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not source_dir.exists():
        print(f"Cartella materiali non trovata: {source_dir}", file=sys.stderr)
        return 1
    if args.ocr_workers <= 0:
        print("--ocr-workers deve essere un intero positivo.", file=sys.stderr)
        return 2
    if args.min_cached_chars < 0:
        print("--min-cached-chars non può essere negativo.", file=sys.stderr)
        return 2

    output_dir.mkdir(parents=True, exist_ok=True)
    materials = iter_materials(source_dir)

    if not materials:
        print(f"Nessun materiale trovato in {source_dir}.")
        return 0

    all_warnings: list[str] = []
    ocr_count = 0

    for material in materials:
        try:
            output_path, used_ocr, warnings = prepare_material(
                material,
                output_dir,
                args.language,
                args.dpi,
                args.ocr_workers,
                args.force,
                args.min_cached_chars,
            )
        except (PreparationError, subprocess.CalledProcessError) as error:
            all_warnings.append(f"{material.name}: {error}")
            continue

        if used_ocr:
            ocr_count += 1
        all_warnings.extend(warnings)
        action = "Creato" if used_ocr or warnings or args.force else "Pronto"
        print(f"{action} {output_path.relative_to(ROOT)}")

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
