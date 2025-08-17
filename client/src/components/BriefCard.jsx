import React from "react";

export default function BriefCard({ brief, onClick }) {
  return (
    <div
      className="bg-white rounded-lg shadow hover:shadow-md transition cursor-pointer p-4 mb-4 border border-gray-100"
      onClick={() => onClick(brief)}
    >
      <div className="font-medium text-[#2E4052] text-base mb-1 line-clamp-2">
        {brief.summary}
      </div>
      <div className="flex items-center text-xs text-gray-400 space-x-3">
        <span>{brief.created_at ? new Date(brief.created_at).toLocaleString() : ""}</span>
        <span className="flex items-center space-x-1">
          <span className="bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
            {brief.decisions_count} Decisions
          </span>
          <span className="bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
            {brief.actions_count} Actions
          </span>
          <span className="bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
            {brief.questions_count} Questions
          </span>
        </span>
      </div>
    </div>
  );
}