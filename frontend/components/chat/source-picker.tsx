"use client";

import { Database, FolderOpen } from "lucide-react";
import type { DatabaseConnection, KnowledgeBase } from "@/lib/types";
import { cn } from "@/lib/utils";

export function SourcePicker({
  connections,
  knowledgeBases,
  selectedConnectionIds,
  selectedKnowledgeBaseIds,
  onToggleConnection,
  onToggleKnowledgeBase,
}: {
  connections: DatabaseConnection[];
  knowledgeBases: KnowledgeBase[];
  selectedConnectionIds: string[];
  selectedKnowledgeBaseIds: string[];
  onToggleConnection: (id: string) => void;
  onToggleKnowledgeBase: (id: string) => void;
}) {
  return (
    <div className="space-y-4">
      <div>
        <p className="mb-2 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-ink-faint">
          <Database className="h-3 w-3" />
          Databases
        </p>
        {connections.length === 0 ? (
          <p className="text-xs text-ink-faint">No connections yet.</p>
        ) : (
          <div className="space-y-1">
            {connections.map((c) => (
              <label
                key={c.id}
                className={cn(
                  "flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-sm",
                  selectedConnectionIds.includes(c.id) ? "bg-accent-soft text-accent" : "text-ink-muted hover:bg-surface-muted"
                )}
              >
                <input
                  type="checkbox"
                  className="accent-[var(--accent)]"
                  checked={selectedConnectionIds.includes(c.id)}
                  onChange={() => onToggleConnection(c.id)}
                />
                {c.name}
              </label>
            ))}
          </div>
        )}
      </div>

      <div>
        <p className="mb-2 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-ink-faint">
          <FolderOpen className="h-3 w-3" />
          Knowledge bases
        </p>
        {knowledgeBases.length === 0 ? (
          <p className="text-xs text-ink-faint">No knowledge bases yet.</p>
        ) : (
          <div className="space-y-1">
            {knowledgeBases.map((kb) => (
              <label
                key={kb.id}
                className={cn(
                  "flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-sm",
                  selectedKnowledgeBaseIds.includes(kb.id) ? "bg-accent-soft text-accent" : "text-ink-muted hover:bg-surface-muted"
                )}
              >
                <input
                  type="checkbox"
                  className="accent-[var(--accent)]"
                  checked={selectedKnowledgeBaseIds.includes(kb.id)}
                  onChange={() => onToggleKnowledgeBase(kb.id)}
                />
                {kb.name}
              </label>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
