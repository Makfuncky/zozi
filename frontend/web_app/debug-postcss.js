const path = require('path');
const config = require('lilconfig');
const req = require('./node_modules/postcss-load-config/src/req.js');
const interopRequireDefault = (obj) => obj && obj.__esModule ? obj : { default: obj }

const plugins = (config, file) => {
  let plugins = []

  if (Array.isArray(config.plugins)) {
    plugins = config.plugins.filter(Boolean)
  } else {
    plugins = Object.keys(config.plugins)
      .filter((plugin) => {
        return config.plugins[plugin] !== false ? plugin : ''
      })
      .map((plugin) => {
        return req(plugin, file)
      })
  }

  console.log('raw plugins:', plugins.map(p => typeof p));

  if (plugins.length && plugins.length > 0) {
    plugins.forEach((plugin, i) => {
      console.log('plugin', i, 'before:', typeof plugin, 'postcss:', plugin.postcss, 'default:', !!plugin.default);
      if (plugin.default) {
        plugin = plugin.default
        console.log('after default:', typeof plugin, 'postcss:', plugin.postcss);
      }

      if (plugin.postcss === true) {
        plugin = plugin()
        console.log('after call:', typeof plugin, 'postcssPlugin:', plugin.postcssPlugin);
      } else if (plugin.postcss) {
        plugin = plugin.postcss
      }

      console.log('plugin', i, 'after:', typeof plugin, 'postcssPlugin:', plugin.postcssPlugin);

      if (
        !(
          (typeof plugin === 'object' && Array.isArray(plugin.plugins)) ||
          (typeof plugin === 'object' && plugin.postcssPlugin) ||
          (typeof plugin === 'function')
        )
      ) {
        throw new TypeError(`Invalid PostCSS Plugin found at: plugins[${i}]\n\n(@${file})`)
      }
    })
  }

  return plugins
}

config.lilconfig('postcss').search(path.resolve('.')).then(result => {
  const file = result.filepath || ''
  let config = interopRequireDefault(result.config).default || {}
  return plugins(config, file);
}).catch(err => {
  console.error('ERROR:', err.message);
});
