const avdName = process.env.DETOX_AVD_NAME || "Pixel_6_API_34";
const reactNativeArchitectures = process.env.DETOX_REACT_NATIVE_ARCHITECTURES || "x86_64";
const gradleWrapper = process.platform === "win32" ? "gradlew.bat" : "./gradlew";

function androidBuildCommand(buildVariant, testBuildType) {
  return [
    "npx expo prebuild --platform android --non-interactive",
    `cd android && ${gradleWrapper} assemble${buildVariant} assembleAndroidTest -DtestBuildType=${testBuildType} -PreactNativeArchitectures=${reactNativeArchitectures}`,
  ].join(" && ");
}

module.exports = {
  testRunner: {
    args: {
      $0: "jest",
      config: "e2e/jest.config.js",
    },
    jest: {
      setupTimeout: 120000,
    },
  },
  apps: {
    "android.debug": {
      type: "android.apk",
      binaryPath: "android/app/build/outputs/apk/debug/app-debug.apk",
      testBinaryPath: "android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk",
      build: androidBuildCommand("Debug", "debug"),
      reversePorts: [8081],
    },
    "android.release": {
      type: "android.apk",
      binaryPath: "android/app/build/outputs/apk/release/app-release.apk",
      testBinaryPath: "android/app/build/outputs/apk/androidTest/release/app-release-androidTest.apk",
      build: androidBuildCommand("Release", "release"),
    },
  },
  devices: {
    emulator: {
      type: "android.emulator",
      device: {
        avdName,
      },
    },
  },
  configurations: {
    "android.emu.debug": {
      device: "emulator",
      app: "android.debug",
    },
    "android.emu.release": {
      device: "emulator",
      app: "android.release",
    },
  },
};