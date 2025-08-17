import { useState, useCallback } from "react";
import { getBriefs, createBrief, getBrief, deleteBrief } from "../utils/api";

export default function useBriefs(sessionId) {
  const [briefs, setBriefs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Fetch all briefs for the session
  const fetchBriefs = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getBriefs(sessionId);
      setBriefs(data);
    } catch (e) {
      setError("Failed to fetch briefs.");
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  // Create a new brief
  const submitBrief = useCallback(
    async (sourceText) => {
      setLoading(true);
      setError("");
      try {
        const newBrief = await createBrief(sourceText, sessionId);
        setBriefs((prev) => [newBrief, ...prev]);
        return newBrief;
      } catch (e) {
        setError("Failed to create brief.");
        throw e;
      } finally {
        setLoading(false);
      }
    },
    [sessionId]
  );

  // Get a specific brief by ID
  const fetchBrief = useCallback(
    async (briefId) => {
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
      setLoading(true);
      setError("");
      try {
        await deleteBrief(briefId, sessionId);
        setBriefs((prev) => prev.filter((b) => b.id !== briefId));
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