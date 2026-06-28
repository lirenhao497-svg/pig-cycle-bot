import React from "react";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className = "" }: SkeletonProps) {
  return (
    <div
      className={`bg-slate-700/50 animate-pulse rounded-lg ${className}`}
    />
  );
}
