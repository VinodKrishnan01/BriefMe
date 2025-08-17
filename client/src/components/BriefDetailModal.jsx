import React from "react";

export default function BriefDetailModal({ brief, isOpen, onClose, onDelete, onCopy }) {
  if (!isOpen || !brief) return null;

  const decisions = brief?.decisions || [];
  const actions = brief?.actions || [];
  const questions = brief?.questions || [];

  return (
    <div className="fixed inset-0 z-40 flex items-end sm:items-center justify-center bg-black bg-opacity-40 transition">
      <div className="bg-white w-full sm:w-[420px] max-h-[90vh] rounded-t-2xl sm:rounded-2xl shadow-lg p-6 overflow-y-auto animate-slideup">
        <button
          className="absolute top-4 right-6 text-gray-400 hover:text-gray-600 text-2xl"
          onClick={onClose}
          aria-label="Close"
        >
          ×
        </button>
        <div className="mb-3">
          <div className="font-bold text-lg text-[#2E4052] mb-1">{brief.summary}</div>
          <div className="text-xs text-gray-400">{new Date(brief.created_at).toLocaleString()}</div>
        </div>
        <div className="mb-4">
          <CollapsibleSection title={`Decisions (${decisions.length})`}>
            <ul className="list-disc pl-5">
              {decisions.map((d, i) => (
                <li key={i} className="mb-1">{d}</li>
              ))}
            </ul>
          </CollapsibleSection>
          <CollapsibleSection title={`Actions (${actions.length})`}>
            <ul className="list-disc pl-5">
              {actions.map((a, i) => (
                <li key={i} className="mb-1">
                  {a.task}
                  {a.assignee && <span className="ml-2 text-xs text-gray-500">({a.assignee})</span>}
                  {a.dueDate && <span className="ml-2 text-xs text-gray-400">Due: {a.dueDate}</span>}
                </li>
              ))}
            </ul>
          </CollapsibleSection>
          <CollapsibleSection title={`Questions (${questions.length})`}>
            <ul className="list-disc pl-5">
              {questions.map((q, i) => (
                <li key={i} className="mb-1 text-gray-600 bg-gray-100 rounded px-2 py-1">{q}</li>
              ))}
            </ul>
          </CollapsibleSection>
        </div>
        <div className="flex justify-end space-x-2 mt-4">
          <button
            className="px-3 py-1 rounded bg-[#C1666B] text-white hover:bg-red-700 transition"
            onClick={() => onDelete(brief.id)}
            title="Delete"
          >
            🗑 Delete
          </button>
          <button
            className="px-3 py-1 rounded bg-[#4A6FA5] text-white hover:bg-blue-700 transition"
            onClick={() => onCopy(brief)}
            title="Copy"
          >
            📋 Copy
          </button>
        </div>
      </div>
    </div>
  );
}

// Simple collapsible section for modal
function CollapsibleSection({ title, children }) {
  const [open, setOpen] = React.useState(true);
  return (
    <div className="mb-2">
      <button
        className="w-full flex justify-between items-center text-sm font-semibold text-[#4A6FA5] py-1"
        onClick={() => setOpen((v) => !v)}
      >
        {title}
        <span>{open ? "▲" : "▼"}</span>
      </button>
      {open && <div className="pl-1">{children}</div>}
    </div>
  );
}