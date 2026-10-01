import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { ExpoSecureStorage } from "@/lib/expoSecureStorage";

export interface ChatMessage {
  id: string;
  text: string;
  isBot: boolean;
  time: string;
  products?: any[];
  suggestedPrompts?: string[];
  resultMode?: "none" | "exact" | "close";
  translateText?: boolean;
  translatePrompts?: boolean;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: ChatMessage[];
}

interface ChatbotStoreState {
  sessions: ChatSession[];
  activeSessionId: string | null;
  getSession: (id: string) => ChatSession | undefined;
  createSession: (initialMessage?: string) => ChatSession;
  addMessage: (sessionId: string, message: ChatMessage) => void;
  updateSessionTitle: (sessionId: string, title: string) => void;
  deleteSession: (id: string) => void;
  clearSessions: () => void;
  setActiveSession: (id: string | null) => void;
  getActiveSession: () => ChatSession | undefined;
}

function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substr(2, 9);
}

function generateTitle(firstUserMessage: string): string {
  const truncated = firstUserMessage.length > 30 ? firstUserMessage.slice(0, 30) + "..." : firstUserMessage;
  return truncated || "New Conversation";
}

export const useChatbotStore = create<ChatbotStoreState>()(
  persist(
    (set, get) => ({
      sessions: [],
      activeSessionId: null,

      getSession: (id) => {
        return get().sessions.find((s) => s.id === id);
      },

      createSession: (initialMessage?: string) => {
        const newSession: ChatSession = {
          id: generateId(),
          title: initialMessage ? generateTitle(initialMessage) : "New Conversation",
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          messages: initialMessage
            ? [
                {
                  id: generateId(),
                  text: initialMessage,
                  isBot: false,
                  time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                },
              ]
            : [],
        };

        set((state) => ({
          sessions: [...state.sessions, newSession],
          activeSessionId: newSession.id,
        }));

        return newSession;
      },

      addMessage: (sessionId, message) => {
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === sessionId
              ? {
                  ...s,
                  messages: [...s.messages, message],
                  updatedAt: new Date().toISOString(),
                }
              : s
          ),
        }));
      },

      updateSessionTitle: (sessionId, title) => {
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === sessionId ? { ...s, title } : s
          ),
        }));
      },

      deleteSession: (id) => {
        set((state) => ({
          sessions: state.sessions.filter((s) => s.id !== id),
          activeSessionId: state.activeSessionId === id ? null : state.activeSessionId,
        }));
      },

      clearSessions: () => {
        set({ sessions: [], activeSessionId: null });
      },

      setActiveSession: (id) => {
        set({ activeSessionId: id });
      },

      getActiveSession: () => {
        const { activeSessionId, sessions } = get();
        if (!activeSessionId) return undefined;
        return sessions.find((s) => s.id === activeSessionId);
      },
    }),
    {
      name: "chatbot-storage",
      storage: createJSONStorage(() => ExpoSecureStorage),
    }
  )
);

export function useChatbotSessions() {
  return useChatbotStore((s) => s.sessions);
}

export function useChatbotActiveSession() {
  return useChatbotStore((s) => s.getActiveSession());
}

export function useChatbotActions() {
  return useChatbotStore((s) => ({
    getSession: s.getSession,
    createSession: s.createSession,
    addMessage: s.addMessage,
    updateSessionTitle: s.updateSessionTitle,
    deleteSession: s.deleteSession,
    clearSessions: s.clearSessions,
    setActiveSession: s.setActiveSession,
  }));
}