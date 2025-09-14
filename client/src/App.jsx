import React, { useEffect, useState, useCallback } from "react";
import Header from "./components/Header";
import BriefInput from "./components/BriefInput";
import BriefList from "./components/BriefList";
import BriefDetailModal from "./components/BriefDetailModal";
import Toast from "./components/Toast";
import useBriefs from "./hooks/useBriefs";
import useToast from "./hooks/useToast";

function getOrCreateSessionId() {
  let id = localStorage.getItem("briefme_session_id");
  if (!id) {
    id = crypto.randomUUID(); // generates a valid UUID
    localStorage.setItem("briefme_session_id", id);
    console.log("Generated new session ID:", id);
  } else {
    console.log("Using existing session ID:", id);
  }
  
  // Validate the UUID format
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (!uuidRegex.test(id)) {
    console.warn("Invalid UUID format, generating new one. Old ID:", id);
    id = crypto.randomUUID();
    localStorage.setItem("briefme_session_id", id);
    console.log("Generated replacement session ID:", id);
  }
  
  return id;
}

export default function App() {
  const [sessionId] = useState(getOrCreateSessionId());
  const [selectedBrief, setSelectedBrief] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const apiUrl = process.env.REACT_APP_API_URL || "https://briefme.onrender.com";

  const {
    briefs,
    loading,
    error,
    fetchBriefs,
    submitBrief,
    removeBrief,
    fetchBrief,
    setError,
  } = useBriefs(sessionId);

  const { toast, showToast, clearToast } = useToast();

  useEffect(() => {
    fetchBriefs();
    // eslint-disable-next-line
  }, [sessionId]);

  useEffect(() => {
    if (error) showToast(error, "error");
    // eslint-disable-next-line
  }, [error, showToast]);


const handleCreateBrief = async (text) => {
  try {
    await submitBrief(text);
    await fetchBriefs(); // <-- Add this line
    showToast("Brief created!", "success");
  } catch {
    // error handled in hook
  }
};

  const handleSelectBrief = async (brief) => {
    try {
      const fullBrief = await fetchBrief(brief.id);
      setSelectedBrief(fullBrief);
      setModalOpen(true);
    } catch {
      showToast("Failed to load brief details.", "error");
    }
  };

  const handleDeleteBrief = async (briefId) => {
    try {
      await removeBrief(briefId);
      setModalOpen(false);
      showToast("Brief deleted.", "success");
    } catch {
      // error handled in hook
    }
  };

  const handleCopyBrief = useCallback(
    (brief) => {
      const text = [
        `Summary: ${brief.summary}`,
        "",
        "Decisions:",
        ...brief.decisions.map((d) => `- ${d}`),
        "",
        "Actions:",
        ...brief.actions.map(
          (a) =>
            `- ${a.task}${a.assignee ? ` (Assignee: ${a.assignee})` : ""}${
              a.dueDate ? ` (Due: ${a.dueDate})` : ""
            }`
        ),
        "",
        "Questions:",
        ...brief.questions.map((q) => `- ${q}`),
      ].join("\n");
      navigator.clipboard.writeText(text);
      showToast("Copied to clipboard!", "success");
    },
    [showToast]
  );

  return (
    <div className="min-h-screen bg-[#F8F9FA] pb-10">
      <Header sessionId={sessionId} />
      <main className="pt-20 px-2">
        <BriefInput onSubmit={handleCreateBrief} loading={loading} />
          <BriefList
            briefs={briefs}
            loading={loading}
            onSelectBrief={handleSelectBrief}
            onRefresh={fetchBriefs}
          />
        <BriefDetailModal
          brief={selectedBrief}
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          onDelete={handleDeleteBrief}
          onCopy={handleCopyBrief}
        />
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={clearToast}
        />
      </main>
    </div>
  );
}