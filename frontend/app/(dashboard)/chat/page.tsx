"use client";

import { useEffect, useRef, useState } from "react";
import { Settings2, MessageSquare } from "lucide-react";
import { api } from "@/lib/api";
import { streamChatMessage } from "@/lib/chat-stream";
import type { ChatMessage, Conversation, DatabaseConnection, KnowledgeBase } from "@/lib/types";
import { ConversationList } from "@/components/chat/conversation-list";
import { MessageBubble } from "@/components/chat/message-bubble";
import { ChatInput } from "@/components/chat/chat-input";
import { SourcePicker } from "@/components/chat/source-picker";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Spinner, EmptyState } from "@/components/ui/feedback";

const STAGE_LABELS: Record<string, string> = {
  classify: "Figuring out what you need…",
  db_agent: "Querying the database…",
  rag_agent: "Searching your documents…",
  merge: "Putting it together…",
  answer: "Writing the answer…",
};

type DialogMode = "new" | "edit" | null;

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [connections, setConnections] = useState<DatabaseConnection[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [currentStage, setCurrentStage] = useState<string | null>(null);
  const [dialogMode, setDialogMode] = useState<DialogMode>(null);
  const [pendingConnectionIds, setPendingConnectionIds] = useState<string[]>([]);
  const [pendingKbIds, setPendingKbIds] = useState<string[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.get<Conversation[]>("/api/conversations").then(setConversations);
    api.get<DatabaseConnection[]>("/api/connections").then(setConnections);
    api.get<KnowledgeBase[]>("/api/knowledge-bases").then(setKnowledgeBases);
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, currentStage]);

  async function selectConversation(id: string) {
    const conversation = conversations.find((c) => c.id === id);
    if (!conversation) return;
    setActiveConversation(conversation);
    const msgs = await api.get<ChatMessage[]>(`/api/conversations/${id}/messages`);
    setMessages(msgs);
  }

  function openNewConversationDialog() {
    setPendingConnectionIds(connections.map((c) => c.id));
    setPendingKbIds(knowledgeBases.map((k) => k.id));
    setDialogMode("new");
  }

  function openEditSourcesDialog() {
    if (!activeConversation) return;
    setPendingConnectionIds(activeConversation.active_connection_ids);
    setPendingKbIds(activeConversation.active_knowledge_base_ids);
    setDialogMode("edit");
  }

  async function handleDialogConfirm() {
    if (dialogMode === "new") {
      const conversation = await api.post<Conversation>("/api/conversations", {
        active_connection_ids: pendingConnectionIds,
        active_knowledge_base_ids: pendingKbIds,
      });
      setConversations((prev) => [conversation, ...prev]);
      setActiveConversation(conversation);
      setMessages([]);
    } else if (dialogMode === "edit" && activeConversation) {
      const updated = await api.put<Conversation>(`/api/conversations/${activeConversation.id}/sources`, {
        active_connection_ids: pendingConnectionIds,
        active_knowledge_base_ids: pendingKbIds,
      });
      setActiveConversation(updated);
      setConversations((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    }
    setDialogMode(null);
  }

  async function handleSend(content: string) {
    if (!activeConversation) return;
    const optimisticUserMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      conversation_id: activeConversation.id,
      role: "user",
      content,
      detected_intent: null,
      status: "completed",
      error_message: null,
      created_at: new Date().toISOString(),
      citations: [],
    };
    setMessages((prev) => [...prev, optimisticUserMessage]);
    setIsSending(true);
    setCurrentStage("classify");

    await streamChatMessage(activeConversation.id, content, {
      onStage: (stage) => setCurrentStage(stage.node),
      onDone: (message) => {
        setMessages((prev) => [...prev, message]);
        setIsSending(false);
        setCurrentStage(null);
        setConversations((prev) =>
          prev.map((c) => (c.id === activeConversation.id ? { ...c, title: c.title ?? content.slice(0, 100) } : c))
        );
      },
      onError: (message) => {
        setMessages((prev) => [
          ...prev,
          {
            id: `error-${Date.now()}`,
            conversation_id: activeConversation.id,
            role: "assistant",
            content: "",
            detected_intent: null,
            status: "failed",
            error_message: message,
            created_at: new Date().toISOString(),
            citations: [],
          },
        ]);
        setIsSending(false);
        setCurrentStage(null);
      },
    });
  }

  const totalSources = activeConversation
    ? activeConversation.active_connection_ids.length + activeConversation.active_knowledge_base_ids.length
    : 0;

  return (
    <div className="flex h-full">
      <ConversationList
        conversations={conversations}
        activeId={activeConversation?.id ?? null}
        onSelect={selectConversation}
        onNew={openNewConversationDialog}
      />

      <div className="flex flex-1 flex-col">
        {activeConversation ? (
          <>
            <div className="flex items-center justify-between border-b border-border px-5 py-3">
              <p className="font-display font-medium text-ink">{activeConversation.title || "New conversation"}</p>
              <button
                onClick={openEditSourcesDialog}
                className="flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1.5 text-xs font-medium text-ink-muted hover:bg-surface-muted"
              >
                <Settings2 className="h-3.5 w-3.5" />
                {totalSources} source{totalSources === 1 ? "" : "s"}
              </button>
            </div>

            <div ref={scrollRef} className="flex-1 space-y-5 overflow-y-auto px-5 py-5">
              {messages.length === 0 && !currentStage && (
                <EmptyState
                  icon={MessageSquare}
                  title="Ask your first question"
                  description="Try: “How many orders came from Egypt last month?” or “What does the refund policy say?”"
                />
              )}
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
              {currentStage && (
                <div className="flex items-center gap-2 pl-10 text-xs text-ink-faint">
                  <Spinner className="h-3.5 w-3.5" />
                  {STAGE_LABELS[currentStage] ?? "Thinking…"}
                </div>
              )}
            </div>

            <ChatInput onSend={handleSend} isSending={isSending} />
          </>
        ) : (
          <div className="flex flex-1 items-center justify-center px-8">
            <EmptyState
              icon={MessageSquare}
              title="Select or start a conversation"
              description="Ask questions in plain English about your connected databases and uploaded documents."
              action={
                <Button size="sm" onClick={openNewConversationDialog}>
                  New conversation
                </Button>
              }
            />
          </div>
        )}
      </div>

      <Dialog open={dialogMode !== null} onClose={() => setDialogMode(null)} title={dialogMode === "new" ? "New conversation" : "Chat sources"}>
        <div className="space-y-4">
          <SourcePicker
            connections={connections}
            knowledgeBases={knowledgeBases}
            selectedConnectionIds={pendingConnectionIds}
            selectedKnowledgeBaseIds={pendingKbIds}
            onToggleConnection={(id) =>
              setPendingConnectionIds((prev) => (prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id]))
            }
            onToggleKnowledgeBase={(id) =>
              setPendingKbIds((prev) => (prev.includes(id) ? prev.filter((k) => k !== id) : [...prev, id]))
            }
          />
          <Button className="w-full" onClick={handleDialogConfirm}>
            {dialogMode === "new" ? "Start chatting" : "Save"}
          </Button>
        </div>
      </Dialog>
    </div>
  );
}
