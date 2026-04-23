#!/usr/bin/env python3

import json
import math
import random
import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"


class ConfigError(Exception):
    pass


@dataclass
class MultipleChoiceQuestion:
    question_id: str
    topic: str
    question: str
    options: list[dict[str, str]]
    correct_option: str
    source: str
    explanation: str
    difficulty: str


@dataclass
class RenderedMultipleChoiceQuestion:
    question_id: str
    topic: str
    question: str
    options: list[dict[str, str]]
    correct_option_label: str
    source: str
    explanation: str


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    return path if path.is_absolute() else ROOT / path


def read_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise ConfigError("config.json non trovato.")
    config = load_json(CONFIG_PATH)
    if not isinstance(config, dict):
        raise ConfigError("config.json deve contenere un oggetto JSON.")
    return config


def derive_number_of_versions(number_of_students: int) -> int:
    return max(1, math.ceil(number_of_students / 3))


def validate_generation_counts(config: dict[str, Any]) -> None:
    students = int(config.get("number_of_students", 0))
    if students <= 0:
        raise ConfigError("number_of_students deve essere un intero positivo.")
    versions = config.get("number_of_versions")
    if versions in (None, ""):
        config["number_of_versions"] = derive_number_of_versions(students)
        versions = config["number_of_versions"]
    else:
        versions = int(versions)
        config["number_of_versions"] = versions
    if versions <= 0:
        raise ConfigError("number_of_versions deve essere un intero positivo.")
    if versions > students:
        raise ConfigError("number_of_versions non puo' essere maggiore di number_of_students.")


def normalize_multiple_choice_scoring(config: dict[str, Any]) -> None:
    mc_config = config.get("multiple_choice", {})
    if not mc_config.get("enabled"):
        return

    points_correct = float(mc_config["points_correct"])
    if points_correct <= 0:
        raise ConfigError("points_correct deve essere positivo.")

    mc_config["points_wrong"] = -points_correct / 2


def collect_json_items(source_dir: Path) -> dict[str, dict[str, Any]]:
    items: dict[str, dict[str, Any]] = {}
    for path in sorted(source_dir.glob("*.json")):
        data = load_json(path)
        item_id = data.get("id")
        if not item_id:
            raise ConfigError(f"{path} non contiene il campo 'id'.")
        items[item_id] = data
    return items


def ensure_solution_blocks(item: dict[str, Any], path_hint: str) -> None:
    solution = item.get("solution")
    if not isinstance(solution, dict):
        raise ConfigError(f"{path_hint}: solution mancante o non valida.")
    blocks = solution.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        raise ConfigError(f"{path_hint}: solution.blocks deve essere una lista non vuota.")


def prepare_selected_items(config_section: dict[str, Any]) -> list[dict[str, Any]]:
    if not config_section.get("enabled"):
        return []

    source_dir = resolve_path(config_section["source_dir"])
    if not source_dir.exists():
        raise ConfigError(f"Cartella non trovata: {source_dir}")

    pool = collect_json_items(source_dir)
    selected: list[dict[str, Any]] = []
    for item_id in config_section.get("include_ids", []):
        if item_id not in pool:
            raise ConfigError(f"ID '{item_id}' non trovato in {source_dir}")
        item = deepcopy(pool[item_id])
        ensure_solution_blocks(item, str(source_dir / f"{item_id}.json"))
        selected.append(item)
    return selected


def load_multiple_choice_questions(json_path: Path) -> list[MultipleChoiceQuestion]:
    payload = load_json(json_path)
    questions = payload.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ConfigError(f"Il file {json_path} deve contenere una lista 'questions' non vuota.")

    result: list[MultipleChoiceQuestion] = []
    for item in questions:
        if not isinstance(item, dict):
            raise ConfigError(f"Voce non valida in {json_path}: ogni domanda deve essere un oggetto JSON.")

        options = item.get("options")
        if not isinstance(options, list) or len(options) != 4:
            raise ConfigError(
                f"La domanda {item.get('id')} deve avere esattamente 4 opzioni in 'options'."
            )

        normalized_options = []
        correct_label = ""
        correct_count = 0
        for option in options:
            option_id = str(option.get("id", "")).strip().upper()
            option_text = str(option.get("text", "")).strip()
            is_correct = bool(option.get("is_correct"))

            if option_id not in {"A", "B", "C", "D"}:
                raise ConfigError(
                    f"La domanda {item.get('id')} contiene un'opzione con id non valido: {option_id}"
                )
            if not option_text:
                raise ConfigError(f"La domanda {item.get('id')} contiene un'opzione senza testo.")

            if is_correct:
                correct_label = option_id
                correct_count += 1

            normalized_options.append({"original_label": option_id, "text": option_text})

        if correct_count != 1:
            raise ConfigError(
                f"La domanda {item.get('id')} deve avere una e una sola opzione corretta."
            )

        result.append(
            MultipleChoiceQuestion(
                question_id=str(item.get("id", "")).strip(),
                topic=str(item.get("topic", "")).strip(),
                question=str(item.get("prompt", "")).strip(),
                options=normalized_options,
                correct_option=correct_label,
                source=str(item.get("source", "Fonte non specificata")).strip(),
                explanation=str(item.get("explanation", "")).strip(),
                difficulty=str(item.get("difficulty", "")).strip(),
            )
        )
    return result


def validate_points(config: dict[str, Any], open_items: list[dict[str, Any]], exercise_items: list[dict[str, Any]]) -> None:
    total = 0.0
    max_points = float(config["max_points"])

    mc_config = config["multiple_choice"]
    if mc_config.get("enabled"):
        total += float(mc_config["questions_per_exam"]) * float(mc_config["points_correct"])

    if config["open_questions"].get("enabled"):
        total += sum(float(item["points"]) for item in open_items)

    if config["practical_exercises"].get("enabled"):
        total += sum(float(item["points"]) for item in exercise_items)

    if total > max_points + 1e-9:
        raise ConfigError(
            f"Punteggio totale attivato ({total}) superiore al massimo consentito ({max_points})."
        )


def scramble_multiple_choice(
    questions: list[MultipleChoiceQuestion],
    count: int,
    shuffle_questions: bool,
    shuffle_options: bool,
    rng: random.Random,
) -> list[RenderedMultipleChoiceQuestion]:
    if len(questions) < count:
        raise ConfigError(f"Domande multiple insufficienti: richieste {count}, disponibili {len(questions)}.")

    chosen = rng.sample(questions, count) if shuffle_questions else questions[:count]
    labels = ["A", "B", "C", "D"]
    result: list[RenderedMultipleChoiceQuestion] = []

    for question in chosen:
        options = deepcopy(question.options)
        if shuffle_options:
            rng.shuffle(options)

        rendered_options = []
        correct_label = ""
        for index, option in enumerate(options):
            label = labels[index]
            rendered_options.append({"label": label, "text": option["text"]})
            if option["original_label"] == question.correct_option:
                correct_label = label

        result.append(
            RenderedMultipleChoiceQuestion(
                question_id=question.question_id,
                topic=question.topic,
                question=question.question,
                options=rendered_options,
                correct_option_label=correct_label,
                source=question.source,
                explanation=question.explanation,
            )
        )
    return result


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CenteredTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=18,
            leading=22,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading2"],
            alignment=TA_LEFT,
            fontSize=13,
            leading=16,
            spaceBefore=8,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Question",
            parent=styles["BodyText"],
            fontSize=10.5,
            leading=14,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="MultipleChoiceQuestion",
            parent=styles["Question"],
            leading=12,
            spaceAfter=1,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Option",
            parent=styles["BodyText"],
            fontSize=10,
            leading=12,
            leftIndent=12 * mm,
            firstLineIndent=0,
            spaceBefore=0,
            spaceAfter=0,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["BodyText"],
            fontSize=9,
            leading=12,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Instruction",
            parent=styles["BodyText"],
            fontSize=10,
            leading=13,
            fontName="Helvetica-Oblique",
            italic=True,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SolutionSource",
            parent=styles["BodyText"],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#555555"),
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableCell",
            parent=styles["BodyText"],
            fontSize=8,
            leading=10,
            spaceAfter=0,
        )
    )
    return styles


def scale_image(path: Path, max_width: float, max_height: float) -> Image:
    image = Image(str(path))
    width = image.imageWidth
    height = image.imageHeight
    ratio = min(max_width / width, max_height / height)
    image.drawWidth = width * ratio
    image.drawHeight = height * ratio
    return image


def build_student_info_table(config: dict[str, Any]) -> Table:
    cells = []
    info = config["student_info"]
    if info.get("show_name"):
        cells.extend([("Alunno/a", 22 * mm), ("", 62 * mm)])
    if info.get("show_class"):
        cells.extend([("Classe", 18 * mm), ("", 24 * mm)])
    if info.get("show_date"):
        cells.extend([("Data", 16 * mm), ("", 38 * mm)])

    if not cells:
        cells = [
            ("Alunno/a", 22 * mm),
            ("", 62 * mm),
            ("Classe", 18 * mm),
            ("", 24 * mm),
            ("Data", 16 * mm),
            ("", 38 * mm),
        ]

    fields = [value for value, _ in cells]
    widths = [width for _, width in cells]

    table = Table([fields], colWidths=widths, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.9, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def get_enabled_evaluation_grid_targets(config: dict[str, Any]) -> set[str]:
    enabled_targets: set[str] = set()
    if config.get("multiple_choice", {}).get("enabled"):
        enabled_targets.add("multiple_choice")
    if config.get("open_questions", {}).get("enabled"):
        enabled_targets.add("open_questions")
    if config.get("practical_exercises", {}).get("enabled"):
        enabled_targets.add("practical_exercises")
    return enabled_targets


def infer_grid_section_target(section: dict[str, Any]) -> str | None:
    applies_to = str(section.get("applies_to", "")).strip()
    if applies_to:
        return applies_to

    label = str(section.get("label", "")).strip().lower()
    if "scelta multipla" in label or "quiz" in label:
        return "multiple_choice"
    if "aperta" in label or "teorica" in label:
        return "open_questions"
    if "esercizio" in label:
        return "practical_exercises"
    return None


def build_evaluation_grid(path: Path, config: dict[str, Any]) -> Table:
    grid = load_json(path)
    base_styles = build_styles()
    sections = grid.get("sections")
    if not isinstance(sections, list) or not sections:
        raise ConfigError(f"Griglia di valutazione non valida: {path}")

    enabled_targets = get_enabled_evaluation_grid_targets(config)
    filtered_sections = []
    for section in sections:
        target = infer_grid_section_target(section)
        if target is None or target in enabled_targets:
            filtered_sections.append(section)

    if not filtered_sections:
        raise ConfigError(
            "Nessuna sezione della griglia di valutazione corrisponde alle parti abilitate della verifica."
        )

    label_style = ParagraphStyle(
        name="GridLabel",
        parent=base_styles["TableCell"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=10,
    )
    checklist_style = ParagraphStyle(
        name="GridChecklist",
        parent=base_styles["TableCell"],
        fontSize=8,
        leading=10,
    )
    percentage_style = ParagraphStyle(
        name="GridPercentage",
        parent=base_styles["TableCell"],
        fontSize=8,
        leading=10,
    )

    table_rows = []
    for section in filtered_sections:
        criteria = section.get("criteria")
        if not isinstance(criteria, list) or not criteria:
            raise ConfigError(f"Sezione griglia non valida in {path}: {section.get('label')}")

        checklist_lines = []
        percentage_lines = []
        for item in criteria:
            text = str(item.get("text", "")).strip()
            percentage = str(item.get("percentage", "")).strip()
            if not text or not percentage:
                raise ConfigError(f"Elemento griglia incompleto in {path}: {item}")
            if item.get("emphasis"):
                checklist_lines.append(f"&#x2610;&nbsp;&nbsp;<b>{text}</b>")
                percentage_lines.append(f"<b>{percentage}</b>")
            else:
                checklist_lines.append(f"&#x2610;&nbsp;&nbsp;{text}")
                percentage_lines.append(percentage)

        table_rows.append(
            [
                Paragraph(str(section.get("label", "")).replace("\n", "<br/>"), label_style),
                Paragraph("<br/>".join(checklist_lines), checklist_style),
                Paragraph("<br/>".join(percentage_lines), percentage_style),
            ]
        )

    table = Table(table_rows, colWidths=[42 * mm, 96 * mm, 42 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.8, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def build_solution_blocks(solution: dict[str, Any], styles) -> list[Any]:
    elements: list[Any] = []
    for block in solution["blocks"]:
        kind = block.get("type", "paragraph")
        if kind == "paragraph":
            elements.append(Paragraph(block["content"], styles["Question"]))
        elif kind == "bullets":
            content = "<br/>".join(f"- {item}" for item in block.get("items", []))
            elements.append(Paragraph(content, styles["Question"]))
        elif kind == "preformatted":
            elements.append(Preformatted(block["content"], styles["Small"]))
        elif kind == "image":
            image_path = resolve_path(block["path"])
            if image_path.exists():
                elements.append(scale_image(image_path, 120 * mm, 70 * mm))
        else:
            raise ConfigError(f"Tipo di blocco soluzione non supportato: {kind}")
    return elements


def build_exam_title(config: dict[str, Any]) -> str:
    subject = str(config.get("subject", "")).strip()
    title = str(config.get("title", "")).strip()

    if subject and title:
        return f"Verifica di {subject} - {title}"
    if title:
        return f"Verifica di {title}"
    if subject:
        return f"Verifica di {subject}"
    return "Verifica"


def add_header(flow: list[Any], config: dict[str, Any], styles, exam_id: str) -> None:
    banner = config.get("banner", {})
    if banner.get("enabled"):
        banner_path = resolve_path(banner["path"])
        if not banner_path.exists():
            raise ConfigError(f"Banner non trovato: {banner_path}")
        flow.append(scale_image(banner_path, 180 * mm, float(banner["max_height_mm"]) * mm))
        flow.append(Spacer(1, 4))

    flow.append(Paragraph(build_exam_title(config), styles["CenteredTitle"]))
    flow.append(build_student_info_table(config))
    flow.append(Spacer(1, 8))

    instructions = config["instructions"]
    if instructions.get("enabled"):
        instruction_text = instructions.get("content", "")
        flow.append(Paragraph(f"<b>{exam_id}</b> - {instruction_text}", styles["Instruction"]))

    evaluation = config["evaluation_grid"]
    if evaluation.get("enabled"):
        flow.append(build_evaluation_grid(resolve_path(evaluation["path"]), config))
        flow.append(Spacer(1, 8))


def add_multiple_choice_section(flow: list[Any], exam: dict[str, Any], config: dict[str, Any], styles) -> None:
    mc = config["multiple_choice"]
    if not mc.get("enabled"):
        return

    score_label = f"(+{float(mc['points_correct']):g} / {float(mc['points_wrong']):g} pt)"
    flow.append(Paragraph(mc["part_title"], styles["SectionTitle"]))
    for index, question in enumerate(exam["multiple_choice"], start=1):
        options_html = "<br/>".join(
            f"{option['label']}. {option['text']}" for option in question.options
        )
        question_block: list[Any] = [
            Paragraph(f"{index}. {question.question} <b>{score_label}</b>", styles["MultipleChoiceQuestion"]),
            Paragraph(options_html, styles["Option"]),
        ]
        question_block.append(Spacer(1, 2))
        flow.append(KeepTogether(question_block))


def add_open_items_section(flow: list[Any], title: str, items: list[dict[str, Any]], styles) -> None:
    if not items:
        return

    flow.append(Paragraph(title, styles["SectionTitle"]))
    for index, item in enumerate(items, start=1):
        flow.append(Paragraph(f"{index}. {item['prompt']} <b>[{float(item['points']):g} pt]</b>", styles["Question"]))
        flow.append(Spacer(1, 3))


def build_exam_flow(exam: dict[str, Any], config: dict[str, Any], styles) -> list[Any]:
    flow: list[Any] = []
    add_header(flow, config, styles, exam["exam_id"])
    add_multiple_choice_section(flow, exam, config, styles)

    if config["open_questions"].get("enabled"):
        add_open_items_section(flow, config["open_questions"]["part_title"], exam["open_questions"], styles)

    if config["practical_exercises"].get("enabled"):
        add_open_items_section(flow, config["practical_exercises"]["part_title"], exam["practical_exercises"], styles)

    return flow


def build_solutions_flow(exams: list[dict[str, Any]], config: dict[str, Any], styles) -> list[Any]:
    flow: list[Any] = [PageBreak(), Paragraph("Soluzioni e Correzione Rapida", styles["CenteredTitle"])]
    if config["multiple_choice"].get("enabled"):
        flow.append(Paragraph("Schema rapido quiz a risposta multipla", styles["SectionTitle"]))
        question_count = len(exams[0]["multiple_choice"]) if exams else 0
        header_group = ["ID"] + [str(index) for index in range(1, question_count + 1)]
        summary_rows: list[list[str]] = []
        for exam in exams:
            answers = [question.correct_option_label for question in exam["multiple_choice"]]
            summary_rows.append([exam["exam_id"]] + answers)

        version_count = len(summary_rows)
        block_count = 3 if version_count >= 15 else 2
        gutter = 6 * mm
        available_width = 180 * mm
        block_width = (available_width - gutter * (block_count - 1)) / block_count
        version_col_width = min(16 * mm, max(11 * mm, block_width * 0.24))
        answer_col_width = (block_width - version_col_width) / max(1, question_count)
        col_widths = [version_col_width] + [answer_col_width] * question_count
        body_font_size = 8 if block_count == 2 else 7
        header_font_size = 8.5 if block_count == 2 else 7.5

        def make_answers_table(rows: list[list[str]]) -> Table:
            table = Table(rows, colWidths=col_widths, hAlign="LEFT")
            last_row = len(rows) - 1
            last_col = len(rows[0]) - 1
            table.setStyle(
                TableStyle(
                    [
                        ("INNERGRID", (0, 0), (-1, -1), 0.8, colors.black),
                        ("LINEABOVE", (0, 0), (last_col, 0), 0.8, colors.black),
                        ("LINEBELOW", (0, last_row), (last_col, last_row), 0.8, colors.black),
                        ("LINEBEFORE", (0, 0), (0, last_row), 0.8, colors.black),
                        ("LINEAFTER", (last_col, 0), (last_col, last_row), 0.8, colors.black),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf4")),
                        ("BACKGROUND", (0, 1), (0, last_row), colors.HexColor("#f2f5fa")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTNAME", (0, 1), (0, last_row), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), header_font_size),
                        ("FONTSIZE", (0, 1), (-1, -1), body_font_size),
                        ("LEADING", (0, 0), (-1, 0), header_font_size + 2),
                        ("LEADING", (0, 1), (-1, -1), body_font_size + 2),
                        ("ALIGN", (0, 0), (0, last_row), "CENTER"),
                        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            return table

        chunk_size = math.ceil(version_count / block_count)
        blocks: list[Table] = []
        for start in range(0, version_count, chunk_size):
            block_rows = [header_group] + summary_rows[start:start + chunk_size]
            blocks.append(make_answers_table(block_rows))

        if len(blocks) < block_count:
            filler = Spacer(1, 1)
            blocks.extend([filler] * (block_count - len(blocks)))
        container = Table([blocks], colWidths=[block_width] * block_count, hAlign="LEFT")
        container.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("LEFTPADDING", (1, 0), (-1, 0), gutter),
                    ("LINEBEFORE", (0, 0), (-1, -1), 0, colors.white),
                    ("LINEAFTER", (0, 0), (-1, -1), 0, colors.white),
                    ("LINEABOVE", (0, 0), (-1, -1), 0, colors.white),
                    ("LINEBELOW", (0, 0), (-1, -1), 0, colors.white),
                ]
            )
        )
        flow.append(container)
        flow.append(Spacer(1, 8))

    reference_exam = exams[0]
    for label, items in (("Domande aperte", reference_exam["open_questions"]), ("Esercizi", reference_exam["practical_exercises"])):
        if not items:
            continue
        flow.append(Paragraph(label, styles["SectionTitle"]))
        for index, item in enumerate(items, start=1):
            flow.append(Paragraph(f"{index}. {item['prompt']} <b>[{float(item['points']):g} pt]</b>", styles["Question"]))
            flow.extend(build_solution_blocks(item["solution"], styles))
            flow.append(Paragraph(f"Fonte: {item['solution'].get('source', 'Fonte non specificata')}", styles["SolutionSource"]))
        flow.append(Spacer(1, 8))

    return flow


def build_exam_versions(config: dict[str, Any], open_items: list[dict[str, Any]], exercise_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rng = random.Random(config.get("random_seed", 0))
    exams: list[dict[str, Any]] = []
    mc_questions: list[MultipleChoiceQuestion] = []

    if config["multiple_choice"].get("enabled"):
        mc_questions = load_multiple_choice_questions(resolve_path(config["multiple_choice"]["source_file"]))

    total_versions = int(config["number_of_versions"])
    for index in range(total_versions):
        exam = {
            "exam_id": f"V{index + 1}",
            "multiple_choice": [],
            "open_questions": deepcopy(open_items),
            "practical_exercises": deepcopy(exercise_items),
        }
        if config["multiple_choice"].get("enabled"):
            exam["multiple_choice"] = scramble_multiple_choice(
                mc_questions,
                int(config["multiple_choice"]["questions_per_exam"]),
                bool(config["multiple_choice"].get("shuffle_questions", True)),
                bool(config["multiple_choice"].get("shuffle_options", True)),
                rng,
            )
        exams.append(exam)

    return exams


def build_exam_copies(exams: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    total_students = int(config["number_of_students"])
    total_versions = len(exams)
    base_count = total_students // total_versions
    remainder = total_students % total_versions

    version_buckets: list[list[dict[str, Any]]] = []
    for index, exam in enumerate(exams):
        copies_for_version = base_count + (1 if index < remainder else 0)
        version_buckets.append([exam] * copies_for_version)

    copies: list[dict[str, Any]] = []
    while any(version_buckets):
        for bucket in version_buckets:
            if bucket:
                copies.append(bucket.pop(0))
    return copies


def build_document(config: dict[str, Any], exams: list[dict[str, Any]], copies: list[dict[str, Any]]) -> Path:
    output_path = resolve_path(config["output_pdf"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=build_exam_title(config),
    )

    styles = build_styles()
    flow: list[Any] = []
    for index, exam in enumerate(copies):
        if index:
            flow.append(PageBreak())
        flow.extend(build_exam_flow(exam, config, styles))

    flow.extend(build_solutions_flow(exams, config, styles))
    doc.build(flow)
    return output_path


def print_summary(config: dict[str, Any], exams: list[dict[str, Any]], output_path: Path) -> None:
    mc_points = 0.0
    if config["multiple_choice"].get("enabled"):
        mc_points = float(config["multiple_choice"]["questions_per_exam"]) * float(config["multiple_choice"]["points_correct"])
    open_points = sum(float(item["points"]) for item in exams[0]["open_questions"])
    exercise_points = sum(float(item["points"]) for item in exams[0]["practical_exercises"])
    total = mc_points + open_points + exercise_points
    total_students = int(config["number_of_students"])
    total_versions = int(config["number_of_versions"])
    base_count = total_students // total_versions
    remainder = total_students % total_versions
    distribution = ", ".join(
        f"V{index + 1}={base_count + (1 if index < remainder else 0)}"
        for index in range(total_versions)
    )

    print(f"PDF generato: {output_path}")
    print(f"Alunni: {total_students}")
    print(f"Versioni generate: {len(exams)}")
    print(f"Distribuzione copie: {distribution}")
    print(f"Punteggio massimo configurato: {float(config['max_points']):g}")
    print(f"Punteggio totale attivo: {total:g}")


def main() -> int:
    try:
        config = read_config()
        validate_generation_counts(config)
        normalize_multiple_choice_scoring(config)
        open_items = prepare_selected_items(config["open_questions"])
        exercise_items = prepare_selected_items(config["practical_exercises"])
        validate_points(config, open_items, exercise_items)
        exams = build_exam_versions(config, open_items, exercise_items)
        copies = build_exam_copies(exams, config)
        output_path = build_document(config, exams, copies)
        print_summary(config, exams, output_path)
        return 0
    except ConfigError as exc:
        print(f"Errore di configurazione: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Errore inatteso: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
