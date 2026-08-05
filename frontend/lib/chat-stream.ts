import { API_URL } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

export interface ChatStage {
  node: string;
  intent?: string | null;
}

export async function streamChatMessage(
  conversationId: string,
  content: string,
  handlers: {
    onStage: (stage: ChatStage) => void;
    onDone: (message: ChatMessage) => void;
    onError: (message: string) => void;
  }
): Promise<void> {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/conversations/${conversationId}/messages/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ content }),
    });
  } catch {
    handlers.onError("Could not reach the server. Is the backend running?");
    return;
  }

  if (!response.ok || !response.body) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body?.detail) message = body.detail;
    } catch {
      // ignore
    }
    handlers.onError(message);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const rawEvent = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);

      const eventMatch = rawEvent.match(/^event: (.+)$/m);
      const dataMatch = rawEvent.match(/^data: (.+)$/m);
      if (dataMatch) {
        const eventName = eventMatch?.[1] ?? "message";
        try {
          const data = JSON.parse(dataMatch[1]);
          if (eventName === "done") handlers.onDone(data as ChatMessage);
          else if (eventName === "stage") handlers.onStage(data as ChatStage);
        } catch {
          // ignore malformed chunk
        }
      }
      boundary = buffer.indexOf("\n\n");
    }
  }
}
