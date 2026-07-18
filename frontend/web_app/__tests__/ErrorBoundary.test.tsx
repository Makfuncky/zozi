import React from "react";
import { render, screen } from "@testing-library/react";
import ErrorBoundary from "@shared/components/ui/ErrorBoundary";

// The compiled shared/dist declaration cannot resolve `react` from its own
// location (skipLibCheck hides that), so the class's Component base degrades to
// an error type and trips the JSX element-type check. The component is valid at
// runtime; re-assert it as a proper JSX element type for the test only.
const Boundary = ErrorBoundary as unknown as React.ComponentType<{ children: React.ReactNode }>;

function Bomb(): React.ReactElement {
  throw new Error("boom");
}

test("ErrorBoundary shows fallback when a child throws", () => {
  render(
    <Boundary>
      <Bomb />
    </Boundary>
  );

  expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
  expect(screen.getByText(/boom/i)).toBeInTheDocument();
});
