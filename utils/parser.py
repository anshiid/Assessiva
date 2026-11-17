
import re


def parse_sections(text):
    """
    Split a document into numbered sections such as Q1, Q2, Q3.
    Supports headings like:
        Q1. Climate Change
        Q1 - Climate Change
        Q1: Climate Change
        1. Climate Change
    """

    pattern = re.compile(
        r"(?im)^\s*(?:Q\s*)?(\d{1,2})\s*[.)\-–:]\s*(.*)$"
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

        content = text[start:end].strip()

        if content:
            sections[question_number] = content

    return sections


def parse_question_paper(text):
    """Extract numbered questions from the question paper."""
    return parse_sections(text)


def parse_reference_sheet(text):
    """Extract teacher reference answers by question number."""
    return parse_sections(text)


def parse_student_answers(text):
    """Extract student answers by question number."""
    return parse_sections(text)
