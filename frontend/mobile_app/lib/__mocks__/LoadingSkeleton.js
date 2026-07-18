/**
 * Jest mock for LoadingSkeleton / LoadingSkeletonItem components.
 * Returns null (invisible placeholder) to avoid native Animated code in tests.
 */
const React = require("react");

module.exports = {
  Skeleton: () => null,
  SkeletonRow: () => null,
  LoadingSkeletonItem: () => null,
};
