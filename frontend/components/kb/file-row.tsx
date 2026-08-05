import { FileText, CheckCircle2, XCircle, Loader2, Trash2 } from "lucide-react";
import type { KbFile } from "@/lib/types";
import { Badge } from "@/components/ui/card";
import { formatBytes, formatRelativeTime } from "@/lib/utils";

const STATUS_CONFIG = {
  pending: { tone: "neutral" as const, icon: Loader2, label: "Queued" },
  processing: { tone: "warning" as const, icon: Loader2, label: "Processing" },
  completed: { tone: "success" as const, icon: CheckCircle2, label: "Ready" },
  failed: { tone: "danger" as const, icon: XCircle, label: "Failed" },
};

export function FileRow({ file, onDelete }: { file: KbFile; onDelete: (fileId: string) => void }) {
  const config = STATUS_CONFIG[file.processing_status];
  const Icon = config.icon;

  return (
    <li className="flex items-center gap-3 rounded-md border border-border px-3 py-2.5">
      <FileText className="h-4 w-4 shrink-0 text-ink-faint" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-ink">{file.original_name}</p>
        <p className="text-xs text-ink-faint">
          {formatBytes(file.file_size_bytes)} · {formatRelativeTime(file.created_at)}
          {file.processing_error && <span className="text-danger"> · {file.processing_error}</span>}
        </p>
      </div>
      <Badge tone={config.tone}>
        <Icon className={`h-3 w-3 ${file.processing_status === "processing" ? "animate-spin" : ""}`} />
        {config.label}
      </Badge>
      <button
        onClick={() => onDelete(file.id)}
        aria-label={`Delete ${file.original_name}`}
        className="rounded-md p-1.5 text-ink-faint hover:bg-danger-soft hover:text-danger"
      >
        <Trash2 className="h-3.5 w-3.5" />
      </button>
    </li>
  );
}
