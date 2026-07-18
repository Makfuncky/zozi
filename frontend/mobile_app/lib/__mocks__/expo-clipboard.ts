// Mock for clipboard in Jest tests
const Clipboard = {
  setStringAsync: jest.fn().mockResolvedValue(undefined),
  getStringAsync: jest.fn().mockResolvedValue(""),
  hasStringAsync: jest.fn().mockResolvedValue(false),
};

export default Clipboard;
export const setStringAsync = Clipboard.setStringAsync;
export const getStringAsync = Clipboard.getStringAsync;
export const hasStringAsync = Clipboard.hasStringAsync;
