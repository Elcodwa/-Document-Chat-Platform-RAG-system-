"use client";

import { useRef, useState } from "react";
import { Upload } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { KbFile } from "@/lib/types";
import { cn } from "@/lib/utils";

const ACCEPTED_EXTENSIONS = ".pdf,.docx,.xlsx,.xls,.csv,.txt,.md";

export function FileUpload({ knowledgeBaseId, onUploaded }: { knowledgeBaseId: string; onUploaded: (file: KbFile) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function uploadFile(file: File) {
    setError(null);
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const uploaded = await api.upload<KbFile>(`/api/knowledge-bases/${knowledgeBaseId}/files`, formData);
      onUploaded(uploaded);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed.");
    } finally {
      setIsUploading(false);
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) uploadFile(file);
  }

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "flex cursor-pointer flex-col items-center gap-2 rounded-lg border-2 border-dashed px-6 py-8 text-center transition-colors",
          isDragging ? "border-accent bg-accent-soft" : "border-border hover:border-border-strong"
        )}
      >
        <Upload className="h-5 w-5 text-ink-faint" />
        <p className="text-sm text-ink-muted">
          <span className="font-medium text-accent">Click to upload</span> or drag and drop
        </p>
        <p className="text-xs text-ink-faint">PDF, Word, Excel, CSV, or text files, up to 25MB</p>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS}
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) uploadFile(file);
            e.target.value = "";
          }}
        />
      </div>
      {isUploading && <p className="mt-2 text-xs text-ink-muted">Uploading and processing…</p>}
      {error && <p className="mt-2 rounded-md bg-danger-soft px-3 py-2 text-sm text-danger">{error}</p>}
    </div>
  );
}
