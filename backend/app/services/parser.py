
import re


def parse_sections(text):
    """
    Extract numbered sections from typed or OCR-extracted documents.

    Supports:
    Q1. Climate Change
    Q1 - Climate Change
    Q1: Climate Change
    Question 1: Climate Change
    1. Climate Change
    """

    if not text or not text.strip():
        return {}

    # Normalize OCR line endings and whitespace.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Handwriting OCR can mistake the "1" in a Q1 heading for l, I, or |.
    text = re.sub(
        r"(?im)^(\s*Q(?:UESTION)?\s*)[lI|](?=\s*(?:[.)\-–:]|\s))",
        r"\g<1>1",
        text,
    )

    pattern = re.compile(
        r"(?im)^\s*(?:Q(?:UESTION)?\s*)?(\d{1,2})"
        r"\s*(?:[.)\-–:]\s*|\s+)(.*?)\s*$"
    )

    matches = list(pattern.finditer(text))
    sections = {}

    for index, match in enumerate(matches):
        question_number = int(match.group(1))

        start = match.end()

        if index + 1 < len(matches):
            end = matches[index + 1].start()
        else:
            end = len(text)

        heading_content = match.group(2).strip()
        remaining_content = text[start:end].strip()

        content = "\n".join(
            part for part in [heading_content, remaining_content] if part
        )

        if content:
            sections[question_number] = content

    return sections


def parse_question_paper(text):
    return parse_sections(text)


def parse_reference_sheet(text):
    return parse_sections(text)


def parse_student_answers(text):
    return parse_sections(text)
