import { useState } from "react";
import { ask, ApiError, type AskResponse } from "./api";

type Status = "idle" | "loading" | "success" | "error";

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<AskResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>("");

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null;
    setFile(selected);
    setStatus("idle");
    setResult(null);
    setErrorMessage("");
  }

  async function handleSubmit() {
    if (!file) return;
    setStatus("loading");
    setResult(null);
    setErrorMessage("");
    try {
      const response = await ask(file);
      setResult(response);
      setStatus("success");
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMessage(err.detail);
      } else {
        setErrorMessage("Unexpected error. Check the browser console.");
        console.error(err);
      }
      setStatus("error");
    }
  }

  return (
    <main className="app">
      <h1>Voice Education Assistant</h1>
      <p className="subtitle">
        Upload a spoken question. The assistant will transcribe it and answer.
      </p>

      <div className="controls">
        <input
          type="file"
          accept="audio/*"
          onChange={handleFileChange}
          disabled={status === "loading"}
        />
        <button
          onClick={handleSubmit}
          disabled={!file || status === "loading"}
        >
          {status === "loading" ? "Asking…" : "Ask"}
        </button>
      </div>

      {file && <p className="filename">Selected: {file.name}</p>}

      {status === "loading" && (
        <p className="status">Working… the real model takes 10–60 seconds.</p>
      )}

      {status === "error" && (
        <div className="error">
          <strong>Error:</strong> {errorMessage}
        </div>
      )}

      {result && (
        <div className="result">
          <section>
            <h2>Your question</h2>
            <p className="transcript">{result.transcript}</p>
          </section>

          <section>
            <h2>Answer</h2>
            <p className="answer">{result.answer}</p>
          </section>

          <section className="timings">
            <span>ASR: {result.asr_seconds.toFixed(2)}s</span>
            <span>LLM: {result.llm_seconds.toFixed(2)}s</span>
            <span>Total: {result.total_seconds.toFixed(2)}s</span>
          </section>
        </div>
      )}
    </main>
  );
}
