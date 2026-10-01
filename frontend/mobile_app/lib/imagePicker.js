// Web-compatible image picker polyfill
// This file is used as a replacement for expo-image-picker on web

// Web implementation using HTML file input
async function pickImage(options = {}) {
  return new Promise((resolve) => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "image/*";
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
            width: 0,
            height: 0,
            aspectRatio: 1,
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

export const launchImageLibraryAsync = isWeb ? pickImage : async () => ({ canceled: true, assets: [] });
export const launchCameraAsync = isWeb ? pickImage : async () => ({ canceled: true, assets: [] });
export const getImageUrlAsync = async () => ({ localUri: "" });

export default { 
  launchImageLibraryAsync, 
  launchCameraAsync,
  getImageUrlAsync,
};