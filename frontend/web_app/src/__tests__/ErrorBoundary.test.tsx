import React from "react";
import { render, screen } from "@testing-library/react";
import ErrorBoundary from "@/components/ErrorBoundary";

function Bomb(): React.ReactElement {
  throw new Error("boom");
}

test("ErrorBoundary shows fallback when a child throws", () => {
  const consoleError = jest.spyOn(console, "error").mockImplementation(() => {});

  render(
    <ErrorBoundary>
      <Bomb />
    </ErrorBoundary>
  );

  expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
  expect(screen.getAllByText(/boom/i).length).toBeGreaterThan(0);
  expect(screen.getByText(/Error handling window/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();

  consoleError.mockRestore();
});


