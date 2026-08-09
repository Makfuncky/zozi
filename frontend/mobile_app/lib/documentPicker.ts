// Cross-platform document picker utility
// Works on web and mobile

export interface DocumentPickerAsset {
  name: string;
  size?: number;
  type?: string;
  uri: string;
  mimeType?: string;
}

export interface DocumentPickerResult {
  canceled: boolean;
  assets: DocumentPickerAsset[];
}

export async function getDocumentAsync(options: { types?: string[] } = {}): Promise<DocumentPickerResult> {
  // Web implementation
  if (typeof window !== "undefined") {
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
  // On mobile, this will be replaced by expo-document-picker at runtime
  return { canceled: true, assets: [] };
}

export const launchImageLibraryAsync = getDocumentAsync;

export default { getDocumentAsync, launchImageLibraryAsync };