// Cross-platform file system utility
// Works on web and mobile

const fileStorage: Record<string, { content: string; encoding: string }> = {};

const FileSystem = {
  // Basic file system operations
  getInfoAsync: async (fileId: string) => {
    const info = fileStorage[fileId];
    return info || { exists: false };
  },
  
  readAsStringAsync: async (fileId: string, options?: { encoding?: string }) => {
    return fileStorage[fileId]?.content || "";
  },
  
  writeAsStringAsync: async (fileId: string, content: string, options?: { encoding?: string }) => {
    fileStorage[fileId] = { content, encoding: options?.encoding || "utf8" };
  },
  
  deleteAsync: async (fileId: string) => {
    delete fileStorage[fileId];
  },
  
  // Legacy API
  getLocalUriForSource: async (source: { uri?: string }) => {
    return source?.uri || "";
  },
  
  // Additional methods
  makeDirectoryAsync: async () => {
    // No-op on web
  },
  
  downloadAsync: async (url: string, _fileUri?: string) => {
    const response = await fetch(url);
    const blob = await response.blob();
    const url2 = URL.createObjectURL(blob);
    return { uri: url2, md5: "", headers: {} };
  },
  
  uploadAsync: async (url: string, options?: { body?: unknown }) => {
    const formData = new FormData();
    if (options?.body) {
      formData.append("file", options.body as Blob);
    }
    const response = await fetch(url, {
      method: "POST",
      body: formData,
    });
    return { status: response.status, body: await response.text() };
  },
  
  // Directory handling
  documentDirectory: "file:///document/",
  libraryDirectory: "file:///library/",
  cacheDirectory: "file:///cache/",
  
  // Utility methods
  encodeBase64: async (text: string) => btoa(text),
  decodeBase64: async (base64: string) => atob(base64),
};

// Named exports for namespace import compatibility
export const getInfoAsync = FileSystem.getInfoAsync;
export const readAsStringAsync = FileSystem.readAsStringAsync;
export const writeAsStringAsync = FileSystem.writeAsStringAsync;
export const deleteAsync = FileSystem.deleteAsync;
export const getLocalUriForSource = FileSystem.getLocalUriForSource;
export const makeDirectoryAsync = FileSystem.makeDirectoryAsync;
export const downloadAsync = FileSystem.downloadAsync;
export const uploadAsync = FileSystem.uploadAsync;
export const documentDirectory = FileSystem.documentDirectory;
export const libraryDirectory = FileSystem.libraryDirectory;
export const cacheDirectory = FileSystem.cacheDirectory;
export const encodeBase64 = FileSystem.encodeBase64;
export const decodeBase64 = FileSystem.decodeBase64;

export default FileSystem;