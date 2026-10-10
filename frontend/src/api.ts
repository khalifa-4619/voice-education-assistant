/**
 * HTTP client for the Voice Education Assistant backend.
 *
 * This module knows only how to talk to the backend. It knows nothing
 * about React or about how the UI is structured. Keeping this separation
 * means the UI can change without touching HTTP, and vice versa.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export interface AskResponse {
  interaction_id: string;
  transcript: string;
  answer: string;
  asr_seconds: number;
  llm_seconds: number;
  total_seconds: number;
  started_at: string;
}

export interface FeedbackPayload {
  interaction_id: string;
  useful: boolean;
  language: string;
  subject: string;
  notes: string;
}

export interface FeedbackResponse {
  recorded: boolean;
  interaction_id: string;
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

async function _handleResponse<T>(response: Response): Promise<T> {
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
  return (await response.json()) as T;
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
  } catch {
    throw new ApiError(
      0,
      "Could not reach the backend. Is the server running on " + API_BASE + "?"
    );
  }

  return _handleResponse<AskResponse>(response);
}

export async function submitFeedback(
  payload: FeedbackPayload
): Promise<FeedbackResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/v1/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError(
      0,
      "Could not reach the backend to submit feedback."
    );
  }

  return _handleResponse<FeedbackResponse>(response);
}
