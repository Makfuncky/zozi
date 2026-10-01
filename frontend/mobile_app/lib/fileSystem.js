// Web-compatible file system polyfill
// This file is used as a replacement for expo-file-system on web

// Web implementation using localStorage or memory storage
const fileStorage = {};

const FileSystem = {
  // Basic file system operations
  getInfoAsync: async (fileId) => {
    const info = fileStorage[fileId];
    return info || { exists: false };
  },
  
  readAsStringAsync: async (fileId, options = {}) => {
    return fileStorage[fileId]?.content || "";
  },
  
  writeAsStringAsync: async (fileId, content, options = {}) => {
    fileStorage[fileId] = { content, encoding: options.encoding || "utf8" };
  },
  
  deleteAsync: async (fileId) => {
    delete fileStorage[fileId];
  },
  
  // Legacy API
  getLocalUriForSource: async (source) => {
    return source?.uri || "";
  },
  
  // Additional methods
  makeDirectoryAsync: async () => {
    // No-op on web
  },
  
  downloadAsync: async (url) => {
    const response = await fetch(url);
    const blob = await response.blob();
    const url2 = URL.createObjectURL(blob);
    return { uri: url2, md5: "", headers: {} };
  },
  
  uploadAsync: async (url, options) => {
    const formData = new FormData();
    if (options?.body) {
      formData.append("file", options.body);
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
  encodeBase64: async (text) => btoa(text),
  decodeBase64: async (base64) => atob(base64),
};

export default FileSystem;