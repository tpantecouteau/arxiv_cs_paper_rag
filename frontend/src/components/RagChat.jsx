import { useState } from "react";

export default function RagChat() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleAsk(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setAnswer(null);

    try {
      const res = await fetch(
        `http://localhost:8000/rag/query?query=${encodeURIComponent(query)}`,
      );
      if (!res.ok) throw new Error("Erreur serveur");
      const data = await res.json();
      console.log(data);
      setAnswer(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto mt-10 p-6 bg-white rounded-xl shadow">
      <h2 className="text-xl font-semibold mb-4">🔍 Pose une question</h2>

      <form onSubmit={handleAsk} className="flex gap-2 mb-4">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ex: What is attention blink?"
          className="flex-1 border border-gray-300 rounded-md px-3 py-2"
        />
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          disabled={loading}
        >
          {loading ? "⏳" : "Ask"}
        </button>
      </form>

      {error && <p className="text-red-600">{error}</p>}

      {answer && (
        <div className="mt-4">
          <h3 className="font-medium mb-2">💡 Réponse :</h3>
          <p className="text-gray-800 whitespace-pre-wrap">{answer.answer}</p>

          <h4 className="font-medium mt-4">📚 Sources :</h4>
          <ul className="list-disc ml-6 text-sm text-gray-600">
            {answer.sources?.map((src, i) => (
              <li key={i}>
                <strong>{src.metadata?.title || "No title"}</strong>
                {src.metadata?.arxiv_id && (
                  <span className="text-gray-500">
                    {" "}
                    — {src.metadata.arxiv_id}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
