import React from "react";
import { render } from "@testing-library/react";
import { Providers } from "@/app/providers";

beforeEach(() => {
  const { useQueryStateStore } = require("@/lib/api/queryStates");
  useQueryStateStore.setState({
    queries: {},
    refetchCallbacks: {},
    unhandledError: null,
  });
});

describe("providers", () => {
  test("test_providers_use_zustand_not_react_query", () => {
    const fs = require("fs");
    const path = require("path");
    const providersPath = path.resolve(__dirname, "../../src/app/providers.tsx");
    const content = fs.readFileSync(providersPath, "utf-8");
    expect(content).not.toContain("@tanstack/react-query");

    const { container } = render(
      <Providers>
        <div data-testid="child">Hello</div>
      </Providers>
    );
    expect(container.querySelector('[data-testid="child"]')).toHaveTextContent("Hello");
  });
});
