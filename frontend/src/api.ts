/**
 * HTTP client for the Voice Education Assistant backend.
 *
 * This module knows only how to talk to the backend. It knows nothing
 * about React or about how the UI is structured. Keeping this separation
 * means the UI can change without touching HTTP, and vice versa.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export interface AskResponse {
  transcript: string;
  answer: string;
  asr_seconds: number;
  llm_seconds: number;
  total_seconds: number;
  started_at: string;
}

export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(`HTTP ${status}: ${detail}`);
    this.status = status;
    this.detail = detail;
  }
}

export async function ask(audio: File): Promise<AskResponse> {
  const form = new FormData();
  form.append("audio", audio);

  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/v1/ask`, {
      method: "POST",
      body: form,
    });
  } catch (networkError) {
    throw new ApiError(
      0,
      "Could not reach the backend. Is the server running on " + API_BASE + "?"
    );
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      // Response was not JSON; keep the status text.
    }
    throw new ApiError(response.status, detail);
  }

  return (await response.json()) as AskResponse;
}
