"use client";

import { createElement, forwardRef } from "react";

const MOTION_PROPS = new Set([
  "animate",
  "exit",
  "initial",
  "layout",
  "layoutId",
  "onAnimationComplete",
  "onDragEnd",
  "onDragStart",
  "onHoverEnd",
  "onHoverStart",
  "onPan",
  "onPanEnd",
  "onPanStart",
  "onTap",
  "onTapCancel",
  "onTapStart",
  "onUpdate",
  "transition",
  "variants",
  "viewport",
  "whileDrag",
  "whileFocus",
  "whileHover",
  "whileInView",
  "whileTap",
]);

function stripMotionProps(props: Record<string, unknown>) {
  const nextProps: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(props)) {
    if (!MOTION_PROPS.has(key)) {
      nextProps[key] = value;
    }
  }
  return nextProps;
}

function createMotionComponent(tagName: string) {
  return forwardRef<unknown, Record<string, unknown>>(function MotionShim(props, ref) {
    return createElement(tagName, { ...stripMotionProps(props), ref });
  });
}

export const motion = {
  div: createMotionComponent("div"),
  ellipse: createMotionComponent("ellipse"),
  g: createMotionComponent("g"),
  path: createMotionComponent("path"),
  span: createMotionComponent("span"),
  svg: createMotionComponent("svg"),
};