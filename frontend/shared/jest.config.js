/** @type {import('ts-jest').JestConfigWithTsJest} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src'],
  testRegex: '(/__tests__/.*|(\\.|/)(test|spec))\\.(ts|tsx)$',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@shared/(.*)$': '<rootDir>/src/$1',
    // Resolve .web.tsx variants for component tests
    '^(.*)\\.web$': '$1.web',
  },
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', {
      tsconfig: {
        jsx: 'react-jsx'
      }
    }],
    '^.+\\.js$': 'ts-jest'
  },
  transformIgnorePatterns: [
    'node_modules/(?!(node-fetch)/)'
  ]
};
