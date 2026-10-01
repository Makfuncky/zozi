"use client";

import { useEffect, useCallback, useRef } from "react";
import { useComm } from "@/components/comms/CommShell";
import { useUnifiedInbox } from "@/hooks/useUnifiedInbox";
import { useThreadMessages } from "@/hooks/useThreadMessages";

/**
 * Replaces DataIngester — fetches real data from `/comms/unified-inbox`
 * and loads messages when a thread is selected.
 *
 * Renders nothing (returns null) — only wires data into CommShell context.
 */
export default function UnifiedInboxBridge() {
  const {
    setThreads,
    setMessages,
    activeThread,
    lens,
  } = useComm();

  // Fetch thread summaries from backend
  const {
    items: threads,
    loading: threadsLoading,
    error: threadsError,
    refetch: refetchThreads,
  } = useUnifiedInbox({ lens });

  // Fetch messages for the active thread
  const {
    messages,
    loading: messagesLoading,
    error: messagesError,
    loadMessages,
    clearMessages,
  } = useThreadMessages();

  // Push threads into context whenever they arrive
  const prevThreadsRef = useRef(threads);
  useEffect(() => {
    if (threads !== prevThreadsRef.current) {
      setThreads(threads);
      prevThreadsRef.current = threads;
    }
  }, [threads, setThreads]);

  // Push messages into context whenever they arrive
  const prevMessagesRef = useRef(messages);
  useEffect(() => {
    if (messages !== prevMessagesRef.current) {
      setMessages(messages);
      prevMessagesRef.current = messages;
    }
  }, [messages, setMessages]);

  // Load messages when active thread changes
  useEffect(() => {
    if (activeThread?.id) {
      loadMessages(activeThread.id, activeThread.transport);
    } else {
      clearMessages();
    }
  }, [activeThread?.id, activeThread?.transport, loadMessages, clearMessages]);

  // Expose loading/error state to the shell via CSS classes
  // so loading skeletons can react
  useEffect(() => {
    const shell = document.querySelector(".comm-shell");
    if (!shell) return;

    shell.classList.toggle("comm-threads-loading", threadsLoading && threads.length === 0);
    shell.classList.toggle("comm-threads-error", !!threadsError);
    shell.classList.toggle("comm-messages-loading", messagesLoading);
    shell.classList.toggle("comm-messages-error", !!messagesError);

    return () => {
      shell?.classList.remove("comm-threads-loading", "comm-threads-error", "comm-messages-loading", "comm-messages-error");
    };
  }, [threadsLoading, threadsError, messagesLoading, messagesError, threads.length]);

  // Listen for retry events from the Rail retry button
  useEffect(() => {
    const handler = () => refetchThreads();
    window.addEventListener("comm-refetch", handler);
    return () => window.removeEventListener("comm-refetch", handler);
  }, [refetchThreads]);

  return null;
}
