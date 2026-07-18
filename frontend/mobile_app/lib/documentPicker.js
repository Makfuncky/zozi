// Web-compatible document picker polyfill
// This file is used as a replacement for expo-document-picker on web

// Web implementation using HTML file input
async function pickDocument(options = {}) {
  return new Promise((resolve) => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = options.types ? options.types.join(",") : ".pdf,.doc,.docx,.jpg,.jpeg,.png,.gif,.txt";
    input.onchange = () => {
      if (input.files && input.files[0]) {
        const file = input.files[0];
        resolve({
          canceled: false,
          assets: [{
            name: file.name,
            size: file.size,
            type: file.type,
            uri: URL.createObjectURL(file),
            mimeType: file.type,
          }],
        });
      } else {
        resolve({ canceled: true, assets: [] });
      }
    };
    input.oncancel = () => resolve({ canceled: true, assets: [] });
    document.body.appendChild(input);
    input.click();
    document.body.removeChild(input);
  });
}

// Check if we're in a web browser
const isWeb = typeof window !== "undefined";

export const getDocumentAsync = isWeb ? pickDocument : async () => ({ canceled: true, assets: [] });
export const launchImageLibraryAsync = isWeb ? pickDocument : async () => ({ canceled: true, assets: [] });

export default { getDocumentAsync, launchImageLibraryAsync };