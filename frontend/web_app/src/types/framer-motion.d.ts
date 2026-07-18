// Workaround for framer-motion typings that may not include standard React HTML attributes like `className`.
// This file makes core framer-motion exports (motion, AnimatePresence, etc.) permissively typed.

declare module "framer-motion" {
  export const motion: any;
  export const AnimatePresence: any;
  export const AnimateSharedLayout: any;
  export const AnimateSharedLayoutContext: any;
  export const useAnimation: any;
  export const useInView: any;
  export const m: any; // alias used by some codebases
}
