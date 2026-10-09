/**
 * Microphone recorder built on the browser's MediaRecorder API.
 *
 * This module has no React dependency -- it is plain TypeScript that
 * opens the microphone, records, and returns a Blob. The UI layer is
 * responsible for showing states; this layer is responsible only for
 * capturing audio.
 *
 * Browser compatibility notes:
 *   - Chrome / Edge: produces audio/webm;codecs=opus (best quality/size).
 *   - Firefox:       produces audio/ogg;codecs=opus.
 *   - Safari 14.1+:  produces audio/mp4.
 *   We pick the first supported format. The backend allow-list includes
 *   wav, mp3, m4a, webm, ogg, flac, so any of these is accepted.
 *
 * HTTPS is required except on localhost. During development we use
 * http://localhost:5173, which browsers treat as a secure context.
 */

export interface Recording {
  blob: Blob;
  mimeType: string;
  durationMs: number;
  /** File extension matching the mimeType, e.g. "webm", "ogg", "mp4". */
  extension: string;
}

const CANDIDATE_MIME_TYPES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/ogg;codecs=opus",
  "audio/ogg",
  "audio/mp4",
];

function pickMimeType(): string | undefined {
  for (const candidate of CANDIDATE_MIME_TYPES) {
    if (typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(candidate)) {
      return candidate;
    }
  }
  return undefined;
}

function extensionFromMime(mimeType: string): string {
  if (mimeType.includes("webm")) return "webm";
  if (mimeType.includes("ogg")) return "ogg";
  if (mimeType.includes("mp4")) return "m4a";
  return "webm"; // Fallback: browsers default to webm when nothing else works.
}

export class MicrophoneRecorder {
  private mediaRecorder: MediaRecorder | null = null;
  private chunks: Blob[] = [];
  private startedAt = 0;
  private stream: MediaStream | null = null;
  private mimeType = "";

  /**
   * Request microphone access and begin recording.
   *
   * Throws a DOMException if the user denies permission or no microphone
   * is available. Callers should catch and show a friendly message.
   */
  async start(): Promise<void> {
    if (this.mediaRecorder) {
      throw new Error("Already recording.");
    }

    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    const chosen = pickMimeType();
    this.mediaRecorder = chosen
      ? new MediaRecorder(this.stream, { mimeType: chosen })
      : new MediaRecorder(this.stream);

    this.mimeType = this.mediaRecorder.mimeType || "audio/webm";
    this.chunks = [];
    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        this.chunks.push(event.data);
      }
    };

    this.startedAt = performance.now();
    this.mediaRecorder.start();
  }

  /**
   * Stop recording and return the captured audio.
   *
   * Resolves once the MediaRecorder has flushed its final chunk.
   */
  async stop(): Promise<Recording> {
    if (!this.mediaRecorder) {
      throw new Error("Not recording.");
    }

    const recorder = this.mediaRecorder;

    return new Promise<Recording>((resolve, reject) => {
      recorder.onstop = () => {
        try {
          const durationMs = Math.round(performance.now() - this.startedAt);
          const blob = new Blob(this.chunks, { type: this.mimeType });
          const extension = extensionFromMime(this.mimeType);

          // Release the microphone so the browser's "recording" indicator
          // disappears and the hardware is free for other apps.
          this.stream?.getTracks().forEach((track) => track.stop());
          this.stream = null;
          this.mediaRecorder = null;

          if (blob.size === 0) {
            reject(new Error("No audio was captured."));
            return;
          }

          resolve({ blob, mimeType: this.mimeType, durationMs, extension });
        } catch (err) {
          reject(err);
        }
      };

      recorder.onerror = (event) => {
        reject(event.error ?? new Error("Recording failed."));
      };

      recorder.stop();
    });
  }

  /** True if a recording is currently in progress. */
  isRecording(): boolean {
    return this.mediaRecorder !== null;
  }
}
