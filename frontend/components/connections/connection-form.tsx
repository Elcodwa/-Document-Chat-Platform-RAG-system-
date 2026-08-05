"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { DatabaseConnection } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";

const DEFAULT_PORTS: Record<string, number> = { postgresql: 5432, mysql: 3306 };

export function ConnectionForm({ onCreated }: { onCreated: (connection: DatabaseConnection) => void }) {
  const [name, setName] = useState("");
  const [databaseType, setDatabaseType] = useState("postgresql");
  const [host, setHost] = useState("");
  const [port, setPort] = useState(String(DEFAULT_PORTS.postgresql));
  const [databaseName, setDatabaseName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const connection = await api.post<DatabaseConnection>("/api/connections", {
        name,
        database_type: databaseType,
        host,
        port: Number(port),
        database_name: databaseName,
        username,
        password,
      });
      onCreated(connection);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create the connection.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="conn-name">Connection name</Label>
        <Input id="conn-name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="Production DB" />
      </div>

      <div>
        <Label htmlFor="conn-type">Database type</Label>
        <Select
          id="conn-type"
          value={databaseType}
          onChange={(e) => {
            setDatabaseType(e.target.value);
            setPort(String(DEFAULT_PORTS[e.target.value] ?? ""));
          }}
        >
          <option value="postgresql">PostgreSQL</option>
          <option value="mysql">MySQL</option>
        </Select>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="col-span-2">
          <Label htmlFor="conn-host">Host</Label>
          <Input id="conn-host" required value={host} onChange={(e) => setHost(e.target.value)} placeholder="localhost" />
        </div>
        <div>
          <Label htmlFor="conn-port">Port</Label>
          <Input id="conn-port" required type="number" value={port} onChange={(e) => setPort(e.target.value)} />
        </div>
      </div>

      <div>
        <Label htmlFor="conn-db">Database name</Label>
        <Input
          id="conn-db"
          required
          value={databaseName}
          onChange={(e) => setDatabaseName(e.target.value)}
          placeholder="demo_business"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label htmlFor="conn-user">Username</Label>
          <Input id="conn-user" required value={username} onChange={(e) => setUsername(e.target.value)} />
        </div>
        <div>
          <Label htmlFor="conn-pass">Password</Label>
          <Input id="conn-pass" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
      </div>

      {error && <p className="rounded-md bg-danger-soft px-3 py-2 text-sm text-danger">{error}</p>}

      <Button type="submit" className="w-full" isLoading={isSubmitting}>
        Create connection
      </Button>
    </form>
  );
}
