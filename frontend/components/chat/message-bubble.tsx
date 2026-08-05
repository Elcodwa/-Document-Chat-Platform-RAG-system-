"use client";

import { useEffect, useState } from "react";
import { FileText, User, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import type { ChatMessage, QueryExecutionDetail } from "@/lib/types";
import { SqlPanel } from "@/components/chat/sql-panel";
import { cn } from "@/lib/utils";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const databaseCitation = message.citations.find((c) => c.citation_type === "database");
  const documentCitations = message.citations.filter((c) => c.citation_type === "document");
  const [queryDetail, setQueryDetail] = useState<QueryExecutionDetail | null>(null);

  useEffect(() => {
    if (databaseCitation) {
      api.get<QueryExecutionDetail | null>(`/api/conversations/messages/${message.id}/sql`).then(setQueryDetail);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [message.id]);

  return (
    <div className={cn("flex gap-3", isUser && "flex-row-reverse")}>
      <div
        className={cn(
          "flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-surface-muted text-ink-muted" : "bg-accent text-white"
        )}
      >
        {isUser ? <User className="h-3.5 w-3.5" /> : <Sparkles className="h-3.5 w-3.5" />}
      </div>

      <div className={cn("max-w-[75%] space-y-2", isUser && "flex flex-col items-end")}>
        <div
          className={cn(
            "rounded-lg px-3.5 py-2.5 text-sm leading-relaxed",
            isUser ? "bg-accent text-white" : "border border-border bg-surface text-ink"
          )}
        >
          {message.status === "completed" || isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <p className="text-danger">{message.error_message || "Something went wrong."}</p>
          )}
        </div>

        {!isUser && queryDetail && <SqlPanel query={queryDetail} />}

        {!isUser && documentCitations.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {documentCitations.map((c) => (
              <span
                key={c.id}
                className="flex items-center gap-1 rounded-full border border-border bg-surface px-2 py-0.5 text-xs text-ink-muted"
              >
                <FileText className="h-3 w-3" />
                {c.title}
                {c.page_number ? `, p.${c.page_number}` : ""}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
