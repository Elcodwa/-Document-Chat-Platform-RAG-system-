"use client";

import { Plus, MessageSquare } from "lucide-react";
import type { Conversation } from "@/lib/types";
import { cn } from "@/lib/utils";
import { formatRelativeTime } from "@/lib/utils";

export function ConversationList({
  conversations,
  activeId,
  onSelect,
  onNew,
}: {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
}) {
  return (
    <div className="flex h-full w-64 shrink-0 flex-col border-r border-border">
      <div className="border-b border-border p-3">
        <button
          onClick={onNew}
          className="flex w-full items-center justify-center gap-2 rounded-md border border-border bg-surface px-3 py-2 text-sm font-medium text-ink hover:bg-surface-muted"
        >
          <Plus className="h-4 w-4" />
          New conversation
        </button>
      </div>
      <div className="flex-1 space-y-1 overflow-y-auto p-2">
        {conversations.length === 0 && (
          <p className="px-2 py-4 text-center text-xs text-ink-faint">No conversations yet.</p>
        )}
        {conversations.map((c) => (
          <button
            key={c.id}
            onClick={() => onSelect(c.id)}
            className={cn(
              "flex w-full items-start gap-2 rounded-md px-2.5 py-2 text-left transition-colors",
              activeId === c.id ? "bg-accent-soft" : "hover:bg-surface-muted"
            )}
          >
            <MessageSquare className={cn("mt-0.5 h-3.5 w-3.5 shrink-0", activeId === c.id ? "text-accent" : "text-ink-faint")} />
            <div className="min-w-0 flex-1">
              <p className={cn("truncate text-sm", activeId === c.id ? "font-medium text-accent" : "text-ink")}>
                {c.title || "New conversation"}
              </p>
              {c.last_message_at && <p className="text-xs text-ink-faint">{formatRelativeTime(c.last_message_at)}</p>}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
