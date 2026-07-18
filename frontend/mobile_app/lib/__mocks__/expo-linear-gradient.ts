// Mock for expo-linear-gradient in Jest tests
import React from "react";

const LinearGradient = ({
  children,
  ...props
}: {
  children?: React.ReactNode;
  colors?: string[];
  start?: { x: number; y: number };
  end?: { x: number; y: number };
  style?: object;
}): React.ReactElement =>
  React.createElement("LinearGradient", props as object, children);

export { LinearGradient };
