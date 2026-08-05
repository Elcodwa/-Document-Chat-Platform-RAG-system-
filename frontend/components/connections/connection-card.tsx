"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, Table2, RefreshCw, Zap } from "lucide-react";
import { api } from "@/lib/api";
import type { ConnectionTestResult, DatabaseConnection, DatabaseTable, SchemaSyncResult } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/card";
import { Spinner } from "@/components/ui/feedback";
import { cn } from "@/lib/utils";

function statusTone(status: string): "success" | "danger" | "neutral" {
  if (status === "connected") return "success";
  if (status === "error") return "danger";
  return "neutral";
}

export function ConnectionCard({ connection: initial }: { connection: DatabaseConnection }) {
  const [connection, setConnection] = useState(initial);
  const [isExpanded, setIsExpanded] = useState(false);
  const [tables, setTables] = useState<DatabaseTable[] | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [testResult, setTestResult] = useState<ConnectionTestResult | null>(null);

  async function handleTest() {
    setIsTesting(true);
    setTestResult(null);
    try {
      const result = await api.post<ConnectionTestResult>(`/api/connections/${connection.id}/test`);
      setTestResult(result);
      setConnection((c) => ({ ...c, status: result.success ? "connected" : "error", last_test_message: result.message }));
    } finally {
      setIsTesting(false);
    }
  }

  async function handleSync() {
    setIsSyncing(true);
    try {
      const result = await api.post<SchemaSyncResult>(`/api/connections/${connection.id}/sync-schema`);
      setConnection((c) => ({ ...c, schema_sync_status: "completed" }));
      if (isExpanded) await loadTables();
      setTestResult({ success: true, message: `Synced ${result.table_count} tables, ${result.column_count} columns.`, server_version: null });
    } finally {
      setIsSyncing(false);
    }
  }

  async function toggleExpand() {
    const next = !isExpanded;
    setIsExpanded(next);
    if (next && tables === null) await loadTables();
  }

  async function loadTables() {
    const result = await api.get<DatabaseTable[]>(`/api/connections/${connection.id}/tables`);
    setTables(result);
  }

  return (
    <div className="rounded-lg border border-border bg-surface">
      <div className="flex items-center justify-between px-4 py-3">
        <button onClick={toggleExpand} className="flex flex-1 items-center gap-2.5 text-left">
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 shrink-0 text-ink-faint" />
          ) : (
            <ChevronRight className="h-4 w-4 shrink-0 text-ink-faint" />
          )}
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <p className="truncate font-medium text-ink">{connection.name}</p>
              <Badge tone={statusTone(connection.status)}>{connection.status}</Badge>
            </div>
            <p className="truncate font-mono text-xs text-ink-faint">
              {connection.database_type} · {connection.host}:{connection.port}/{connection.database_name}
            </p>
          </div>
        </button>
        <div className="flex shrink-0 gap-2">
          <Button variant="secondary" size="sm" onClick={handleTest} isLoading={isTesting}>
            <Zap className="h-3.5 w-3.5" />
            Test
          </Button>
          <Button variant="secondary" size="sm" onClick={handleSync} isLoading={isSyncing}>
            <RefreshCw className="h-3.5 w-3.5" />
            Sync schema
          </Button>
        </div>
      </div>

      {testResult && (
        <div
          className={cn(
            "mx-4 mb-3 rounded-md px-3 py-2 text-xs",
            testResult.success ? "bg-success-soft text-success" : "bg-danger-soft text-danger"
          )}
        >
          {testResult.message}
        </div>
      )}

      {isExpanded && (
        <div className="border-t border-border px-4 py-3">
          {tables === null ? (
            <div className="flex justify-center py-6">
              <Spinner />
            </div>
          ) : tables.length === 0 ? (
            <p className="py-4 text-center text-sm text-ink-faint">
              No tables synced yet - click &quot;Sync schema&quot; to discover tables.
            </p>
          ) : (
            <ul className="space-y-2">
              {tables.map((table) => (
                <li key={table.id} className="rounded-md bg-surface-muted px-3 py-2">
                  <div className="flex items-center gap-2 font-mono text-sm text-ink">
                    <Table2 className="h-3.5 w-3.5 text-ink-faint" />
                    {table.schema_name}.{table.table_name}
                    {table.estimated_row_count !== null && (
                      <span className="text-xs text-ink-faint">~{table.estimated_row_count.toLocaleString()} rows</span>
                    )}
                  </div>
                  <p className="mt-1 font-mono text-xs text-ink-faint">
                    {table.columns.map((c) => c.column_name).join(", ")}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
