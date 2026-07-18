process.env.NODE_ENV = 'test';

/** @type {import('ts-jest').JestConfigWithTsJest} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src'],
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/app/(.*)$': '<rootDir>/src/app/$1',
    '^@/lib/(.*)$': '<rootDir>/src/lib/$1',
    '^@/components/(.*)$': '<rootDir>/src/components/$1',
    '^@/hooks/(.*)$': '<rootDir>/src/hooks/$1',
    '@shared/(.*)$': '<rootDir>/../shared/src/$1',
    '^nanoid$': '<rootDir>/src/__mocks__/nanoid.ts'
  },
  transformIgnorePatterns: [
    '/node_modules/(?!(nanoid)/)'
  ],
  modulePaths: ['<rootDir>/node_modules'],
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', {
      tsconfig: {
        jsx: 'react-jsx'
      }
    }],
    '^.+\\.js$': 'ts-jest'
  }
};
