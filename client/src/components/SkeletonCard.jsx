import React from "react";

export default function SkeletonCard() {
  return (
    <div className="animate-pulse bg-white rounded-lg shadow p-4 mb-4 border border-gray-100">
      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
      <div className="h-3 bg-gray-100 rounded w-1/2 mb-1"></div>
      <div className="h-3 bg-gray-100 rounded w-1/3"></div>
    </div>
  );
}