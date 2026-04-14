const webpack = require('webpack');
azertt
module.exports = function override(config, env) {
    config.resolve.fallback = {
        url: require.resolve('url/'),
        util: require.resolve('util/'),
        buffer: require.resolve('buffer/'),
        path: require.resolve('path-browserify'),
        fs: require.resolve('fs'),
        assert: require.resolve('assert/'),
        http: require.resolve('stream-http'),
        https: require.resolve('https-browserify'),
        os: require.resolve('os-browserify/browser'),
        buffer: require.resolve('buffer'),
        stream: require.resolve('stream-browserify'),
        zlib: require.resolve('browserify-zlib'),
        os: require.resolve('os-browserify/browser'),
        crypto: require.resolve('crypto-browserify'),        
    };    
    config.plugins.push(
        new webpack.ProvidePlugin({
            process: 'process/browser',
            Buffer: ['buffer', 'Buffer'],
        }),
        new webpack.SourceMapDevToolPlugin({
            test: new RegExp('\.[js|css|mjs].*')
        })
    );
    config.module = {
        rules: [
          {
            test: /\.js$/,
            enforce: "pre",
            use: ["source-map-loader"],
          },
          {
            test: /\.scss$/, 
            use: [ 'style-loader', 'css-loader', 'sass-loader' ]
          }
        ],
    },
    config.ignoreWarnings = [/Failed to parse source map/]
    
    return config;
}