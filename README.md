# Assessiva

Assessiva is a local, teacher-led essay assessment tool. It accepts a question
paper, a teacher reference sheet, and one student's answers; extracts their
text; compares each student answer with the corresponding reference answer; and
returns a question-by-question review with a downloadable PDF report.

The current application has a React/Vite web interface and a FastAPI backend.
It is intended to assist a teacher, not to make final grading decisions.

## What it does

- Accepts PDF documents and PNG, JPG, or JPEG images for each of the three
  documents. Each upload is limited to 15 MB.
- Extracts selectable text from digital PDFs.
- Uses handwriting OCR for scanned PDFs and uploaded images:
  - **English:** `microsoft/trocr-base-handwritten`, which recognizes cropped
    text lines.
  - **Malayalam, Hindi, and Arabic:** `Qwen/Qwen3-VL-2B-Instruct`, which reads
    the page image and is asked to transcribe in the selected language.
- Finds numbered questions and answers using headings such as `Q1.`, `Q1:`,
  `Question 1:`, or `1.`.
- Compares student and reference answers using
  `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
- Displays preliminary per-question similarity, marks, and feedback, and
  creates a downloadable PDF report.
- Provides a responsive interface for desktop and mobile screens.

## Requirements

- Windows (the included launcher is `start_assessiva.bat`).
- Python 3.10 or later.
- Node.js compatible with Vite 8 (Node.js 20.19+ or 22.12+).
- npm.
- Internet access the first time a Hugging Face model is needed, to download
  its model files. Downloads are cached locally. Non-English handwriting OCR
  uses a multi-gigabyte model and may be slow on a CPU.

The backend and machine-learning models can use substantial memory and disk
space. Hardware requirements vary with document size and model versions.

## Install

Run these commands from the project root in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Set-Location frontend
npm install
Set-Location ..
```

If `py -3.12` is not available, create the environment with the Python 3
executable installed on your machine, for example:

```powershell
python -m venv .venv
```

The root `requirements.txt` is for the older Gradio prototype. The current
React/FastAPI app uses `backend\requirements.txt`.

## Run the application

### Windows launcher

From the project root, run:

```powershell
.\start_assessiva.bat
```

The launcher opens separate terminal windows for the backend and frontend.
Keep both windows open while using the app.

Open:

- Web app: <http://localhost:5173>
- API health: <http://127.0.0.1:8000/health>
- Interactive API documentation: <http://127.0.0.1:8000/docs>

If the browser says that it cannot connect, check that both terminal windows
are still running. The frontend is served on port `5173`; the API is served on
port `8000`.

### Run each service separately

Start the backend from the `backend` directory:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

In another terminal, start the frontend:

```powershell
Set-Location frontend
npm run dev
```

### Optional legacy Gradio prototype

The repository also contains an older Gradio interface in the root `main.py`,
with helper modules under `utils`. It is separate from the current React and
FastAPI application and is not started by `start_assessiva.bat`.

## Use the web app

1. Upload the **question paper**, **teacher reference**, and **student
   submission**. Each may be a PDF or a PNG/JPG/JPEG image.
2. Choose the handwriting language for scanned pages and images. English is
   selected by default; Malayalam, Hindi, and Arabic are available as
   best-effort options.
3. Select **Review submission** and wait for text extraction and evaluation.
   The first use of an OCR or evaluation model may take longer while model
   files are downloaded and loaded.
4. Review the extracted-answer indicators, similarity, marks, and feedback.
   Download the report if needed, and confirm or adjust the result as the
   teacher.

The language selection applies to **all scanned pages and images** in that
assessment. Digital PDFs with selectable text are extracted directly and do
not use the OCR language setting. If the documents use different languages,
the selected OCR language may not be suitable for every scanned document.

## How processing works

1. The frontend sends all three files and the selected handwriting language to
   `POST /api/evaluate`.
2. The API validates the file extension and file contents, enforces the 15 MB
   per-file limit, and places the uploads in a temporary working directory.
3. Digital PDF text is extracted directly. Scanned PDFs are rendered as page
   images; image files are read as images. English handwriting uses the
   line-detection and TrOCR path. The other supported handwriting languages
   use the Qwen vision-language model on the full page.
4. The parser groups extracted text under numbered headings. The question
   paper supplies the question text shown in the results; the teacher
   reference supplies the answers used for scoring.
5. For each answer in the reference sheet, the evaluator obtains multilingual
   sentence embeddings for the student and reference answers, computes cosine
   similarity, and scales that similarity to a score out of 10. Similarity
   thresholds select general feedback about coverage.
6. The API returns the results and a report ID. The generated PDF is stored
   under `backend\reports` and can be retrieved using that ID.

If no student answer is parsed for a reference question, Assessiva reports
that no answer was submitted for that question and awards zero marks for it.
The PDF report also assigns a letter grade from the overall percentage: A at
90% or above, B from 80% to under 90%, C from 70% to under 80%, D from 60%
to under 70%, and F below 60%.

## API

The development API base URL is `http://127.0.0.1:8000`.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Basic API status. |
| `GET` | `/health` | Health check. |
| `POST` | `/api/evaluate` | Evaluate the uploaded documents. |
| `GET` | `/api/reports/{report_id}` | Download a generated PDF report. |
| `GET` | `/docs` | Interactive FastAPI documentation. |

`POST /api/evaluate` accepts multipart form data:

- `question_paper` (required file)
- `reference_sheet` (required file)
- `student_answers` (required file)
- `handwriting_language` (optional: `en`, `ml`, `hi`, or `ar`; defaults to
  `en`)

Example using PowerShell and `curl.exe`:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/evaluate" `
  -F "question_paper=@question.pdf" `
  -F "reference_sheet=@reference.pdf" `
  -F "student_answers=@student.pdf" `
  -F "handwriting_language=en"
```

A successful response includes `total_marks`, `max_marks`, `percentage`,
question-level `results`, and `report_url`. Validation or processing errors
are returned as HTTP errors with a `detail` message.

## Models, languages, and accuracy

- Handwriting OCR languages offered by the interface: English, Malayalam,
  Hindi, and Arabic.
- The multilingual sentence-embedding model is used for answer comparison;
  that does not make the handwriting OCR equally accurate in every language.
- The multilingual handwriting path is best effort. Handwriting style, image
  quality, page layout, and language can affect recognition. Do not assume
  near-100% transcription accuracy.
- The evaluator uses semantic similarity rather than a detailed subject
  rubric. Similarity is not proof of factual correctness, completeness, or
  plagiarism, and the score is not a calibrated grade.
- The report itself includes a reminder that a teacher must review answers
  and marks before using them for formal assessment.

## Privacy and local use

Uploaded documents are processed by the local FastAPI backend and written to
a temporary directory that is removed after the request finishes. Generated
reports remain in `backend\reports` until manually removed. Model files are
downloaded from the Hugging Face Hub on first use and cached on the machine.
Document images and answer text are passed to the locally running models; this
code does not send student documents to a hosted OCR API.

The included development server is intended for local use. The API has no
user authentication, and its CORS configuration allows the local frontend
origins. Do not expose it to an untrusted network without adding appropriate
authentication, access controls, deployment configuration, and data-retention
protections.

## Development and tests

Run the frontend checks from `frontend`:

```powershell
npm run lint
npm run build
```

Run the focused Python OCR and parser regression tests from the project root:

```powershell
.\.venv\Scripts\python.exe -m unittest test_ocr test_parser
```

The OCR tests mock model inference; they do not measure real-world OCR
accuracy. On the first real OCR request, model files may need to be downloaded.

## Project layout

```text
backend/
  app/
    main.py                 FastAPI app, CORS, and route registration
    routes/evaluation.py    Upload validation, evaluation, and report endpoint
    services/
      pdf_reader.py         PDF/image text extraction and handwriting OCR
      parser.py             Numbered question/answer section parsing
      evaluator.py          Embedding similarity and preliminary feedback
      pdf_report.py         PDF report creation
  requirements.txt          Dependencies for the current backend
frontend/
  src/
    App.jsx                 Assessment page and API request
    components/             Upload cards, navigation, and results
    styles/style.css        Responsive interface styles
start_assessiva.bat         Starts the current frontend and backend
test_ocr.py                 OCR path regression tests
test_parser.py              Parser regression tests
```
