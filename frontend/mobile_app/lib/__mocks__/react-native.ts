/**
 * Global jest mock for react-native.
 * Used in the ts-jest / node environment where native modules are unavailable.
 * Tests that need specific behaviour can override with jest.mock("react-native", ...).
 */

const Platform = {
  OS: "android" as const,
  select: <T extends Record<string, unknown>>(obj: T): T[keyof T] | undefined => {
    return (obj as any)["android"] ?? (obj as any)["default"] ?? undefined;
  },
  isPad: false,
  isTVOS: false,
  Version: 31,
};

const noop = (): null => null;

const StyleSheet = {
  create: <T extends Record<string, object>>(styles: T): T => styles,
  flatten: (style: unknown): unknown => style,
  hairlineWidth: 1,
  absoluteFillObject: { position: "absolute", left: 0, right: 0, top: 0, bottom: 0 },
};

const AnimatedValue = jest.fn().mockImplementation(() => ({
  setValue: jest.fn(),
  interpolate: jest.fn(() => ({})),
  addListener: jest.fn(),
  removeAllListeners: jest.fn(),
}));

const Animated = {
  View: noop,
  Text: noop,
  Image: noop,
  ScrollView: noop,
  FlatList: noop,
  Value: AnimatedValue,
  timing: jest.fn(() => ({ start: jest.fn() })),
  spring: jest.fn(() => ({ start: jest.fn() })),
  loop: jest.fn(() => ({ start: jest.fn(), stop: jest.fn() })),
  sequence: jest.fn(() => ({ start: jest.fn() })),
  parallel: jest.fn(() => ({ start: jest.fn() })),
  createAnimatedComponent: (comp: unknown): unknown => comp,
  event: jest.fn(),
};

module.exports = {
  Platform,
  StyleSheet,
  Animated,
  View: noop,
  Text: noop,
  TouchableOpacity: noop,
  TouchableHighlight: noop,
  TouchableWithoutFeedback: noop,
  TouchableNativeFeedback: noop,
  Pressable: noop,
  ScrollView: noop,
  FlatList: noop,
  SectionList: noop,
  VirtualizedList: noop,
  Image: noop,
  ImageBackground: noop,
  TextInput: noop,
  Modal: noop,
  ActivityIndicator: noop,
  RefreshControl: noop,
  SafeAreaView: noop,
  KeyboardAvoidingView: noop,
  StatusBar: noop,
  Switch: noop,
  Slider: noop,
  Alert: {
    alert: jest.fn(),
    prompt: jest.fn(),
  },
  Dimensions: {
    get: (): { width: number; height: number } => ({ width: 375, height: 812 }),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
  },
  Share: {
    share: jest.fn().mockResolvedValue({ action: "sharedAction" }),
  },
  Linking: {
    openURL: jest.fn().mockResolvedValue(undefined),
    canOpenURL: jest.fn().mockResolvedValue(true),
    getInitialURL: jest.fn().mockResolvedValue(null),
    addEventListener: jest.fn(),
  },
  Keyboard: {
    dismiss: jest.fn(),
    addListener: jest.fn(),
    removeListener: jest.fn(),
  },
  AppState: {
    addEventListener: jest.fn(() => ({ remove: jest.fn() })),
    currentState: "active",
  },
  Easing: {
    linear: jest.fn((v: unknown) => v),
    ease: jest.fn((v: unknown) => v),
    in: jest.fn(() => jest.fn()),
    out: jest.fn(() => jest.fn()),
    inOut: jest.fn(() => jest.fn()),
    bounce: jest.fn(),
    bezier: jest.fn(),
  },
  NativeModules: {},
  NativeEventEmitter: jest.fn().mockImplementation(() => ({
    addListener: jest.fn(() => ({ remove: jest.fn() })),
    removeListener: jest.fn(),
    removeAllListeners: jest.fn(),
    emit: jest.fn(),
  })),
  DeviceEventEmitter: {
    addListener: jest.fn(() => ({ remove: jest.fn() })),
    removeAllListeners: jest.fn(),
    emit: jest.fn(),
  },
  PixelRatio: {
    get: (): number => 2,
    getPixelSizeForLayoutSize: (size: number): number => size * 2,
    roundToNearestPixel: (size: number): number => size,
    getFontScale: (): number => 1,
  },
  AccessibilityInfo: {
    isScreenReaderEnabled: jest.fn().mockResolvedValue(false),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
  },
  BackHandler: {
    addEventListener: jest.fn(() => ({ remove: jest.fn() })),
    removeEventListener: jest.fn(),
    exitApp: jest.fn(),
  },
  I18nManager: {
    isRTL: false,
    allowRTL: jest.fn(),
    forceRTL: jest.fn(),
  },
  useColorScheme: jest.fn(() => "dark"),
  useWindowDimensions: jest.fn(() => ({ width: 375, height: 812, fontScale: 1, scale: 2 })),
};
