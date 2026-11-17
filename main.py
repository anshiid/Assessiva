
import os
import gradio as gr

from utils.pdf_reader import extract_text_from_pdf
from utils.parser import (
    parse_question_paper,
    parse_reference_sheet,
    parse_student_answers
)
from utils.evaluator import evaluate_all
from utils.report_generator import generate_report


os.makedirs("reports", exist_ok=True)
os.makedirs("uploads", exist_ok=True)


# ---------------------------
# ASSESSMENT PROCESSING
# ---------------------------

def run_assessment(question_pdf, reference_pdf, student_pdf):

    if not question_pdf or not reference_pdf or not student_pdf:
        return (
            "### Missing documents\nPlease upload all three PDF files.",
            None
        )

    question_text = extract_text_from_pdf(question_pdf)
    reference_text = extract_text_from_pdf(reference_pdf)
    student_text = extract_text_from_pdf(student_pdf)

    for document in [question_text, reference_text, student_text]:
        if document.startswith("ERROR:"):
            return f"### PDF reading error\n{document}", None

    questions = parse_question_paper(question_text)
    references = parse_reference_sheet(reference_text)
    answers = parse_student_answers(student_text)

    if not references:
        return (
            "### Reference sheet not recognised\n"
            "Please check that the reference PDF has numbered headings such as Q1, Q2 and Q3.",
            None
        )

    if not answers:
        return (
            "### Student answers not recognised\n"
            "Please check that the student PDF has numbered headings such as Q1, Q2 and Q3.",
            None
        )

    results, total = evaluate_all(answers, references)

    report_path = generate_report(results, total)

    total_possible = len(references) * 10
    percentage = (total / total_possible * 100) if total_possible else 0

    grade = (
        "A" if percentage >= 90 else
        "B" if percentage >= 80 else
        "C" if percentage >= 70 else
        "D" if percentage >= 60 else
        "F"
    )

    output = f"""
## Evaluation completed

<div class="result-summary">
    <div class="result-stat">
        <span class="stat-label">TOTAL SCORE</span>
        <strong>{total} <small>/ {total_possible}</small></strong>
    </div>
    <div class="result-stat">
        <span class="stat-label">PERCENTAGE</span>
        <strong>{percentage:.1f}%</strong>
    </div>
    <div class="result-stat">
        <span class="stat-label">GRADE</span>
        <strong>{grade}</strong>
    </div>
</div>

### Question-wise performance

| Question | Similarity | Marks | Feedback |
|---|---:|---:|---|
"""

    for result in results:
        feedback = result["feedback"].replace("|", "/")
        output += (
            f"| Q{result['question']} "
            f"| {result['similarity']}% "
            f"| {result['marks']}/10 "
            f"| {feedback} |\n"
        )

    missing = sorted(set(references) - set(answers))
    unmatched = sorted(set(answers) - set(references))

    if missing:
        output += "\n**Missing student answers:** " + ", ".join(
            f"Q{number}" for number in missing
        )

    if unmatched:
        output += "\n\n**Answers without reference entries:** " + ", ".join(
            f"Q{number}" for number in unmatched
        )

    output += """

> **Teacher review required:** These are preliminary AI estimates based on semantic similarity. They may not identify every factual error. Please review the answers before finalising marks.
"""

    return output, report_path


# ---------------------------
# CUSTOM DESIGN
# ---------------------------

custom_css = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --ink: #172b3a;
    --muted: #718096;
    --teal: #138b83;
    --teal-dark: #08756e;
    --line: #e5eceb;
    --paper: #ffffff;
    --soft: #f5f8f7;
}

body, .gradio-container {
    font-family: 'DM Sans', sans-serif !important;
    background: #f4f7f6 !important;
    color: var(--ink) !important;
}

.gradio-container {
    max-width: 1180px !important;
    margin: 0 auto !important;
    padding: 22px !important;
}

#assessiva-header {
    background: linear-gradient(120deg, #142d3b 0%, #174b50 65%, #147d77 100%);
    color: white;
    padding: 34px 38px;
    border-radius: 22px;
    margin-bottom: 25px;
    position: relative;
    overflow: hidden;
}

#assessiva-header:after {
    content: "";
    position: absolute;
    width: 230px;
    height: 230px;
    border: 1px solid rgba(255,255,255,.14);
    border-radius: 50%;
    right: 7%;
    top: -115px;
    box-shadow: 0 0 0 28px rgba(255,255,255,.035),
                0 0 0 58px rgba(255,255,255,.025);
}

.brand-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 27px;
}

.brand-mark {
    width: 39px;
    height: 39px;
    border-radius: 12px;
    display: grid;
    place-items: center;
    background: rgba(255,255,255,.15);
    font-size: 21px;
    font-weight: 800;
}

.brand-name {
    font-family: 'Manrope', sans-serif;
    font-size: 19px;
    font-weight: 800;
    letter-spacing: -.5px;
}

.brand-name span {
    color: #7de0d0;
}

.header-eyebrow {
    color: #9ce1d7;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 10px;
}

.header-title {
    font-family: 'Manrope', sans-serif;
    font-size: clamp(27px, 4vw, 39px);
    line-height: 1.2;
    font-weight: 800;
    max-width: 650px;
    margin: 0 0 12px;
}

.header-description {
    color: #d2e5e4;
    font-size: 14px;
    line-height: 1.7;
    max-width: 620px;
    margin: 0;
}

.section-heading {
    font-family: 'Manrope', sans-serif;
    font-size: 21px;
    font-weight: 800;
    color: #1c3442;
    margin: 8px 0 5px;
}

.section-subtitle {
    color: #788b91;
    font-size: 13px;
    margin-bottom: 18px;
}

.upload-card {
    background: white !important;
    border: 1px solid var(--line) !important;
    border-radius: 17px !important;
    padding: 18px !important;
    box-shadow: 0 5px 20px rgba(24, 57, 65, .035);
    min-height: 190px;
}

.upload-card label {
    color: #243e49 !important;
    font-weight: 700 !important;
}

.upload-card .file-preview,
.upload-card .upload-container {
    border-radius: 12px !important;
}

.upload-card .wrap {
    border: 1px dashed #c7d9d6 !important;
    background: #f8fbfa !important;
    border-radius: 12px !important;
}

.upload-card button {
    border-radius: 9px !important;
}

#evaluate-button {
    background: #138b83 !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    min-height: 52px !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    box-shadow: 0 6px 15px rgba(19,139,131,.18);
    transition: .2s ease;
}

#evaluate-button:hover {
    background: #08756e !important;
    transform: translateY(-1px);
}

#results-panel {
    background: white;
    border: 1px solid var(--line);
    border-radius: 17px;
    padding: 22px;
    margin-top: 12px;
}

#results-panel h2,
#results-panel h3 {
    font-family: 'Manrope', sans-serif;
    color: #1c3442;
}

#results-panel table {
    border-collapse: collapse;
    width: 100%;
    font-size: 13px;
}

#results-panel th {
    background: #f0f6f5;
    color: #31515a;
    font-weight: 700;
}

#results-panel th,
#results-panel td {
    padding: 12px;
    border-bottom: 1px solid #e8efee;
    text-align: left;
}

.result-summary {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin: 18px 0 25px;
}

.result-stat {
    background: #f3f8f7;
    border: 1px solid #e3eeeb;
    border-radius: 13px;
    padding: 17px;
}

.stat-label {
    display: block;
    color: #71878a;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    margin-bottom: 8px;
}

.result-stat strong {
    color: #137f78;
    font-family: 'Manrope', sans-serif;
    font-size: 26px;
}

.result-stat small {
    color: #829393;
    font-size: 13px;
}

#report-download {
    border: 1px solid #dce9e6 !important;
    border-radius: 14px !important;
    background: white !important;
    padding: 15px !important;
}

#footer-note {
    text-align: center;
    color: #879697;
    font-size: 11px;
    padding: 20px 5px 8px;
}

.gradio-container button,
.gradio-container input {
    font-family: 'DM Sans', sans-serif !important;
}

@media (max-width: 700px) {
    .gradio-container {
        padding: 10px !important;
    }

    #assessiva-header {
        padding: 25px 22px;
        border-radius: 17px;
    }

    .upload-card {
        min-height: auto;
    }

    .result-summary {
        grid-template-columns: 1fr;
    }

    .result-stat {
        padding: 13px 16px;
    }

    #results-panel {
        padding: 14px;
        overflow-x: auto;
    }

    #results-panel table {
        min-width: 560px;
    }
}
"""


# ---------------------------
# RESPONSIVE GRADIO APP
# ---------------------------

with gr.Blocks(
    title="Assessiva AI | Essay Evaluation",
    theme=gr.themes.Soft(
        primary_hue="teal",
        secondary_hue="slate",
        neutral_hue="slate",
        font=["DM Sans", "sans-serif"]
    ),
    css=custom_css
) as demo:

    gr.HTML("""
    <div id="assessiva-header">
        <div class="brand-row">
            <div class="brand-mark">A</div>
            <div class="brand-name">assessiva<span>.</span></div>
        </div>
        <div class="header-eyebrow">Intelligent essay assessment</div>
        <h1 class="header-title">A smarter way to evaluate written answers.</h1>
        <p class="header-description">
            Upload your exam documents, analyse student responses and
            generate structured evaluation reports — all in one place.
        </p>
    </div>
    """)

    gr.HTML("""
    <div class="section-heading">Start an evaluation</div>
    <div class="section-subtitle">
        Add the three documents below to begin assessing a student's work.
    </div>
    """)

    with gr.Row(equal_height=True):

        with gr.Column(elem_classes=["upload-card"], scale=1, min_width=220):
            gr.Markdown("### 01 · Question paper")
            gr.Markdown(
                "<small>Upload the exam questions in PDF format.</small>"
            )
            question_file = gr.File(
                label="Question paper",
                file_types=[".pdf"],
                type="filepath"
            )

        with gr.Column(elem_classes=["upload-card"], scale=1, min_width=220):
            gr.Markdown("### 02 · Reference sheet")
            gr.Markdown(
                "<small>Upload the teacher's answers and marking guide.</small>"
            )
            reference_file = gr.File(
                label="Teacher reference",
                file_types=[".pdf"],
                type="filepath"
            )

        with gr.Column(elem_classes=["upload-card"], scale=1, min_width=220):
            gr.Markdown("### 03 · Student submission")
            gr.Markdown(
                "<small>Upload the student's completed answer sheet.</small>"
            )
            student_file = gr.File(
                label="Student answers",
                file_types=[".pdf"],
                type="filepath"
            )

    gr.Markdown(
        "<small>PDF files only · Text-based PDFs are recommended for best extraction.</small>"
    )

    evaluate_button = gr.Button(
        "Evaluate submission  →",
        variant="primary",
        elem_id="evaluate-button"
    )

    gr.HTML("""
    <div class="section-heading" style="margin-top:30px">
        Assessment report
    </div>
    <div class="section-subtitle">
        Your evaluation summary and downloadable report will appear here.
    </div>
    """)

    results_box = gr.Markdown(
        "Your results will appear here after you evaluate a submission.",
        elem_id="results-panel"
    )

    report_file = gr.File(
        label="Your evaluation report",
        elem_id="report-download"
    )

    evaluate_button.click(
        fn=run_assessment,
        inputs=[question_file, reference_file, student_file],
        outputs=[results_box, report_file]
    )

    gr.HTML("""
    <div id="footer-note">
        ASSESSIVA AI · Evaluate Smarter. Learn Better.<br>
        AI-generated assessments should be reviewed by a teacher.
    </div>
    """)


if __name__ == "__main__":
    demo.launch()
