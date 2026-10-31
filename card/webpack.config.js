const path = require('path');

module.exports = {
  mode: 'production',
  entry: path.resolve(__dirname, 'src', 'diy-plants-card.ts'),
  output: {
    filename: 'diy-plants-card.js',
    path: path.resolve(__dirname, '..', 'custom_components', 'diy_plants', 'frontend'),
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: {
          loader: 'ts-loader',
          options: {
            compilerOptions: { noEmit: false },
          },
        },
        exclude: /node_modules/,
      },
    ],
  },
  resolve: { extensions: ['.ts', '.js'] },
};
