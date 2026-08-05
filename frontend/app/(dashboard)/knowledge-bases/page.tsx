"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FolderOpen, Plus, FileText } from "lucide-react";
import { api } from "@/lib/api";
import type { KnowledgeBase } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Card } from "@/components/ui/card";
import { Spinner, EmptyState } from "@/components/ui/feedback";
import { KnowledgeBaseForm } from "@/components/kb/kb-form";

export default function KnowledgeBasesPage() {
  const [kbs, setKbs] = useState<KnowledgeBase[] | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  useEffect(() => {
    api.get<KnowledgeBase[]>("/api/knowledge-bases").then(setKbs);
  }, []);

  function handleCreated(kb: KnowledgeBase) {
    setKbs((prev) => [kb, ...(prev ?? [])]);
    setIsDialogOpen(false);
  }

  return (
    <div className="mx-auto max-w-3xl px-8 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="font-display text-xl font-semibold text-ink">Knowledge bases</h1>
          <p className="mt-1 text-sm text-ink-muted">Upload documents to chat with them - contracts, policies, reports.</p>
        </div>
        <Button onClick={() => setIsDialogOpen(true)}>
          <Plus className="h-4 w-4" />
          New knowledge base
        </Button>
      </div>

      {kbs === null ? (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      ) : kbs.length === 0 ? (
        <EmptyState
          icon={FolderOpen}
          title="No knowledge bases yet"
          description="Create one and upload a PDF, Word doc, or spreadsheet to chat with it."
          action={
            <Button onClick={() => setIsDialogOpen(true)} size="sm">
              <Plus className="h-4 w-4" />
              New knowledge base
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {kbs.map((kb) => (
            <Link key={kb.id} href={`/knowledge-bases/${kb.id}`}>
              <Card className="h-full p-4 transition-colors hover:border-accent">
                <div className="flex items-start gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-accent-soft text-accent">
                    <FolderOpen className="h-4 w-4" />
                  </div>
                  <div className="min-w-0">
                    <p className="truncate font-medium text-ink">{kb.name}</p>
                    {kb.description && <p className="mt-0.5 line-clamp-2 text-xs text-ink-muted">{kb.description}</p>}
                    <p className="mt-2 flex items-center gap-1 text-xs text-ink-faint">
                      <FileText className="h-3 w-3" />
                      {kb.file_count} file{kb.file_count === 1 ? "" : "s"}
                    </p>
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}

      <Dialog open={isDialogOpen} onClose={() => setIsDialogOpen(false)} title="New knowledge base">
        <KnowledgeBaseForm onCreated={handleCreated} />
      </Dialog>
    </div>
  );
}
