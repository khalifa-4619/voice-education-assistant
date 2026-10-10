import { useEffect, useRef, useState } from "react";
import {
  ask,
  ApiError,
  submitFeedback,
  type AskResponse,
} from "./api";
import { MicrophoneRecorder } from "./recorder";
import { TextToSpeech } from "./tts";

type Status =
  | "idle"
  | "requesting-permission"
  | "recording"
  | "processing"
  | "success"
  | "error";

export default function App() {
  const recorderRef = useRef<MicrophoneRecorder | null>(null);
  const ttsRef = useRef<TextToSpeech | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<AskResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [isSpeaking, setIsSpeaking] = useState(false);
    // Feedback form state. Reset when a new result arrives.
  const [feedbackUseful, setFeedbackUseful] = useState<boolean | null>(null);
  const [feedbackLanguage, setFeedbackLanguage] = useState("en");
  const [feedbackSubject, setFeedbackSubject] = useState("general");
  const [feedbackNotes, setFeedbackNotes] = useState("");
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [feedbackError, setFeedbackError] = useState("");
  const [submittingFeedback, setSubmittingFeedback] = useState(false);

  // Set up TTS once.
  useEffect(() => {
    ttsRef.current = new TextToSpeech();
    return () => {
      ttsRef.current?.cancel();
    };
  }, []);

  // Timer that ticks while recording.
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
    ttsRef.current?.cancel();
    setIsSpeaking(false);
  }

  async function handleRecordClick() {
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
        setFeedbackUseful(null);
        setFeedbackLanguage("en");
        setFeedbackSubject("general");
        setFeedbackNotes("");
        setFeedbackSubmitted(false);
        setFeedbackError("");
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
      setFeedbackUseful(null)   
      setFeedbackLanguage("en");
      setFeedbackSubject("general");
      setFeedbackNotes("");
      setFeedbackSubmitted(false);
      setFeedbackError("");
      setStatus("success");
    } catch (err) {
      setErrorMessage(describeError(err));
      setStatus("error");
    } finally {
      event.target.value = "";
    }
  }

  function handlePlayAnswer() {
    if (!result || !ttsRef.current) return;

    if (isSpeaking) {
      ttsRef.current.cancel();
      setIsSpeaking(false);
      return;
    }

    try {
      ttsRef.current.onEnd(() => setIsSpeaking(false));
      // Choose the language by whether the transcript contains characters
      // outside the ASCII range -- a simple Hausa-vs-English heuristic.
      // We pick "en-NG" for now; Hausa voices are not installed on
      // Windows by default, so this is documented as a limitation.
      ttsRef.current.speak(result.answer, { lang: "en-NG", rate: 0.95 });
      setIsSpeaking(true);
    } catch (err) {
      setErrorMessage(describeError(err));
    }
  }

  async function handleSubmitFeedback() {
    if (!result || feedbackUseful === null) return;
    setSubmittingFeedback(true);
    setFeedbackError("");
    try {
      await submitFeedback({
        interaction_id: result.interaction_id,
        useful: feedbackUseful,
        language: feedbackLanguage,
        subject: feedbackSubject,
        notes: feedbackNotes,
      });
      setFeedbackSubmitted(true);
    } catch (err) {
      setFeedbackError(describeError(err));
    } finally {
      setSubmittingFeedback(false);
    }
  }
  const isRecording = status === "recording";
  const isBusy = status === "requesting-permission" || status === "processing";
  const ttsAvailable = TextToSpeech.isSupported();

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
            {ttsAvailable && (
              <button
                className="play-button"
                onClick={handlePlayAnswer}
                type="button"
              >
                {isSpeaking ? "⏹ Stop" : "🔊 Play answer"}
              </button>
            )}
            {!ttsAvailable && (
              <p className="tts-unavailable">
                Text-to-speech is not available in this browser.
              </p>
            )}
          </section>
          {!feedbackSubmitted && (
            <section className="feedback">
              <h2>Was this answer useful?</h2>
              <div className="feedback-row">
                <label>
                  <input
                    type="radio"
                    name="useful"
                    checked={feedbackUseful === true}
                    onChange={() => setFeedbackUseful(true)}
                  />{" "}
                  Yes
                </label>
                <label>
                  <input
                    type="radio"
                    name="useful"
                    checked={feedbackUseful === false}
                    onChange={() => setFeedbackUseful(false)}
                  />{" "}
                  No
                </label>
              </div>

              <div className="feedback-row">
                <label>
                  Language:{" "}
                  <select
                    value={feedbackLanguage}
                    onChange={(e) => setFeedbackLanguage(e.target.value)}
                  >
                    <option value="en">English</option>
                    <option value="ha">Hausa</option>
                    <option value="ig">Igbo</option>
                    <option value="yo">Yoruba</option>
                  </select>
                </label>

                <label>
                  Subject:{" "}
                  <select
                    value={feedbackSubject}
                    onChange={(e) => setFeedbackSubject(e.target.value)}
                  >
                    <option value="general">General</option>
                    <option value="science">Science</option>
                    <option value="math">Mathematics</option>
                    <option value="english">English</option>
                    <option value="social">Social Studies</option>
                    <option value="other">Other</option>
                  </select>
                </label>
              </div>

              <textarea
                placeholder="Optional: anything else you want us to know?"
                value={feedbackNotes}
                onChange={(e) => setFeedbackNotes(e.target.value)}
                rows={2}
              />

              {feedbackError && (
                <p className="feedback-error">{feedbackError}</p>
              )}

              <button
                type="button"
                onClick={handleSubmitFeedback}
                disabled={feedbackUseful === null || submittingFeedback}
              >
                {submittingFeedback ? "Submitting…" : "Submit feedback"}
              </button>
            </section>
          )}

          {feedbackSubmitted && (
            <section className="feedback-thanks">
              <p>Thank you — your feedback was recorded.</p>
            </section>
          )}

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
