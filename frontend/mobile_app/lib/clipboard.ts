// Web-compatible clipboard polyfill
// This file is used as a replacement for expo-clipboard on web

// Web implementation using navigator.clipboard API
async function setStringAsyncWeb(text: string): Promise<void> {
  if (typeof window !== "undefined" && navigator?.clipboard) {
    try {
      await navigator.clipboard.writeText(text);
      return;
    } catch (err) {
      console.warn("navigator.clipboard.writeText failed, falling back to execCommand");
    }
  }
  
  // Fallback for older browsers
  const textarea = document.createElement("textarea");
  textarea.value = text;
  document.body.appendChild(textarea);
  textarea.select();
  try {
    document.execCommand("copy");
  } finally {
    document.body.removeChild(textarea);
  }
}

// Check if we're in a web browser
const isWeb = typeof window !== "undefined";

// For web, use our polyfill; for native, use the real expo-clipboard
let Clipboard: { setStringAsync: (text: string) => Promise<void> };

if (isWeb) {
  Clipboard = { setStringAsync: setStringAsyncWeb };
} else {
  // On native, we need to dynamically import
  Clipboard = {
    async setStringAsync(text: string) {
      const ClipboardModule = await import("expo-clipboard");
      await ClipboardModule.setStringAsync(text);
    }
  };
}

export const setStringAsync = Clipboard.setStringAsync;
export default Clipboard;