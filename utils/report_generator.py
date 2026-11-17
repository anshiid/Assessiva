
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


def generate_report(results, total_marks, output_path="reports/Assessiva_Report.pdf"):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("ASSESSIVA AI", styles["Title"]))
    story.append(Paragraph("Multilingual AI Essay Evaluation Report", styles["Heading2"]))
    story.append(Spacer(1, 15))

    grade = (
        "A" if total_marks >= 27 else
        "B" if total_marks >= 24 else
        "C" if total_marks >= 21 else
        "D" if total_marks >= 18 else
        "F"
    )

    story.append(Paragraph(
        f"<b>Total Score:</b> {total_marks} / 30",
        styles["Heading2"]
    ))
    story.append(Paragraph(
        f"<b>Grade:</b> {grade}",
        styles["Heading2"]
    ))
    story.append(Spacer(1, 15))

    data = [["Question", "Similarity", "Marks", "Feedback"]]

    for result in results:
        feedback = result["feedback"].replace("&", "&amp;")
        data.append([
            f"Q{result['question']}",
            f"{result['similarity']}%",
            f"{result['marks']}/10",
            Paragraph(feedback, styles["BodyText"])
        ])

    table = Table(data, colWidths=[2 * cm, 2.5 * cm, 2 * cm, 9 * cm])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#243B53")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    story.append(table)
    story.append(Spacer(1, 20))

    story.append(Paragraph(
        "<b>Important:</b> Scores are AI-generated estimates based on semantic "
        "similarity. They may not identify every factual error. Teacher review "
        "is recommended before finalizing marks.",
        styles["BodyText"]
    ))

    doc.build(story)
    return output_path
