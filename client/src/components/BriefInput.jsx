import React, { useState } from "react";

export default function BriefInput({ onSubmit, loading }) {
  const [text, setText] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    onSubmit(text);
    setText("");
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-2xl mx-auto mt-28 flex flex-col items-center"
    >
      <textarea
        className="w-full min-h-[96px] max-h-60 resize-y border border-gray-300 rounded-lg px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-[#4A6FA5] bg-white shadow-sm transition"
        placeholder="Paste or type your source text..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={loading}
        required
      />
      <button
        type="submit"
        className={`mt-4 px-6 py-2 rounded bg-[#4A6FA5] text-white font-semibold shadow transition hover:bg-[#3A5A95] disabled:opacity-60 disabled:cursor-not-allowed`}
        disabled={loading || !text.trim()}
      >
        {loading ? "Summarizing..." : "Summarize →"}
      </button>
    </form>
  );
}