"use client";

import { useEffect, useState } from "react";
import { Database, Plus } from "lucide-react";
import { api } from "@/lib/api";
import type { DatabaseConnection } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Spinner, EmptyState } from "@/components/ui/feedback";
import { ConnectionForm } from "@/components/connections/connection-form";
import { ConnectionCard } from "@/components/connections/connection-card";

export default function ConnectionsPage() {
  const [connections, setConnections] = useState<DatabaseConnection[] | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  useEffect(() => {
    api.get<DatabaseConnection[]>("/api/connections").then(setConnections);
  }, []);

  function handleCreated(connection: DatabaseConnection) {
    setConnections((prev) => [connection, ...(prev ?? [])]);
    setIsDialogOpen(false);
  }

  return (
    <div className="mx-auto max-w-3xl px-8 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="font-display text-xl font-semibold text-ink">Connections</h1>
          <p className="mt-1 text-sm text-ink-muted">
            Connect a live database so you can ask questions about its data in chat.
          </p>
        </div>
        <Button onClick={() => setIsDialogOpen(true)}>
          <Plus className="h-4 w-4" />
          New connection
        </Button>
      </div>

      {connections === null ? (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      ) : connections.length === 0 ? (
        <EmptyState
          icon={Database}
          title="No connections yet"
          description="Add your first database connection to start asking questions about your data."
          action={
            <Button onClick={() => setIsDialogOpen(true)} size="sm">
              <Plus className="h-4 w-4" />
              New connection
            </Button>
          }
        />
      ) : (
        <div className="space-y-3">
          {connections.map((connection) => (
            <ConnectionCard key={connection.id} connection={connection} />
          ))}
        </div>
      )}

      <Dialog open={isDialogOpen} onClose={() => setIsDialogOpen(false)} title="New database connection">
        <ConnectionForm onCreated={handleCreated} />
      </Dialog>
    </div>
  );
}
