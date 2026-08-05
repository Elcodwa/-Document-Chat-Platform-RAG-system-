"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, ShieldCheck, ShieldAlert, Database } from "lucide-react";
import type { QueryExecutionDetail } from "@/lib/types";
import { cn } from "@/lib/utils";

export function SqlPanel({ query }: { query: QueryExecutionDetail }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const passed = query.validation_status === "passed";

  return (
    <div
      className={cn(
        "overflow-hidden rounded-md border-l-[3px] bg-surface-muted",
        passed ? "border-l-success" : "border-l-danger"
      )}
    >
      <button
        onClick={() => setIsExpanded((v) => !v)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left"
      >
        {isExpanded ? <ChevronDown className="h-3.5 w-3.5 text-ink-faint" /> : <ChevronRight className="h-3.5 w-3.5 text-ink-faint" />}
        <Database className="h-3.5 w-3.5 text-ink-faint" />
        <span className="flex-1 truncate font-mono text-xs text-ink-muted">
          {query.referenced_tables?.length ? query.referenced_tables.join(", ") : "query"}
        </span>
        {passed ? (
          <span className="flex items-center gap-1 text-xs font-medium text-success">
            <ShieldCheck className="h-3.5 w-3.5" />
            {query.execution_status === "success" ? `${query.returned_row_count ?? 0} rows` : "validated"}
          </span>
        ) : (
          <span className="flex items-center gap-1 text-xs font-medium text-danger">
            <ShieldAlert className="h-3.5 w-3.5" />
            blocked
          </span>
        )}
      </button>

      {isExpanded && (
        <div className="space-y-3 border-t border-border/60 px-3 py-3">
          <div>
            <p className="mb-1 text-xs font-medium uppercase tracking-wide text-ink-faint">Executed SQL</p>
            <pre className="overflow-x-auto rounded-md bg-ink px-3 py-2 font-mono text-xs text-white">
              {query.normalized_sql || query.generated_sql}
            </pre>
          </div>

          {!passed && query.validation_errors.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-medium uppercase tracking-wide text-ink-faint">Blocked because</p>
              <ul className="list-inside list-disc space-y-0.5 text-xs text-danger">
                {query.validation_errors.map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
            </div>
          )}

          {passed && query.execution_status === "success" && query.result_preview && (
            <div>
              <p className="mb-1 text-xs font-medium uppercase tracking-wide text-ink-faint">Result preview</p>
              <div className="overflow-x-auto rounded-md border border-border">
                <table className="w-full text-left font-mono text-xs">
                  <thead className="bg-surface text-ink-faint">
                    <tr>
                      {query.result_preview.columns.map((col) => (
                        <th key={col} className="whitespace-nowrap px-2 py-1.5 font-medium">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {query.result_preview.rows.map((row, i) => (
                      <tr key={i} className="border-t border-border">
                        {query.result_preview!.columns.map((col) => (
                          <td key={col} className="whitespace-nowrap px-2 py-1.5 text-ink-muted">
                            {String(row[col] ?? "—")}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {passed && query.execution_status !== "success" && (
            <p className="text-xs text-danger">{query.error_message || "Execution failed."}</p>
          )}
        </div>
      )}
    </div>
  );
}
