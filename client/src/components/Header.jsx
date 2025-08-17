import React from "react";

export default function Header({ sessionId }) {
  return (
    <header className="fixed top-0 left-0 w-full bg-white border-b border-gray-200 z-10 flex items-center justify-between px-6 py-3 shadow-sm">
      <div className="flex items-center space-x-2">
        <span className="font-bold text-2xl text-[#2E4052] tracking-tight select-none">
          BriefMe
        </span>
        <span className="ml-4 text-xs font-mono text-gray-400 bg-gray-100 px-2 py-1 rounded">
          Session: {sessionId}
        </span>
      </div>
    </header>
  );
}