
import { useState } from "react";
import { ArrowRight, BookOpen, Check, LoaderCircle, ShieldCheck } from "lucide-react";
import Navbar from "./components/Navbar";
import UploadCard from "./components/UploadCard";
import Results from "./components/Results";
import classroomHero from "./assets/classroom-hero.jpg";
import "./styles/style.css";

const API_URL = "http://127.0.0.1:8000";

export default function App() {
  const [files, setFiles] = useState({
    question: null,
    reference: null,
    student: null,
  });

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [handwritingLanguage, setHandwritingLanguage] = useState("en");

  const updateFile = (key, file) => {
    setFiles((previous) => ({ ...previous, [key]: file }));
    setError("");
    setResults(null);
  };

  const evaluateEssays = async () => {
    if (!files.question || !files.reference || !files.student) {
      setError("Please upload all three documents before continuing.");
      return;
    }

    setLoading(true);
    setError("");
    setResults(null);

    const formData = new FormData();
    formData.append("question_paper", files.question);
    formData.append("reference_sheet", files.reference);
    formData.append("student_answers", files.student);
    formData.append("handwriting_language", handwritingLanguage);

    try {
      const response = await fetch(`${API_URL}/api/evaluate`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Evaluation failed. Please try again.");
      }

      setResults(data);
      setTimeout(() => {
        document.getElementById("results")?.scrollIntoView({
          behavior: "smooth",
        });
      }, 100);
    } catch (err) {
      setError(
        err.message === "Failed to fetch"
          ? "Cannot connect to Assessiva backend. Please make sure FastAPI is running."
          : err.message
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar />

      <main>
        <section className="hero" id="home" aria-labelledby="hero-title">
          <div className="hero-content">
            <span className="eyebrow"><span className="eyebrow-mark" /> A WORKSPACE FOR EDUCATORS</span>
            <h1 id="hero-title">Make room for<br /><em>better feedback.</em></h1>
            <p>
              Bring the question paper, your marking guide, and each student’s
              work into one calm, focused place. Review structured feedback
              while keeping every final decision in your hands.
            </p>
            <a href="#evaluation" className="primary-button">
              Start an assessment <ArrowRight size={18} />
            </a>

            <div className="hero-proof">
              <span><ShieldCheck size={17} /> Teacher-led, always</span>
              <span className="proof-divider" />
              <span>Three documents. One clear review.</span>
            </div>
          </div>

          <div className="hero-art">
            <img
              className="hero-image"
              src={classroomHero}
              alt="A teacher working at a laptop in front of a classroom chalkboard"
            />
            <span className="hero-image-caption">ASSESSIVA / IN THE CLASSROOM</span>
            <span className="hero-image-index">TEACH · LEARN · GROW</span>
          </div>
        </section>

        <section className="evaluation-section" id="evaluation" aria-labelledby="evaluation-title">
          <div className="section-topline">
            <span>01&nbsp; / &nbsp;NEW ASSESSMENT</span>
            <span>THREE DOCUMENTS&nbsp; · &nbsp;PDF OR IMAGE</span>
          </div>

          <div className="section-heading">
            <div>
              <span className="eyebrow">A THOUGHTFUL PLACE TO BEGIN</span>
              <h2 id="evaluation-title">Set the table.</h2>
            </div>
            <p>Add the prompt, your reference, and the student’s submission.<br className="desktop-break" /> We’ll bring them together for review.</p>
          </div>

          <div className="upload-grid">
            <UploadCard
              step="01"
              title="Question paper"
              description="The prompt or exam questions given to the student."
              file={files.question}
              onChange={(file) => updateFile("question", file)}
            />

            <UploadCard
              step="02"
              title="Teacher reference"
              description="Your reference answers, rubric, or marking guide."
              file={files.reference}
              onChange={(file) => updateFile("reference", file)}
            />

            <UploadCard
              step="03"
              title="Student submission"
              description="The student's completed answers, ready to review."
              file={files.student}
              onChange={(file) => updateFile("student", file)}
            />
          </div>

          <div className="handwriting-language">
            <label htmlFor="handwriting-language">Handwriting language</label>
            <select
              id="handwriting-language"
              value={handwritingLanguage}
              onChange={(event) => setHandwritingLanguage(event.target.value)}
            >
              <option value="en">English</option>
              <option value="ml">Malayalam (best effort)</option>
              <option value="hi">Hindi (best effort)</option>
              <option value="ar">Arabic (best effort)</option>
            </select>
            <p>
              Applies to scanned pages and images. Non-English OCR uses a local
              multi-GB model on first use and can be slower; review the results
              carefully before grading.
            </p>
          </div>

          <div className="evaluation-action">
            {error && <div className="error-message" role="alert">{error}</div>}
            <div className="action-copy">
              <span>WHEN YOU’RE READY</span>
              <p>PDF or PNG/JPG/JPEG · up to 15 MB each. Clear, straight images help OCR; review results before grading.</p>
            </div>
            <button
              className="evaluate-button"
              onClick={evaluateEssays}
              disabled={loading}
            >
              {loading ? (
                <><LoaderCircle className="spin" size={18} /> Preparing your review…</>
              ) : (
                <>Review submission <ArrowRight size={18} /></>
              )}
            </button>
            <span className="action-note"><ShieldCheck size={16} /> Final decisions stay with the teacher.</span>
          </div>
        </section>

        <Results data={results} />

        <section className="about-section" id="about" aria-labelledby="about-title">
          <div className="about-number">A / 01</div>
          <div className="about-copy">
            <span className="eyebrow">MADE FOR THE HUMAN SIDE OF TEACHING</span>
            <h2 id="about-title">A little less sorting.<br /><em>A little more teaching.</em></h2>
            <p>
              Assessiva organizes essay review into a clear starting point.
              Its feedback is a helpful second look—not a substitute for your
              judgement, your context, or the conversation with a student.
            </p>
          </div>
          <div className="about-aside">
            <span className="aside-mark"><Check size={18} /></span>
            <p>Every assessment deserves a thoughtful human review.</p>
          </div>
        </section>
      </main>

      <footer className="footer">
        <a className="brand footer-brand" href="#home" aria-label="Assessiva home">
          <span className="brand-icon"><BookOpen size={20} /></span>
          <span>Assessiva</span>
        </a>
        <span className="footer-line">A calmer way to review written work.</span>
        <a href="#home" className="back-to-top">BACK TO TOP ↑</a>
      </footer>
    </>
  );
}
