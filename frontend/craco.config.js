// CRACO is used ONLY to adjust the production webpack build (`craco build`).
// `npm start` / `npm test` still run vanilla react-scripts, so local dev and
// the test runner are unaffected.
//
// Why this exists: CRA's `CI=true` flag (set automatically on CI servers)
// escalates BOTH our ESLint warnings AND every webpack compilation warning to
// build-breaking errors. We WANT the former — our own lint warnings must fail
// the build — but a third-party transitive warning shouldn't.
//
// `react-datepicker`'s compiled bundle does a dynamic `require()` of its locale
// files, which webpack reports as:
//   "Critical dependency: the request of a dependency is an expression"
// That warning lives entirely in node_modules and there's nothing to fix on
// our side. `ignoreWarnings` drops it from the compilation stats so CI=true no
// longer treats it as an error — while leaving our ESLint warnings (surfaced by
// eslint-webpack-plugin) fully intact.
module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      webpackConfig.ignoreWarnings = [
        ...(webpackConfig.ignoreWarnings || []),
        (warning) => {
          const message = String(warning?.message || '');
          if (!/Critical dependency: the request of a dependency is an expression/.test(message)) {
            return false;
          }
          // Only silence it for third-party code — never suppress the same
          // warning if it ever originates from our own src/.
          const resource = String(
            warning?.module?.resource
            || warning?.module?.userRequest
            || (typeof warning?.module?.identifier === 'function' ? warning.module.identifier() : '')
            || '',
          );
          return /[\\/]node_modules[\\/]/.test(resource) || !/[\\/]src[\\/]/.test(resource);
        },
      ];
      return webpackConfig;
    },
  },
};
