#!/usr/bin/env python3

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
ARCHIVES_DIR = ROOT / "archives"
WORK_DIRS = [
    "teaching-materials",
    "multiple-choice-question",
    "open-question",
    "practical-exercises",
    "output",
]


class ArchiveError(Exception):
    pass


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    return path if path.is_absolute() else ROOT / path


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "verifica"


def unique_archive_dir(base_dir: Path) -> Path:
    if not base_dir.exists():
        return base_dir

    counter = 2
    while True:
        candidate = base_dir.with_name(f"{base_dir.name}-{counter}")
        if not candidate.exists():
            return candidate
        counter += 1


def copy_file_if_exists(source: Path, destination: Path, archive_dir: Path, copied: list[str]) -> None:
    if not source.exists() or not source.is_file():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    copied.append(str(destination.relative_to(archive_dir)))


def copy_tree_contents(source: Path, destination: Path, archive_dir: Path, copied: list[str]) -> None:
    if not source.exists() or not source.is_dir():
        return

    for item in sorted(source.rglob("*")):
        if not item.is_file() or item.name == ".gitkeep":
            continue
        relative_path = item.relative_to(source)
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        copied.append(str(target.relative_to(archive_dir)))


def remove_work_files() -> None:
    for dir_name in WORK_DIRS:
        directory = ROOT / dir_name
        if not directory.exists():
            continue
        for item in directory.iterdir():
            if item.name == ".gitkeep":
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()


def build_archive(config: dict[str, Any], reset_current: bool) -> Path:
    title = str(config.get("title") or "verifica")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive_dir = unique_archive_dir(ARCHIVES_DIR / f"{timestamp}-{slugify(title)}")
    archive_dir.mkdir(parents=True)

    copied: list[str] = []

    copy_file_if_exists(CONFIG_PATH, archive_dir / "config.json", archive_dir, copied)
    copy_file_if_exists(ROOT / "prompt.md", archive_dir / "prompt.md", archive_dir, copied)

    for dir_name in WORK_DIRS:
        copy_tree_contents(ROOT / dir_name, archive_dir / dir_name, archive_dir, copied)

    evaluation_path = config.get("evaluation_grid", {}).get("path")
    if evaluation_path:
        source = resolve_path(str(evaluation_path))
        copy_file_if_exists(source, archive_dir / str(evaluation_path), archive_dir, copied)

    banner = config.get("banner", {})
    if banner.get("enabled") and banner.get("path"):
        source = resolve_path(str(banner["path"]))
        copy_file_if_exists(source, archive_dir / str(banner["path"]), archive_dir, copied)

    manifest = {
        "archived_at": datetime.now().isoformat(timespec="seconds"),
        "title": config.get("title"),
        "subject": config.get("subject"),
        "output_pdf": config.get("output_pdf"),
        "number_of_students": config.get("number_of_students"),
        "number_of_versions": config.get("number_of_versions"),
        "random_seed": config.get("random_seed"),
        "reset_current": reset_current,
        "copied_files": copied,
    }
    with (archive_dir / "manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    if reset_current:
        remove_work_files()

    return archive_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Archivia la verifica corrente prima di prepararne una nuova."
    )
    parser.add_argument(
        "--reset-current",
        action="store_true",
        help="dopo l'archiviazione svuota materiali, domande, esercizi e output correnti",
    )
    return parser.parse_args()


def main() -> int:
    try:
        if not CONFIG_PATH.exists():
            raise ArchiveError("config.json non trovato.")
        config = load_json(CONFIG_PATH)
        if not isinstance(config, dict):
            raise ArchiveError("config.json deve contenere un oggetto JSON.")

        args = parse_args()
        archive_dir = build_archive(config, args.reset_current)
        print(f"Archivio creato: {archive_dir}")
        if args.reset_current:
            print("Cartelle operative svuotate.")
        return 0
    except ArchiveError as exc:
        print(f"Errore di archiviazione: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Errore inatteso: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
