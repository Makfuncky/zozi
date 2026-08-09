// Cross-platform clipboard utility
// Works on web and mobile

async function setStringAsync(text) {
  // Web implementation
  if (typeof window !== "undefined" && navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(text);
      return;
    } catch (err) {
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
  }
  // On mobile, this function is replaced by expo-clipboard at runtime
  return;
}

export { setStringAsync };
export default { setStringAsync };