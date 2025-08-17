import React from "react";
import BriefCard from "./BriefCard";
import SkeletonCard from "./SkeletonCard";

export default function BriefList({ briefs, loading, onSelectBrief, onRefresh }) {
  return (
    <section className="w-full max-w-2xl mx-auto mt-8 mb-20 relative">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-lg font-semibold text-[#2E4052]">Your Briefs</h2>
        <button
          onClick={onRefresh}
          className="rounded-full p-2 hover:bg-gray-100 transition"
          title="Refresh"
        >
          <span className="text-xl" role="img" aria-label="refresh">↻</span>
        </button>
      </div>
      {loading ? (
        <>
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </>
      ) : briefs.length === 0 ? (
        <div className="flex flex-col items-center text-gray-400 mt-10">
          <svg width="48" height="48" fill="none" viewBox="0 0 24 24">
            <rect x="4" y="4" width="16" height="16" rx="3" fill="#F3F4F6"/>
            <path d="M8 8h8M8 12h5" stroke="#A0AEC0" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          <div className="mt-2 text-base">No briefs yet</div>
          <div className="text-xs mt-1">Paste some text above to create your first brief.</div>
        </div>
      ) : (
        briefs.map((brief) => (
          <BriefCard key={brief.id} brief={brief} onClick={onSelectBrief} />
        ))
      )}
    </section>
  );
}