// React polyfill for Expo Web to fix module resolution issues
// This ensures React exports are properly accessible for both default and named imports

// NOTE: do NOT use require('react') here — Metro aliases 'react' to this very
// file, which would create a circular dependency and leave createContext undefined.
// Require the real React package by relative path so the alias is bypassed.
const React = require('../node_modules/react');

// Ensure all React functions are accessible both ways
const normalizedReact = {
  ...React,
  // Make sure createContext is directly accessible
  createContext: React.createContext,
  use: React.use,
  useCallback: React.useCallback,
  useContext: React.useContext,
  useEffect: React.useEffect,
  useLayoutEffect: React.useLayoutEffect,
  useMemo: React.useMemo,
  useReducer: React.useReducer,
  useRef: React.useRef,
  useState: React.useState,
  Component: React.Component,
  PureComponent: React.PureComponent,
  Fragment: React.Fragment,
  Profiler: React.Profiler,
  memo: React.memo,
  lazy: React.lazy,
  forwardRef: React.forwardRef,
  Suspense: React.Suspense,
  SuspenseList: React.SuspenseList,
};

// Support both default and named imports
module.exports = normalizedReact;
module.exports.default = normalizedReact;
module.exports.__esModule = true;