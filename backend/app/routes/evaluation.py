import uuid
import tempfile
from pathlib import Path
from io import BytesIO

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from PIL import Image, UnidentifiedImageError

from app.services.pdf_reader import (
    HANDWRITING_LANGUAGES,
    extract_text_from_image,
    extract_text_from_pdf,
)
from app.services.parser import (
    parse_question_paper,
    parse_reference_sheet,
    parse_student_answers,
)
from app.services.evaluator import evaluate_all
from app.services.pdf_report import generate_report


router = APIRouter()

MAX_FILE_SIZE = 15 * 1024 * 1024
ALLOWED_IMAGE_FORMATS = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
}


async def read_document_upload(upload: UploadFile, label: str):
    extension = Path(upload.filename or "").suffix.lower()
    if extension != ".pdf" and extension not in ALLOWED_IMAGE_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"{label} must be a PDF, PNG, JPG, or JPEG file.",
        )

    content = await upload.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail=f"{label} is empty.",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"{label} exceeds the 15 MB limit.",
        )

    if extension == ".pdf":
        if not content.startswith(b"%PDF"):
            raise HTTPException(
                status_code=400,
                detail=f"{label} is not a valid PDF file.",
            )
    else:
        try:
            with Image.open(BytesIO(content)) as image:
                if image.format != ALLOWED_IMAGE_FORMATS[extension]:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{label} does not match its file extension.",
                    )
                image.verify()
        except (
            UnidentifiedImageError,
            Image.DecompressionBombError,
            OSError,
        ):
            raise HTTPException(
                status_code=400,
                detail=f"{label} is not a valid PNG or JPEG image.",
            )

    return content, extension


@router.post("/evaluate")
async def evaluate_essays(
    question_paper: UploadFile = File(...),
    reference_sheet: UploadFile = File(...),
    student_answers: UploadFile = File(...),
    handwriting_language: str = Form("en"),
):
    if handwriting_language not in HANDWRITING_LANGUAGES:
        raise HTTPException(
            status_code=422,
            detail=(
                "Unsupported handwriting language. Choose English, "
                "Malayalam, Hindi, or Arabic."
            ),
        )

    question_bytes, question_extension = await read_document_upload(
        question_paper, "Question paper"
    )
    reference_bytes, reference_extension = await read_document_upload(
        reference_sheet, "Reference sheet"
    )
    student_bytes, student_extension = await read_document_upload(
        student_answers, "Student answer sheet"
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        question_path = temp_path / f"questions{question_extension}"
        reference_path = temp_path / f"reference{reference_extension}"
        student_path = temp_path / f"student{student_extension}"

        question_path.write_bytes(question_bytes)
        reference_path.write_bytes(reference_bytes)
        student_path.write_bytes(student_bytes)

        def extract_document_text(path, extension):
            if extension == ".pdf":
                return extract_text_from_pdf(
                    str(path),
                    handwriting_language,
                )
            return extract_text_from_image(
                str(path),
                handwriting_language,
            )

        question_text = extract_document_text(question_path, question_extension)
        reference_text = extract_document_text(reference_path, reference_extension)
        student_text = extract_document_text(student_path, student_extension)

        for label, extracted in [
            ("Question paper", question_text),
            ("Reference sheet", reference_text),
            ("Student answer sheet", student_text),
        ]:
            if extracted.startswith("ERROR:"):
                raise HTTPException(status_code=400, detail=extracted)

        questions = parse_question_paper(question_text)
        reference_answers = parse_reference_sheet(reference_text)
        student_answers_parsed = parse_student_answers(student_text)

        if not questions:
            raise HTTPException(
                status_code=422,
                detail="Could not identify numbered questions in the question paper.",
            )

        if not reference_answers:
            raise HTTPException(
                status_code=422,
                detail="Could not identify numbered answers in the reference sheet.",
            )

        missing_references = sorted(set(questions) - set(reference_answers))
        if missing_references:
            raise HTTPException(
                status_code=422,
                detail=f"Reference answers are missing for question(s): {missing_references}",
            )

        results, total_marks = evaluate_all(
            student_answers_parsed,
            reference_answers,
        )

        max_marks = len(results) * 10
        report_id = str(uuid.uuid4())

        report_path = generate_report(
            results,
            total_marks,
            max_marks,
            report_id,
        )

        detailed_results = []

        for result in results:
            question_number = result["question"]
            detailed_results.append({
                **result,
                "question_text": questions.get(question_number, ""),
                "student_answer_found": bool(
                    student_answers_parsed.get(question_number, "").strip()
                ),
            })

    percentage = round(
        (total_marks / max_marks) * 100, 1
    ) if max_marks else 0

    return {
        "success": True,
        "report_id": report_id,
        "total_marks": total_marks,
        "max_marks": max_marks,
        "percentage": percentage,
        "results": detailed_results,
        "report_url": f"/api/reports/{report_id}",
        "message": "Evaluation completed. Teacher review is recommended.",
    }


@router.get("/reports/{report_id}")
def download_report(report_id: str):
    try:
        uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID.")

    report_path = (
        Path(__file__).resolve().parents[2]
        / "reports"
        / f"{report_id}.pdf"
    )

    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found.")

    return FileResponse(
        path=report_path,
        media_type="application/pdf",
        filename="Assessiva_Evaluation_Report.pdf",
    )