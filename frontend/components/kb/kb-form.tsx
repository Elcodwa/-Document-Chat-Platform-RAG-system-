"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { KnowledgeBase } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, Textarea } from "@/components/ui/textarea";

export function KnowledgeBaseForm({ onCreated }: { onCreated: (kb: KnowledgeBase) => void }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const kb = await api.post<KnowledgeBase>("/api/knowledge-bases", { name, description: description || undefined });
      onCreated(kb);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create the knowledge base.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="kb-name">Name</Label>
        <Input id="kb-name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="Contracts" />
      </div>
      <div>
        <Label htmlFor="kb-desc">Description (optional)</Label>
        <Textarea
          id="kb-desc"
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Signed customer contracts and policy documents."
        />
      </div>
      {error && <p className="rounded-md bg-danger-soft px-3 py-2 text-sm text-danger">{error}</p>}
      <Button type="submit" className="w-full" isLoading={isSubmitting}>
        Create knowledge base
      </Button>
    </form>
  );
}
