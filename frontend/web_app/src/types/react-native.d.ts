declare module 'react-native' {
  import * as React from 'react';
  export const View: React.FC<React.ComponentProps<'div'>>;
  export const Text: React.FC<React.ComponentProps<'span'>>;
  export const Image: React.FC<React.ComponentProps<'img'> & { source: any }>;
  export const StyleSheet: {
    create: (styles: Record<string, React.CSSProperties>) => Record<string, React.CSSProperties>;
  };
  export const TouchableOpacity: React.FC<React.ComponentProps<'button'>>;
  export const ScrollView: React.FC<React.ComponentProps<'div'>>;
  export const TextInput: React.FC<React.ComponentProps<'input'>>;
  export const ActivityIndicator: React.FC<{ size?: number | 'small' | 'large'; color?: string }>;
  export const Platform: { select: <T>(obj: Record<string, T>) => T; OS: string };
  export const Dimensions: { get: (dim: 'window' | 'screen') => { width: number; height: number } };
  export const StatusBar: React.FC<{ barStyle?: 'light-content' | 'dark-content' }>;
  export const SafeAreaView: React.FC<React.ComponentProps<'div'>>;
  export const Pressable: React.FC<React.ComponentProps<'button'>>;
  export const Modal: React.FC<React.ComponentProps<'dialog'>>;
  export const FlatList: React.FC<{ data: any[]; renderItem: (info: { item: any }) => React.ReactNode }>;
  export const SectionList: React.FC<{ sections: any[]; renderItem: (info: { item: any }) => React.ReactNode }>;
  export const RefreshControl: React.FC<{ refreshing: boolean; onRefresh: () => void }>;
  export const KeyboardAvoidingView: React.FC<React.ComponentProps<'div'>>;
  export const Linking: { openURL: (url: string) => Promise<void> };
  export const Alert: { alert: (title: string, message?: string) => void };
  export const Animated: {
    View: React.FC<React.ComponentProps<'div'>>;
    Text: React.FC<React.ComponentProps<'span'>>;
    createAnimatedComponent: <T extends React.ComponentType<any>>(component: T) => T;
  };
  export const Easing: { linear: (t: number) => number; ease: (t: number) => number };
  export const LinearGradient: React.FC<React.ComponentProps<'div'>>;
  export const BorderRadius: { value: number };
  export const processColor: (color: string) => number;
  export const NativeModules: Record<string, never>;
  export const NativeEventEmitter: new <T>(module: T) => { addListener: () => { remove: () => void } };
  export const AppRegistry: { registerComponent: (name: string, component: React.FC) => void };
  export const AppState: { currentState: string; addEventListener: (type: string, handler: () => void) => { remove: () => void } };
  export const DeviceEventEmitter: { addListener: (type: string, handler: (...args: any[]) => void) => { remove: () => void } };
}

declare module 'react-native-svg' {
  import * as React from 'react';
  export const Svg: React.FC<React.ComponentProps<'svg'>>;
  export const Path: React.FC<React.ComponentProps<'path'>>;
  export const Circle: React.FC<React.ComponentProps<'circle'>>;
  export const Rect: React.FC<React.ComponentProps<'rect'>>;
  export const G: React.FC<React.ComponentProps<'g'>>;
  export const Text: React.FC<React.ComponentProps<'text'>>;
  export const Tspan: React.FC<React.ComponentProps<'tspan'>>;
  export const Defs: React.FC<React.ComponentProps<'defs'>>;
  export const LinearGradient: React.FC<{ id?: string; x1?: string; y1?: string; x2?: string; y2?: string }>;
  export const Stop: React.FC<{ stopColor?: string; stopOpacity?: number; offset?: string }>;
  export const ClipPath: React.FC<{ id?: string }>;
  export const Mask: React.FC<{ id?: string }>;
}
