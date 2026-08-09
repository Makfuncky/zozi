// Web-compatible sharing polyfill
// This file is used as a replacement for expo-sharing on web

const Sharing = {
  isAvailableAsync: async () => {
    return typeof navigator !== "undefined" && !!navigator.share;
  },
  
  shareAsync: async (url, options = {}) => {
    if (typeof navigator !== "undefined" && navigator.share) {
      try {
        await navigator.share({
          title: options.dialogTitle || "Share",
          url: url,
        });
        return;
      } catch (error) {
        console.warn("Web Share API failed:", error);
      }
    }
    // Fallback: open in new tab
    if (typeof window !== "undefined") {
      window.open(url, "_blank");
    }
  },
  
  shareSingleAsync: async () => {
    // Not supported on web
  },
  
  prepareSingleShareAsync: async () => {
    // Not supported on web
  },
};

export default Sharing;