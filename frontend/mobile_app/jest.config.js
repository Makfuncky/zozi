/** @type {import('ts-jest').JestConfigWithTsJest} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/lib'],
  testRegex: '(/__tests__/.*\\.(test|spec)|(.|/)(test|spec))\\.(ts|tsx)$',
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', { tsconfig: { jsx: 'react-jsx' } }],
  },
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
    '^@shared/(.*)$': '<rootDir>/../shared/dist/$1',
    '^expo-clipboard$': '<rootDir>/lib/__mocks__/expo-clipboard.ts',
    '^expo-linear-gradient$': '<rootDir>/lib/__mocks__/expo-linear-gradient.ts',
    '^react-native$': '<rootDir>/lib/__mocks__/react-native.ts',
  },
  setupFilesAfterEnv: ['<rootDir>/lib/__tests__/jest.setup.ts'],
  clearMocks: true,
  testPathIgnorePatterns: ['/node_modules/', '/.expo/'],
  modulePaths: ['<rootDir>/node_modules'],
};
