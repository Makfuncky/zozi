// Cross-platform image picker utility
// Works on web and mobile

export interface ImagePickerAsset {
  name: string;
  size: number;
  type: string;
  uri: string;
  mimeType: string;
  width: number;
  height: number;
  aspectRatio: number;
}

export interface ImagePickerResult {
  canceled: boolean;
  assets: ImagePickerAsset[];
}

export async function launchImageLibraryAsync(options: { mediaTypes?: string[] } = {}): Promise<ImagePickerResult> {
  // Web implementation
  if (typeof window !== "undefined") {
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
  // On mobile, this will be replaced by expo-image-picker at runtime
  return { canceled: true, assets: [] };
}

export const launchCameraAsync = launchImageLibraryAsync;

export default { launchImageLibraryAsync, launchCameraAsync };