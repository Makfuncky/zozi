// Cross-platform sharing utility
// Works on web and mobile

const Sharing = {
  isAvailableAsync: async () => {
    return typeof navigator !== "undefined" && !!navigator.share;
  },
  
  shareAsync: async (url: string, options?: { dialogTitle?: string }) => {
    if (typeof navigator !== "undefined" && navigator.share) {
      try {
        await navigator.share({
          title: options?.dialogTitle || "Share",
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

// Named exports for namespace import compatibility
export const isAvailableAsync = Sharing.isAvailableAsync;
export const shareAsync = Sharing.shareAsync;
export const shareSingleAsync = Sharing.shareSingleAsync;
export const prepareSingleShareAsync = Sharing.prepareSingleShareAsync;

export default Sharing;