from pathlib import Path
from html import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

REPORT_DIR = Path(__file__).resolve().parents[2] / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def generate_report(results, total_marks, max_marks, report_id):
    report_path = REPORT_DIR / f"{report_id}.pdf"

    document = SimpleDocTemplate(
        str(report_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        textColor=colors.HexColor("#173B4D"),
        fontSize=22,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="QuestionHeading",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#168B82"),
        spaceBefore=14,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="SmallBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
    ))

    percentage = (total_marks / max_marks * 100) if max_marks else 0

    if percentage >= 90:
        grade = "A"
    elif percentage >= 80:
        grade = "B"
    elif percentage >= 70:
        grade = "C"
    elif percentage >= 60:
        grade = "D"
    else:
        grade = "F"

    story = [
        Paragraph("Assessiva", styles["ReportTitle"]),
        Paragraph("Multilingual AI Essay Evaluation Report", styles["Heading2"]),
        Spacer(1, 10),
    ]

    summary_data = [
        ["Total Marks", "Percentage", "Grade"],
        [
            f"{total_marks} / {max_marks}",
            f"{percentage:.1f}%",
            grade,
        ],
    ]

    summary_table = Table(summary_data, colWidths=[55 * mm] * 3)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173B4D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#EAF3EF")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#173B4D")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("PADDING", (0, 0), (-1, -1), 10),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D5E2DE")),
    ]))

    story.extend([summary_table, Spacer(1, 15)])

    story.append(Paragraph("Question-wise Evaluation", styles["Heading1"]))

    for item in results:
        story.append(Paragraph(
            f"Question {item['question']}",
            styles["QuestionHeading"],
        ))
        story.append(Paragraph(
            f"<b>Marks:</b> {item['marks']} / 10",
            styles["SmallBody"],
        ))
        story.append(Paragraph(
            f"<b>Similarity:</b> {item['similarity']}%",
            styles["SmallBody"],
        ))
        story.append(Paragraph(
            f"<b>Feedback:</b> {escape(item['feedback'])}",
            styles["SmallBody"],
        ))
        story.append(Spacer(1, 5))

    story.extend([
        Spacer(1, 15),
        Paragraph(
            "<b>Important:</b> This report contains preliminary AI-assisted "
            "scores based on semantic similarity. Similarity is not proof of "
            "factual correctness. A teacher should review the answers and "
            "final marks before using this report for formal assessment.",
            styles["SmallBody"],
        ),
    ])

    document.build(story)
    return report_path