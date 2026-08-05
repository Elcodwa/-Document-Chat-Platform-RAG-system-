"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { api } from "@/lib/api";
import type { KbFile, KnowledgeBase } from "@/lib/types";
import { FileUpload } from "@/components/kb/file-upload";
import { FileRow } from "@/components/kb/file-row";
import { Spinner } from "@/components/ui/feedback";

export default function KnowledgeBaseDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [kb, setKb] = useState<KnowledgeBase | null>(null);
  const [files, setFiles] = useState<KbFile[] | null>(null);

  useEffect(() => {
    api.get<KnowledgeBase>(`/api/knowledge-bases/${params.id}`).then(setKb);
    api.get<KbFile[]>(`/api/knowledge-bases/${params.id}/files`).then(setFiles);
  }, [params.id]);

  function handleUploaded(file: KbFile) {
    setFiles((prev) => [file, ...(prev ?? [])]);
    setKb((prev) => (prev ? { ...prev, file_count: prev.file_count + 1 } : prev));
  }

  async function handleDelete(fileId: string) {
    await api.delete(`/api/knowledge-bases/${params.id}/files/${fileId}`);
    setFiles((prev) => (prev ?? []).filter((f) => f.id !== fileId));
  }

  return (
    <div className="mx-auto max-w-3xl px-8 py-8">
      <button
        onClick={() => router.push("/knowledge-bases")}
        className="mb-4 flex items-center gap-1.5 text-sm font-medium text-ink-muted hover:text-ink"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Knowledge bases
      </button>

      {kb ? (
        <div className="mb-6">
          <h1 className="font-display text-xl font-semibold text-ink">{kb.name}</h1>
          {kb.description && <p className="mt-1 text-sm text-ink-muted">{kb.description}</p>}
        </div>
      ) : (
        <div className="mb-6 h-12" />
      )}

      <div className="mb-6">
        <FileUpload knowledgeBaseId={params.id} onUploaded={handleUploaded} />
      </div>

      {files === null ? (
        <div className="flex justify-center py-10">
          <Spinner />
        </div>
      ) : files.length === 0 ? (
        <p className="py-6 text-center text-sm text-ink-faint">No files uploaded yet.</p>
      ) : (
        <ul className="space-y-2">
          {files.map((file) => (
            <FileRow key={file.id} file={file} onDelete={handleDelete} />
          ))}
        </ul>
      )}
    </div>
  );
}
