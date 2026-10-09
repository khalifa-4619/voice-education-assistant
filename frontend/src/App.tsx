import { useEffect, useRef, useState } from "react";
import { ask, ApiError, type AskResponse } from "./api";
import { MicrophoneRecorder } from "./recorder";

type Status =
  | "idle"
  | "requesting-permission"
  | "recording"
  | "processing"
  | "success"
  | "error";

export default function App() {
  const recorderRef = useRef<MicrophoneRecorder | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<AskResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // Timer that ticks while recording, so the user sees the elapsed time.
  useEffect(() => {
    if (status !== "recording") return;
    const start = Date.now();
    setElapsedSeconds(0);
    const id = window.setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - start) / 1000));
    }, 250);
    return () => window.clearInterval(id);
  }, [status]);

  function resetOutput() {
    setResult(null);
    setErrorMessage("");
  }

  async function handleRecordClick() {
    // Start recording.
    if (status === "idle" || status === "success" || status === "error") {
      resetOutput();
      setStatus("requesting-permission");
      const recorder = new MicrophoneRecorder();
      recorderRef.current = recorder;
      try {
        await recorder.start();
        setStatus("recording");
      } catch (err) {
        recorderRef.current = null;
        setErrorMessage(friendlyMicError(err));
        setStatus("error");
      }
      return;
    }

    // Stop recording and submit.
    if (status === "recording") {
      const recorder = recorderRef.current;
      if (!recorder) return;
      setStatus("processing");
      try {
        const recording = await recorder.stop();
        recorderRef.current = null;

        const file = new File(
          [recording.blob],
          `question.${recording.extension}`,
          { type: recording.mimeType }
        );

        const response = await ask(file);
        setResult(response);
        setStatus("success");
      } catch (err) {
        setErrorMessage(describeError(err));
        setStatus("error");
      }
    }
  }

  async function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0];
    if (!selected) return;
    resetOutput();
    setStatus("processing");
    try {
      const response = await ask(selected);
      setResult(response);
      setStatus("success");
    } catch (err) {
      setErrorMessage(describeError(err));
      setStatus("error");
    } finally {
      // Allow re-selecting the same file later.
      event.target.value = "";
    }
  }

  const isRecording = status === "recording";
  const isBusy = status === "requesting-permission" || status === "processing";

  return (
    <main className="app">
      <h1>Voice Education Assistant</h1>
      <p className="subtitle">
        Press the button, ask your question, then press again to send.
      </p>

      <div className="controls">
        <button
          className={`mic-button ${isRecording ? "recording" : ""}`}
          onClick={handleRecordClick}
          disabled={isBusy}
        >
          {status === "idle" && "🎤 Record question"}
          {status === "requesting-permission" && "Waiting for permission…"}
          {status === "recording" && "⏹ Stop and ask"}
          {status === "processing" && "Working…"}
          {status === "success" && "🎤 Ask another"}
          {status === "error" && "🎤 Try again"}
        </button>

        {isRecording && (
          <span className="recording-indicator">
            🔴 Recording — {elapsedSeconds}s
          </span>
        )}
      </div>

      <details className="upload-fallback">
        <summary>Or upload an audio file instead</summary>
        <input
          type="file"
          accept="audio/*"
          onChange={handleFileChange}
          disabled={isBusy || isRecording}
        />
      </details>

      {status === "processing" && (
        <p className="status">
          The model takes 60–180 seconds on this CPU. Please wait…
        </p>
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

function friendlyMicError(err: unknown): string {
  if (err instanceof DOMException) {
    if (err.name === "NotAllowedError") {
      return "Microphone permission was denied. Allow it in your browser settings and try again.";
    }
    if (err.name === "NotFoundError") {
      return "No microphone was found on this device.";
    }
    if (err.name === "NotReadableError") {
      return "The microphone is already in use by another application.";
    }
  }
  if (err instanceof Error) return err.message;
  return "Could not start recording.";
}

function describeError(err: unknown): string {
  if (err instanceof ApiError) return err.detail;
  if (err instanceof Error) return err.message;
  return "Unexpected error.";
}
