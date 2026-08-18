#!/usr/bin/env python3
"""Create a public-safe IRI packet while preserving document structure.

The input is intentionally outside the repository.  This tool keeps semantic
contradictions and equality relationships, but replaces identifiers, names,
titles, dates, amounts, URLs, hashes and attachment filenames with stable
placeholders.  It never writes the replacement map.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


def _label(index: int) -> str:
    out = ""
    while True:
        out = chr(65 + index % 26) + out
        index = index // 26 - 1
        if index < 0:
            return out


class Redactor:
    def __init__(self) -> None:
        self.maps: dict[str, dict[str, str]] = {}

    def token(self, category: str, value: str) -> str:
        values = self.maps.setdefault(category, {})
        if value not in values:
            values[value] = f"<{category}_{_label(len(values))}>"
        return values[value]

    def replace(self, text: str, pattern: str, category: str, flags: int = 0) -> str:
        regex = re.compile(pattern, flags)
        return regex.sub(lambda m: self.token(category, m.group(0)), text)


DATE = r"(?<!\w)(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}[./-]\d{1,2}[./-]\d{1,2}|\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{2,4})(?!\w)"
URL = r"https?://[^\s)\]>]+"
EMAIL = r"[\w.+-]+@[\w.-]+\.[A-Za-zА-Яа-я]{2,}"
HASH = r"(?<![A-Za-z0-9])[0-9a-fA-F]{32,}(?![A-Za-z0-9])"
PHONE = r"(?<!\w)(?:\+?\d[\d ()-]{8,}\d)(?!\w)"
FILENAME = re.compile(r"(?<![\w/])[^\s/<>]+\.(?:pdf|png|jpg|jpeg|docx|xlsx|mp4|zip)(?!\w)")

COMMON_CAPITALS = {
    "АНО", "ИРИ", "РФ", "России", "Российской", "Россия", "Проект", "Игра",
    "Игры", "Демонстрационная", "Версия", "Компьютер", "Москва", "Page",
    "Inline", "Content", "No", "ГАРАНТИЙНОЕ", "РЕКОМЕНДАТЕЛЬНОЕ", "ПИСЬМО",
    "КОНЦЕПТ", "Документ", "Участник", "Заявка", "ФИО", "Field", "Path",
    "MIME", "Bytes", "SHA", "File", "JSON", "Lead", "Unity", "Developer",
    "Product", "Director", "Selectel", "Palantir", "Maven", "IOS", "Android",
    "XCOM", "StarCraft", "Warcraft", "Civilisation", "RTS", "LLM", "GPU",
    "Команда", "Менее", "Необходимо", "Поле", "Требование", "Справка",
    "Отсутствует", "Заявитель", "Руководитель", "Ключевой", "Ключевые",
    "Член", "Опыт", "Образование", "Документы", "Документ", "Дата", "Сумма",
    "Вариант", "Формат", "Платформа", "Жанр", "Сеттинг", "Описание", "Цели",
    "Обоснование", "Социальный", "Эффект", "Игрок", "Для", "Это", "Такой",
    "В»,", "В", "С", "На", "По", "От", "Из", "И", "А", "Но", "Не",
}
STRUCTURAL_HEADINGS = {
    "Текущий снимок сайта", "Metadata", "О проекте", "Вложения", "Page",
    "Inline Content", "No extractable text", "Неизвестный раздел",
}
PERSON_CONTEXT = re.compile(
    r"(?i)(?:фио|руководител|участник|работодател|работал|рекоменд|подпис|директор|"
    r"от\s+[А-ЯЁ]|с\s+[А-ЯЁ]|выдан|генеральн|правообладател)"
)
FULL_NAME = re.compile(
    r"(?<!\w)[А-ЯЁ][а-яё-]+\s+[А-ЯЁ][а-яё-]+(?:\s+[А-ЯЁ][а-яё-]+)?(?!\w)"
)
LATIN_ENTITY = re.compile(r"(?<!\w)[A-Z][A-Za-z0-9-]{2,}(?!\w)")


def redact(text: str) -> str:
    r = Redactor()
    text = text.replace("\r\n", "\n")
    # Build a transient token map from context-bearing lines.  The source
    # values never leave this process and the map is deliberately not written.
    transient: dict[str, str] = {}
    for source_line in text.splitlines():
        heading = re.match(r"^#{1,6}\s+(.+)$", source_line)
        context = PERSON_CONTEXT.search(source_line) or re.search(
            r"(?i)(?:проект|игр(?:а|ы|у|е)|назван(?:ие|ием))", source_line
        )
        if heading and "`" not in heading.group(1):
            words = re.findall(r"[A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё_-]{2,}", heading.group(1))
            for word in words:
                if word not in COMMON_CAPITALS and word.casefold() not in {x.casefold() for x in STRUCTURAL_HEADINGS}:
                    transient.setdefault(word.casefold(), r.token("DOCUMENT", word))
        if context:
            words = re.findall(r"[A-ZА-ЯЁ][A-Za-zА-Яа-яЁё-]{2,}", source_line)
            for word in words:
                if word not in COMMON_CAPITALS:
                    transient.setdefault(word.casefold(), r.token("PERSON", word))
    # Cover full-name forms that occur in signatures or standalone document
    # lines without a nearby role cue.
    for candidate in set(FULL_NAME.findall(text)):
        transient.setdefault(candidate.casefold(), r.token("PERSON", candidate))
    for word in sorted(transient, key=len, reverse=True):
        text = re.sub(r"(?<!\w)" + re.escape(word) + r"(?!\w)", transient[word], text, flags=re.IGNORECASE)
    text = r.replace(text, URL, "URL")
    text = r.replace(text, EMAIL, "EMAIL")
    text = r.replace(text, PHONE, "PHONE")
    text = r.replace(text, HASH, "HASH")
    text = r.replace(text, DATE, "DATE", re.IGNORECASE)

    lines: list[str] = []
    in_project_name = False
    for line in text.splitlines():
        heading = re.match(r"^(#{1,6}\s+)(.+)$", line)
        if (heading and "`" not in heading.group(2)
                and heading.group(2).strip() not in STRUCTURAL_HEADINGS
                and re.search(r"[A-Za-z_.-]", heading.group(2))):
            lines.append(heading.group(1) + r.token("DOCUMENT", heading.group(2).strip()))
            continue
        if re.match(r"^###\s+`?name`?\s*$", line, re.IGNORECASE):
            in_project_name = True
            lines.append(line)
            continue
        if in_project_name and line.strip() and not line.lstrip().startswith("<!--"):
            lines.append(r.token("PROJECT", line.strip()))
            in_project_name = False
            continue

        line = re.sub(
            r"(?i)((?:проект|игр(?:а|ы|у|е)|назван(?:ие|ием)|должност(?:ь|и)|"
            r"компани(?:я|и)|работодател(?:ь|я)|студи(?:я|и)|издател(?:ь|я))\s*[«\"“])"
            r"[^»\"”]+([»\"”])",
            lambda m: m.group(1) + r.token("ENTITY", m.group(0)) + m.group(2),
            line,
        )
        line = FILENAME.sub(
            lambda m: r.token("FILE", m.group(0).rsplit(".", 1)[0]) + "." + m.group(0).rsplit(".", 1)[1],
            line,
        )
        if PERSON_CONTEXT.search(line):
            line = FULL_NAME.sub(lambda m: r.token("PERSON", m.group(0)), line)
            line = LATIN_ENTITY.sub(
                lambda m: m.group(0) if m.group(0) in COMMON_CAPITALS else r.token("ENTITY", m.group(0)),
                line,
            )
            line = re.sub(
                r"(?<!\w)[А-ЯЁ][а-яё-]{2,}(?!\w)",
                lambda m: m.group(0) if m.group(0) in COMMON_CAPITALS else r.token("PERSON", m.group(0)),
                line,
            )
        if re.fullmatch(
            r"\s*[А-ЯЁ][а-яё-]+\s+[А-ЯЁ][а-яё-]+(?:\s+[А-ЯЁ][а-яё-]+)?\s*",
            line,
        ):
            line = FULL_NAME.sub(lambda m: r.token("PERSON", m.group(0)), line)
        lines.append(line)

    text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    # Remove every remaining numeric literal.  Stable alphabetic placeholders
    # preserve equality/inequality without exposing dates, amounts or IDs.
    text = re.sub(r"\d+", lambda m: r.token("NUMBER", m.group(0)), text)
    # A final conservative pass catches all-caps project labels and personal
    # names that occur in prose without an explicit "ФИО" cue.
    def redact_capitalized(match: re.Match[str]) -> str:
        value = match.group(0)
        if value in COMMON_CAPITALS:
            return value
        if value.isupper() or value.endswith(("ович", "евич", "овна", "евна", "овичу", "евичу")):
            return r.token("ENTITY", value)
        return value

    text = re.sub(r"(?<!\w)[А-ЯЁ][А-ЯЁа-яё-]{2,}(?!\w)", redact_capitalized, text)
    return text


def audit(text: str) -> list[str]:
    checks = [
        (DATE, "date"),
        (URL, "URL"),
        (EMAIL, "email"),
        (PHONE, "phone"),
        (HASH, "hash"),
        (r"\d+", "numeric literal"),
    ]
    return [label for pattern, label in checks if re.search(pattern, text, re.IGNORECASE)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    redacted = redact(args.input.read_text(encoding="utf-8"))
    leaks = audit(redacted)
    if leaks:
        raise SystemExit("redaction audit failed: " + ", ".join(leaks))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(redacted, encoding="utf-8")
    print(f"wrote redacted packet: {args.output} ({len(redacted)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
