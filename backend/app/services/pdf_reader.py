
import pymupdf as fitz
import torch
import cv2
import numpy as np

from PIL import Image, ImageOps, UnidentifiedImageError
from transformers import TrOCRProcessor, VisionEncoderDecoderModel


# OCR model is loaded only when required.
_processor = None
_model = None
_multilingual_processor = None
_multilingual_model = None

MODEL_NAME = "microsoft/trocr-base-handwritten"
MULTILINGUAL_MODEL_NAME = "Qwen/Qwen3-VL-2B-Instruct"
HANDWRITING_LANGUAGES = {
    "en": "English",
    "ml": "Malayalam",
    "hi": "Hindi",
    "ar": "Arabic",
}


def load_handwriting_model():
    global _processor, _model

    if _processor is None or _model is None:
        print("Loading Assessiva handwriting model...")

        _processor = TrOCRProcessor.from_pretrained(MODEL_NAME)
        _model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME)

        _model.eval()

        print("Handwriting model loaded successfully.")

    return _processor, _model


def load_multilingual_handwriting_model():
    global _multilingual_processor, _multilingual_model

    if _multilingual_processor is None or _multilingual_model is None:
        from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

        print("Loading Assessiva multilingual handwriting model...")

        _multilingual_processor = AutoProcessor.from_pretrained(
            MULTILINGUAL_MODEL_NAME
        )
        _multilingual_model = Qwen3VLForConditionalGeneration.from_pretrained(
            MULTILINGUAL_MODEL_NAME,
            dtype="auto",
            device_map="auto",
        )
        _multilingual_model.eval()

        print("Multilingual handwriting model loaded successfully.")

    return _multilingual_processor, _multilingual_model


def validate_handwriting_language(language):
    if language not in HANDWRITING_LANGUAGES:
        supported = ", ".join(HANDWRITING_LANGUAGES)
        raise ValueError(
            f"Unsupported handwriting language '{language}'. "
            f"Choose one of: {supported}."
        )


def remove_horizontal_lines(binary_image):
    """
    Remove long horizontal notebook ruling lines from a binary image with
    white foreground on a black background.
    """
    horizontal_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (max(40, binary_image.shape[1] // 25), 1)
    )

    horizontal_lines = cv2.morphologyEx(
        binary_image,
        cv2.MORPH_OPEN,
        horizontal_kernel
    )

    cleaned = cv2.subtract(binary_image, horizontal_lines)

    return cleaned


def detect_text_lines(page):
    """
    Render a PDF page and detect individual text lines.
    Returns cropped PIL images in reading order.
    """

    return detect_text_lines_from_image(render_pdf_page(page))


def render_pdf_page(page):
    max_render_dimension = 4000
    scale = min(
        4.0,
        max_render_dimension / max(page.rect.width, page.rect.height),
    )
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)


def detect_text_lines_from_image(image):
    """Detect individual text lines in a PIL image, in reading order."""
    image = image.convert("RGB")
    image_array = np.array(image)

    gray = cv2.cvtColor(
        image_array,
        cv2.COLOR_RGB2GRAY
    )

    # Use a binary image only to locate text rows and ignore notebook rules.
    _, binary = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    # Remove long notebook lines.
    cleaned = remove_horizontal_lines(binary)

    # Calculate the amount of text in every horizontal row.
    row_projection = np.count_nonzero(cleaned, axis=1)

    threshold = max(5, int(cleaned.shape[1] * 0.01))

    active_rows = np.where(row_projection > threshold)[0]

    if len(active_rows) == 0:
        return []

    # Group nearby active rows into text lines.
    groups = []
    start = active_rows[0]
    previous = active_rows[0]
    row_gap = max(24, int(cleaned.shape[0] * 0.01))

    for row in active_rows[1:]:
        if row - previous > row_gap:
            groups.append((start, previous))
            start = row

        previous = row

    groups.append((start, previous))

    candidates = []
    padding = max(12, int(cleaned.shape[1] * 0.01))
    min_line_height = max(10, int(cleaned.shape[0] * 0.005))

    for top, bottom in groups:
        # Ignore very small marks or noise.
        if bottom - top < min_line_height:
            continue

        y1 = max(0, top - padding)
        y2 = min(cleaned.shape[0], bottom + padding + 1)

        line = cleaned[y1:y2, :]

        # Find the horizontal extent of the text.
        column_ink = np.count_nonzero(line, axis=0)
        column_threshold = max(2, int((bottom - top + 1) * 0.02))
        columns = np.where(column_ink >= column_threshold)[0]

        if len(columns) == 0:
            continue

        x1 = max(0, columns[0] - 15)
        x2 = min(cleaned.shape[1], columns[-1] + 16)

        line_width = x2 - x1
        line_height = y2 - y1
        if (
            line_width > cleaned.shape[1] * 0.95
            and line_width / line_height > 20
        ):
            continue

        candidates.append((y1, y2, x1, x2))

    if not candidates:
        return []

    candidates.sort(key=lambda candidate: candidate[0])
    centers = [(top + bottom) / 2 for top, bottom, _, _ in candidates]
    center_gaps = [
        centers[index] - centers[index - 1]
        for index in range(1, len(centers))
    ]

    if center_gaps:
        typical_gap = float(np.median(center_gaps))
        cluster_gap = max(
            cleaned.shape[0] * 0.03,
            typical_gap * 3,
        )
        clusters = [[candidates[0]]]
        for index, candidate in enumerate(candidates[1:], start=1):
            if centers[index] - centers[index - 1] > cluster_gap:
                clusters.append([])
            clusters[-1].append(candidate)

        if len(clusters) > 1:
            candidates = [
                candidate
                for cluster in clusters
                for candidate in cluster
                if len(cluster) > 1
                or candidate[3] - candidate[2] >= cleaned.shape[1] * 0.25
            ]

    line_images = []
    for y1, y2, x1, x2 in candidates:
        # Keep the original grayscale pixels for recognition: removing rules
        # from the OCR image can erase pen strokes that touch a ruled line.
        original_crop = image.crop((x1, y1, x2, y2))
        line_images.append(original_crop)

    return line_images


def extract_text_from_image(image_path, handwriting_language="en"):
    """Recognize handwriting in a PNG or JPEG image."""
    validate_handwriting_language(handwriting_language)

    try:
        with Image.open(image_path) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
    except (UnidentifiedImageError, OSError) as error:
        return f"ERROR: Could not read image: {error}"

    if handwriting_language == "en":
        line_images = detect_text_lines_from_image(image)
        if not line_images:
            return "ERROR: No readable handwriting was detected in the image."
        recognized_text = recognize_handwriting_lines(line_images)
    else:
        try:
            recognized_text = recognize_multilingual_handwriting(
                image,
                handwriting_language,
            )
        except (ImportError, OSError, RuntimeError) as error:
            return f"ERROR: Multilingual handwriting OCR failed: {error}"

    if not recognized_text:
        return "ERROR: No readable handwriting was recognized in the image."

    return recognized_text


def preprocess_handwriting_line(line_image):
    gray = cv2.cvtColor(
        np.asarray(line_image),
        cv2.COLOR_RGB2GRAY
    )
    _, thresholded = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    _, labels, stats, _ = cv2.connectedComponentsWithStats(
        thresholded,
        connectivity=8,
    )
    keep_component = stats[:, cv2.CC_STAT_AREA] >= 4
    keep_component[0] = False
    thresholded = np.where(
        keep_component[labels],
        255,
        0,
    ).astype(np.uint8)
    rgb = cv2.cvtColor(thresholded, cv2.COLOR_GRAY2RGB)
    return Image.fromarray(rgb)


def recognize_handwriting(page, handwriting_language="en"):
    """
    Recognize text using the OCR model selected for the handwriting language.
    """

    validate_handwriting_language(handwriting_language)

    if handwriting_language != "en":
        return recognize_multilingual_handwriting(
            render_pdf_page(page),
            handwriting_language,
        )

    line_images = detect_text_lines(page)

    if not line_images:
        return ""

    return recognize_handwriting_lines(line_images)


def recognize_multilingual_handwriting(image, handwriting_language):
    validate_handwriting_language(handwriting_language)
    processor, model = load_multilingual_handwriting_model()
    language_name = HANDWRITING_LANGUAGES[handwriting_language]
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image.convert("RGB")},
                {
                    "type": "text",
                    "text": (
                        "Transcribe all handwriting exactly as written in "
                        f"{language_name}. Preserve paragraph breaks, "
                        "numbering, and question labels. Do not translate, "
                        "summarize, or add text. Return only the transcription."
                    ),
                },
            ],
        }
    ]
    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    )
    inputs = inputs.to(model.device)

    with torch.inference_mode():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=2048,
            do_sample=False,
        )

    generated_ids_trimmed = [
        output_ids[len(input_ids):]
        for input_ids, output_ids in zip(inputs["input_ids"], generated_ids)
    ]
    recognized_text = processor.batch_decode(
        generated_ids_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )[0].strip()
    print(f"Multilingual OCR completed for {language_name}.")
    return recognized_text


def recognize_handwriting_lines(line_images):
    processor, model = load_handwriting_model()
    recognized_lines = []

    print(f"Detected {len(line_images)} text lines.")

    for index, line_image in enumerate(line_images, start=1):
        recognition_image = preprocess_handwriting_line(line_image)
        pixel_values = processor(
            images=recognition_image,
            return_tensors="pt"
        ).pixel_values

        with torch.inference_mode():
            generated_ids = model.generate(
                pixel_values,
                max_new_tokens=128,
                num_beams=4,
                early_stopping=True,
            )

        text = processor.batch_decode(
            generated_ids,
            skip_special_tokens=True
        )[0].strip()

        if text:
            recognized_lines.append(text)

        print(f"Line {index}: {text}")

    return "\n".join(recognized_lines)


def extract_text_from_pdf(pdf_path, handwriting_language="en"):
    """
    Extract typed PDF text normally.
    Use handwriting recognition on pages without selectable text.
    """
    validate_handwriting_language(handwriting_language)

    try:
        document = fitz.open(pdf_path)

        try:
            extracted_pages = []

            for page_number, page in enumerate(document, start=1):

                page_text = page.get_text("text").strip()

                if page_text:
                    print(f"Page {page_number}: Typed text detected.")
                    extracted_pages.append(page_text)

                else:
                    print(
                        f"Page {page_number}: No selectable text. "
                        "Starting handwriting recognition..."
                    )

                    recognized_text = recognize_handwriting(
                        page,
                        handwriting_language,
                    )

                    if recognized_text:
                        extracted_pages.append(recognized_text)

            full_text = "\n\n".join(extracted_pages)

        finally:
            document.close()

        if not full_text.strip():
            return "ERROR: No readable text or handwriting was recognized."

        return full_text.strip()

    except Exception as error:
        return f"ERROR: Could not read PDF: {error}"
