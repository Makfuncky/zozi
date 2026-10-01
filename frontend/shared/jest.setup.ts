import "@testing-library/jest-dom";
import React from 'react';
import { TextEncoder, TextDecoder } from 'util';
import { act } from '@testing-library/react';

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

// Polyfill for TextEncoder/TextDecoder
(globalThis as any).TextEncoder = TextEncoder;
(globalThis as any).TextDecoder = TextDecoder as any;

// Polyfill for Response, Request, etc.
class MockResponse {
  constructor(body: any, init?: ResponseInit) {
    this.body = body;
    this.status = init?.status ?? 200;
    this.ok = this.status >= 200 && this.status < 300;
  }
  body: any;
  status: number;
  ok: boolean;
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

// Use act from @testing-library/react for React 19 compatibility
(globalThis as any).act = act;
