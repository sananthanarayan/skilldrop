const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
  entry: {
    app: ['./src/polyfills.js', './src/app/index.jsx'],
    landing: ['./src/polyfills.js', './src/landing/index.jsx'],
  },
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: '[name].[contenthash:6].js',
    publicPath: '/static/',
  },
  resolve: { extensions: ['.js', '.jsx'] },
  module: {
    rules: [{ test: /\.jsx?$/, exclude: /node_modules/, use: 'babel-loader' }],
  },
  optimization: {
    runtimeChunk: 'single',
    splitChunks: {
      cacheGroups: {
        // one cacheable vendor file for everything
        vendors: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'initial',
        },
      },
    },
  },
  plugins: [
    new HtmlWebpackPlugin({ filename: 'index.html', chunks: ['app'] }),
    new HtmlWebpackPlugin({ filename: 'welcome.html', chunks: ['landing'] }),
  ],
};
