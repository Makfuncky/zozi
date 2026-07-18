const launchMode = process.env.DETOX_LAUNCH_MODE || "bundled";
const packagerUrl = process.env.DETOX_PACKAGER_URL || "http://127.0.0.1:8081";
const devClientUrl = `exp+zozi://expo-development-client/?url=${encodeURIComponent(packagerUrl)}`;

beforeEach(async () => {
  if (launchMode === "dev-client") {
    await device.launchApp({ newInstance: true, delete: true, url: devClientUrl });
    return;
  }

  await device.launchApp({ newInstance: true, delete: true });
}, 180000);