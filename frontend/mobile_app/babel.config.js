module.exports = function (api) {
  api.cache(true);
  return {
    // `unstable_transformImportMeta` rewrites `import.meta` (used by some deps such as
    // zustand's devtools middleware) to a safe global. Without it the classic-script
    // web bundle throws `SyntaxError: Cannot use 'import.meta' outside a module`,
    // which crashes the whole app to a blank screen.
    presets: [["babel-preset-expo", { unstable_transformImportMeta: true }]],
    plugins: [
      [
        "babel-plugin-module-resolver",
        {
          root: ["./"],
          extensions: [".ios.js", ".android.js", ".js", ".ts", ".tsx", ".json"],
          alias: {
            "@": "./",
            "@shared": "../shared/dist",
          },
        },
      ],
      "react-native-reanimated/plugin",
    ],
  };
};
