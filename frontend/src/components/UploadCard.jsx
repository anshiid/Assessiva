
import { useRef } from "react";
import { Check, FileText, Upload, X } from "lucide-react";

export default function UploadCard({
  step,
  title,
  description,
  file,
  onChange,
  accept = ".pdf,.png,.jpg,.jpeg"
}) {
  const inputRef = useRef(null);
  const fileType = file?.name.split(".").pop()?.toUpperCase() || "";
  const fileSize = file
    ? file.size < 1024 * 1024
      ? `${Math.max(1, Math.round(file.size / 1024))} KB`
      : `${(file.size / (1024 * 1024)).toFixed(1)} MB`
    : "";

  return (
    <article className="upload-card">
      <div className="upload-card-top">
        <span className="upload-step">{step}</span>
        <span className="upload-icon"><FileText size={20} /></span>
      </div>

      <h3>{title}</h3>
      <p>{description}</p>

      <input
        ref={inputRef}
        type="file"
        accept={accept}
        hidden
        aria-label={`Choose ${title} file`}
        onChange={(event) => onChange(event.target.files[0] || null)}
      />

      {file ? (
        <div className="selected-file">
          <span className="selected-file-check"><Check size={16} /></span>
          <span className="selected-file-details">
            <span className="file-ready">READY TO REVIEW</span>
            <strong title={file.name}>{file.name}</strong>
            <small>{fileType} · {fileSize}</small>
          </span>
          <button
            type="button"
            aria-label={`Remove ${title} file`}
            onClick={() => {
              onChange(null);
              if (inputRef.current) inputRef.current.value = "";
            }}
          >
            <X size={17} />
          </button>
        </div>
      ) : (
        <button
          className="upload-button"
          type="button"
          aria-label={`Choose ${title} file`}
          onClick={() => inputRef.current?.click()}
        >
          <Upload size={17} />
          <span>Choose a file</span>
          <span className="upload-browse">Browse files</span>
        </button>
      )}

      <span className="file-note">PDF, PNG, JPG or JPEG <span>·</span> 15 MB max</span>
    </article>
  );
}
