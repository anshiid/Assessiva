
import { Award, Download, FileCheck, MessageSquareText } from "lucide-react";

export default function Results({ data }) {
  if (!data) return null;

  const downloadReport = () => {
    const reportUrl = `http://127.0.0.1:8000${data.report_url}`;
    window.open(reportUrl, "_blank", "noopener,noreferrer");
  };

  return (
    <section className="results-section" id="results" aria-labelledby="results-title">
      <div className="section-heading">
        <span className="eyebrow">02&nbsp; / &nbsp;REVIEW NOTES</span>
        <h2 id="results-title">A closer look.</h2>
        <p>Explore the score and feedback for each question.</p>
      </div>

      <div className="score-card">
        <div>
          <span className="score-label">Total Score</span>
          <h2>{data.total_marks} <small>/ {data.max_marks}</small></h2>
          <p>{data.percentage}% overall score</p>
        </div>
        <div className="score-icon"><Award size={35} /></div>
      </div>

      <div className="results-list">
        {data.results?.map((item) => (
          <article className="result-item" key={item.question}>
            <div className="result-top">
              <h3>Question {item.question}</h3>
              <strong>{item.marks} / 10</strong>
            </div>

            <p className="question-text">{item.question_text}</p>

            <div className="result-meta">
              <span><FileCheck size={15} /> Similarity: {item.similarity}%</span>
              <span>
                <MessageSquareText size={15} />
                {item.student_answer_found ? "Answer submitted" : "No answer found"}
              </span>
            </div>

            <p className="feedback">{item.feedback}</p>
          </article>
        ))}
      </div>

      <div className="teacher-notice">
        These notes are a starting point for your review. Please confirm the feedback before sharing it with a student.
      </div>

      <button className="download-button" type="button" onClick={downloadReport}>
        <Download size={18} />
        Download PDF Report
      </button>
    </section>
  );
}
