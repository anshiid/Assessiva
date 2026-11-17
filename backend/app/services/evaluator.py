
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

# Multilingual model supporting English, Malayalam, Hindi and Arabic
_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
    return _model


def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def evaluate_answer(student_answer, reference_answer, max_marks=10):
    """
    Preliminary AI evaluation using multilingual semantic similarity.
    Marks are estimates and should be reviewed by a teacher.
    """

    student_answer = clean_text(student_answer)
    reference_answer = clean_text(reference_answer)

    if not student_answer:
        return {
            "similarity": 0,
            "marks": 0,
            "feedback": "No answer was submitted."
        }

    if not reference_answer:
        return {
            "similarity": 0,
            "marks": 0,
            "feedback": "No teacher reference answer was found."
        }

    model = get_model()

    embeddings = model.encode(
        [student_answer, reference_answer],
        convert_to_numpy=True
    )

    similarity = float(
        cosine_similarity(
            [embeddings[0]],
            [embeddings[1]]
        )[0][0]
    )

    similarity = max(0, min(1, similarity))
    marks = round(similarity * max_marks, 1)

    if similarity >= 0.75:
        feedback = "Good coverage of the reference content. Review factual accuracy and completeness."
    elif similarity >= 0.50:
        feedback = "Some relevant concepts are present. More explanation and supporting points are needed."
    elif similarity >= 0.30:
        feedback = "Limited coverage of the expected content. Several important points may be missing."
    else:
        feedback = "The answer appears substantially different from the reference. Review the expected concepts."

    return {
        "similarity": round(similarity * 100, 2),
        "marks": marks,
        "feedback": feedback
    }


def evaluate_all(student_answers, reference_answers):
    results = []
    total_marks = 0

    for question_number in sorted(reference_answers):
        student = student_answers.get(question_number, "")
        reference = reference_answers[question_number]

        result = evaluate_answer(student, reference, 10)

        results.append({
            "question": question_number,
            **result
        })

        total_marks += result["marks"]

    return results, round(total_marks, 1)
