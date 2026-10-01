import '@testing-library/jest-dom';
import React from 'react';
import { act } from '@testing-library/react';
import { TextEncoder, TextDecoder } from 'util';

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

// Polyfill for TextEncoder/TextDecoder
(globalThis as any).TextEncoder = TextEncoder;
(globalThis as any).TextDecoder = TextDecoder as any;

// Polyfill for Response, Request, etc.
class MockResponse {
  constructor(body: any, init?: ResponseInit) {
    this.body = body;
    this.status = init?.status ?? 200;
    this.statusText = (init?.status ?? 200) === 200 ? 'OK' : 'Error';
    this.ok = this.status >= 200 && this.status < 300;
    this.headers = new Map();
  }
  body: any;
  status: number;
  statusText: string;
  ok: boolean;
  headers: Map<string, string>;
  json() { return Promise.resolve(typeof this.body === 'string' ? JSON.parse(this.body) : this.body); }
  text() { return Promise.resolve(typeof this.body === 'string' ? this.body : JSON.stringify(this.body)); }
  arrayBuffer() { return Promise.resolve(new ArrayBuffer(0)); }
  blob() { return Promise.resolve(new Blob()); }
}

(globalThis as any).Response = MockResponse;
(globalThis as any).Request = class MockRequest {
  constructor(input: any, init?: RequestInit) {
    this.input = input;
    this.init = init ?? {};
  }
  input: any;
  init: RequestInit;
};
(globalThis as any).fetch = jest.fn();

// Use act from @testing-library/react
(global as any).act = act;

// Polyfill for ResizeObserver (missing in jsdom)
class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
(globalThis as any).ResizeObserver = ResizeObserver;

// Polyfill for matchMedia (missing in jsdom)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});
