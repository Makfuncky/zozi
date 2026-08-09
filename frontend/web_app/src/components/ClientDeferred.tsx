"use client";

import dynamic from "next/dynamic";

// Heavy, browser-only widgets are loaded client-side only to keep them out of
// the server-rendered HTML and reduce the initial JS/server work.
const BackgroundEffect = dynamic(() => import("@/components/BackgroundEffect"), { ssr: false });
const Chatbot = dynamic(() => import("@/components/Chatbot"), { ssr: false });

export function DeferredBackgroundEffect() {
  return <BackgroundEffect />;
}

export function DeferredChatbot() {
  return <Chatbot />;
}
