import { useState, useCallback } from "react";
import { getBriefs, createBrief, getBrief, deleteBrief } from "../utils/api";

export default function useBriefs(sessionId) {
  const [briefs, setBriefs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Fetch all briefs for the session
  const fetchBriefs = useCallback(async () => {
    if (!sessionId) return; // Don't fetch if no sessionId

    setLoading(true);
    setError("");
    try {
      const data = await getBriefs(sessionId);
      setBriefs(Array.isArray(data) ? data : []); // Ensure it's always an array
    } catch (e) {
      setError("Failed to fetch briefs.");
      setBriefs([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  // Create a new brief
  const submitBrief = useCallback(
    async (sourceText) => {
      if (!sessionId || !sourceText.trim()) return;

      setLoading(true);
      setError(null);
      try {
        const response = await createBrief(sourceText, sessionId);
        setBriefs((prev) => [response, ...(Array.isArray(prev) ? prev : [])]);
        return response;
      } catch (err) {
        const errorMessage = err.message || "Failed to create brief";
        setError(errorMessage);
        // Always propagate errors consistently
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [sessionId]
  );

  // Get a specific brief by ID
  const fetchBrief = useCallback(
    async (briefId) => {
      if (!sessionId || !briefId) return;

      setLoading(true);
      setError("");
      try {
        return await getBrief(briefId, sessionId);
      } catch (e) {
        setError("Failed to fetch brief details.");
        throw e;
      } finally {
        setLoading(false);
      }
    },
    [sessionId]
  );

  // Delete a brief
  const removeBrief = useCallback(
    async (briefId) => {
      if (!sessionId || !briefId) return;

      setLoading(true);
      setError("");
      try {
        await deleteBrief(briefId, sessionId);
        setBriefs((prev) =>
          Array.isArray(prev) ? prev.filter((b) => b.id !== briefId) : []
        );
      } catch (e) {
        setError("Failed to delete brief.");
        throw e;
      } finally {
        setLoading(false);
      }
    },
    [sessionId]
  );

  return {
    briefs,
    loading,
    error,
    fetchBriefs,
    submitBrief,
    fetchBrief,
    removeBrief,
    setError,
  };
}