// Dynamic Expo config.
//
// Expo loads `app.json` first and passes its resolved `expo` object here as
// `config`. We override the web bundler output to "single" (SPA / client-side
// rendering) instead of "static" (SSR/SSG).
//
// Why: running this React Native app on web via SSR triggers server-only React
// resolution issues ("React.default.createContext is not a function"). A mobile
// app preview only needs client-side rendering, so SPA mode is both simpler and
// more robust, and it removes the whole SSR code path.
module.exports = ({ config }) => ({
  ...config,
  web: {
    ...(config.web || {}),
    output: "single",
  },
});
