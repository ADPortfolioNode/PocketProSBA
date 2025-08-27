module.exports = {
  testEnvironment: 'jsdom',
  transformIgnorePatterns: [
    'node_modules/(?!(axios)/)'
  ],
  moduleNameMapping: {
    '^axios$': 'axios/dist/node/axios.cjs'
  }
};
