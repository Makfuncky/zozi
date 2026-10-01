const { getDefaultConfig } = require("expo/metro-config");
const path = require("path");
const fs = require("fs");

const projectRoot = __dirname;
const sharedPath = path.resolve(projectRoot, "../shared");

const config = getDefaultConfig(projectRoot);

// Allow Metro to resolve files outside of the mobile app root
config.watchFolders = config.watchFolders || [];
config.watchFolders.push(sharedPath);

// Exclude problematic directories from being watched
config.watchIgnorePatterns = [
  ...(config.watchIgnorePatterns || []),
  /expo-modules-core[\\\/].*/,
  /expo-module-gradle-plugin/,
];

// Dereference pnpm symlinks so Metro resolves a single, real React instance.
// (Previously this pointed at polyfills/react.js, which aliased 'react' back to
// itself and broke React.createContext. Pointing at the real package fixes that.)
const resolveReal = (p) => fs.realpathSync(path.resolve(projectRoot, p));
config.resolver.extraNodeModules = {
  react: resolveReal("node_modules/react"),
  "react-dom": resolveReal("node_modules/react-dom"),
  // The `@zozi/shared` package (frontend/shared/dist) is built outside the
  // mobile app and imports `react-native` / `react-native-svg`. Under pnpm's
  // strict, isolated node_modules layout those modules are not resolvable from
  // within shared/dist, so Metro fails with "Unable to resolve module
  // react-native". Map them back to the app's own (dereferenced) installs.
  "react-native": resolveReal("node_modules/react-native"),
  "react-native-svg": resolveReal("node_modules/react-native-svg"),
};

// Force `react` to its full build during SSR. Expo/Metro resolve `react` with the
// `react-server` export condition for the server bundle, which points at
// `react.shared-subset.js` — that subset has NO `createContext`, so React Navigation
// (and anything using context) crashes with "React.createContext is not a function".
// Intercept the request and return the complete React entry instead.
const realReactDir = resolveReal("node_modules/react");
config.resolver.resolveRequest = (ctx, moduleName, platform, moduleType) => {
  if (moduleName === "react") {
    return { filePath: path.join(realReactDir, "index.js"), type: "sourceFile" };
  }
  if (moduleName === "react/jsx-runtime") {
    return { filePath: path.join(realReactDir, "jsx-runtime.js"), type: "sourceFile" };
  }
  if (moduleName === "react/jsx-dev-runtime") {
    return { filePath: path.join(realReactDir, "jsx-dev-runtime.js"), type: "sourceFile" };
  }
  return ctx.resolveRequest(ctx, moduleName, platform, moduleType);
};

module.exports = config;