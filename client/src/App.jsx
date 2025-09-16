import React, { useEffect, useState, useCallback } from "react";
import Header from "./components/Header";
import BriefInput from "./components/BriefInput";
import BriefList from "./components/BriefList";
import BriefDetailModal from "./components/BriefDetailModal";
import Toast from "./components/Toast";
import useBriefs from "./hooks/useBriefs";
import useToast from "./hooks/useToast";

// Generate session ID outside of component to avoid re-generation on re-renders
let cachedSessionId = null;

function getOrCreateSessionId() {
  // If we already have a cached session ID, return it
  if (cachedSessionId) {
    console.log("Using cached session ID:", cachedSessionId);
    return cachedSessionId;
  }

  let id = localStorage.getItem("briefme_session_id");
  if (!id) {
    // Add fallback for older browsers
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      id = crypto.randomUUID();
    } else {
      // Fallback UUID generation
      id = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
      });
    }
    localStorage.setItem("briefme_session_id", id);
    console.log("Generated new session ID:", id);
  } else {
    console.log("Loaded session ID from localStorage:", id);
  }
  
  // Validate the UUID format
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (!uuidRegex.test(id)) {
    console.warn("Invalid UUID format, generating new one. Old ID:", id);
    id = typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : 
        'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
          const r = Math.random() * 16 | 0;
          const v = c == 'x' ? r : (r & 0x3 | 0x8);
          return v.toString(16);
        });
    localStorage.setItem("briefme_session_id", id);
    console.log("Generated replacement session ID:", id);
  }
  
  // Cache the session ID
  cachedSessionId = id;
  console.log("Session ID cached:", cachedSessionId);
  return id;
}

export default function App() {
  // Use function in useState to ensure getOrCreateSessionId is called only once
  const [sessionId] = useState(() => getOrCreateSessionId());
  const [selectedBrief, setSelectedBrief] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);

  console.log("App component rendered with session ID:", sessionId);

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

  // Add initial brief loading
  // useEffect(() => {
  //   if (sessionId) {
  //     fetchBriefs();
  //   }
  // }, [sessionId, fetchBriefs]);

  useEffect(() => {
    if (error) showToast(error, "error");
  }, [error, showToast]);

  const handleCreateBrief = async (text) => {
    try {
      const newBrief = await submitBrief(text);
      showToast("Brief created!", "success");
      return newBrief;
    } catch (err) {
      console.error("Create brief error:", err);
      showToast(err.message || "Failed to create brief", "error");
    }
  };

  const handleSelectBrief = async (brief) => {
    try {
      const fullBrief = await fetchBrief(brief.id);
      setSelectedBrief(fullBrief);
      setModalOpen(true);
    } catch (err) {
      console.error("Fetch brief error:", err);
      showToast("Failed to load brief details.", "error");
    }
  };

  const handleDeleteBrief = async (briefId) => {
    try {
      await removeBrief(briefId);
      setModalOpen(false);
      showToast("Brief deleted.", "success");
    } catch (err) {
      console.error("Delete brief error:", err);
      showToast("Failed to delete brief.", "error");
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
      
      if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
          showToast("Copied to clipboard!", "success");
        }).catch(() => {
          showToast("Copy failed", "error");
        });
      } else {
        // Fallback for older browsers
        const textArea = document.createElement("textarea");
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
          document.execCommand('copy');
          showToast("Copied to clipboard!", "success");
        } catch (err) {
          showToast("Copy failed", "error");
        }
        document.body.removeChild(textArea);
      }
    },
    [showToast]
  );

  const handleLoadBriefs = useCallback(() => {
    if (sessionId) {
      fetchBriefs();
    }
  }, [sessionId, fetchBriefs]);

  return (
    <div className="min-h-screen bg-[#F8F9FA] pb-10">
      <Header sessionId={sessionId} />
      <main className="pt-20 px-2">
        <BriefInput onSubmit={handleCreateBrief} loading={loading} />
        <BriefList
          briefs={briefs}
          loading={loading}
          onSelectBrief={handleSelectBrief}
          onRefresh={handleLoadBriefs}
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