const originalError = console.error;

beforeAll(() => {
  jest.spyOn(console, "error").mockImplementation((...args: unknown[]) => {
    const first = args[0];
    if (typeof first === "string" && first.includes("react-test-renderer is deprecated")) {
      return;
    }
    originalError(...(args as Parameters<typeof console.error>));
  });
});

afterAll(() => {
  const mock = console.error as unknown as { mockRestore?: () => void };
  mock.mockRestore?.();
});
