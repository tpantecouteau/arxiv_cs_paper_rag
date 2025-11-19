import { useState } from "react";

export default function RagChat() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleAsk(e) {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setAnswer(null);

    try {
      const res = await fetch(
        `http://localhost:8000/rag/query?query=${encodeURIComponent(query)}`,
      );
      if (!res.ok) throw new Error("Server error - please try again");
      const data = await res.json();
      setAnswer(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-white/10">
        <h2 className="text-2xl font-bold gradient-text">
          🔍 Ask a Question
        </h2>
        <p className="text-sm text-gray-400 mt-1">
          Search through research papers using AI
        </p>
      </div>

      {/* Input Form */}
      <div className="p-6 border-b border-white/10">
        <form onSubmit={handleAsk} className="space-y-3">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="E.g., What contradiction problem does 'I like fish, especially dolphins' address?"
            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 resize-none focus:bg-white/10 focus:border-purple-500 transition-all"
            rows="3"
            autoFocus
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleAsk(e);
              }
            }}
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold rounded-xl hover:shadow-glow hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 transition-all"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Searching...
              </span>
            ) : (
              "Ask Question"
            )}
          </button>
          <p className="text-xs text-gray-500 text-center">
            Press Enter to submit • Shift+Enter for new line
          </p>
        </form>
      </div>

      {/* Results Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Error State */}
        {error && (
          <div className="animate-fadeIn p-4 bg-red-500/10 border border-red-500/30 rounded-xl">
            <div className="flex items-start gap-3">
              <span className="text-2xl">⚠️</span>
              <div>
                <h3 className="font-semibold text-red-400">Error</h3>
                <p className="text-sm text-red-300">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Loading Skeleton */}
        {loading && (
          <div className="space-y-4 animate-fadeIn">
            <div className="h-6 w-32 skeleton rounded" />
            <div className="space-y-2">
              <div className="h-4 skeleton rounded w-full" />
              <div className="h-4 skeleton rounded w-5/6" />
              <div className="h-4 skeleton rounded w-4/6" />
            </div>
            <div className="h-6 w-24 skeleton rounded mt-6" />
            <div className="grid gap-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-16 skeleton rounded" />
              ))}
            </div>
          </div>
        )}

        {/* Answer Display */}
        {answer && (
          <div className="space-y-6 animate-fadeIn">
            {/* Answer Section */}
            <div className="glass rounded-xl p-6 space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-2xl">💡</span>
                <h3 className="text-lg font-semibold">Answer</h3>
              </div>
              <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">
                {answer.answer}
              </p>
            </div>

            {/* Sources Section */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-2xl">📚</span>
                <h3 className="text-lg font-semibold">Sources</h3>
                <span className="text-sm text-gray-500">
                  ({answer.sources?.length || 0} found)
                </span>
              </div>

              <div className="grid gap-3">
                {answer.sources?.map((src, i) => (
                  <div
                    key={i}
                    className="glass rounded-xl p-4 hover:bg-white/10 transition-all group cursor-pointer"
                  >
                    <div className="flex justify-between items-start gap-3">
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-white group-hover:text-purple-400 transition-colors truncate">
                          {src.metadata?.title || "Untitled"}
                        </h4>
                        <p className="text-xs text-gray-500 mt-1">
                          {src.metadata?.authors || "Unknown authors"}
                        </p>
                        {src.metadata?.arxiv_id && (
                          <a
                            href={src.metadata?.pdf_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-purple-400 hover:text-purple-300 mt-1 inline-block"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {src.metadata.arxiv_id} →
                          </a>
                        )}
                      </div>
                      {src.score && (
                        <div className="flex-shrink-0">
                          <div className="px-2 py-1 bg-purple-500/20 rounded-lg">
                            <span className="text-xs font-mono text-purple-300">
                              {(src.score * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                    <p className="text-xs text-gray-400 mt-3 line-clamp-2">
                      {src.preview}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!answer && !loading && !error && (
          <div className="flex flex-col items-center justify-center h-full text-center py-12">
            <div className="text-6xl mb-4">🤔</div>
            <h3 className="text-xl font-semibold text-gray-300 mb-2">
              Ask me anything
            </h3>
            <p className="text-gray-500 max-w-md">
              Type your question above to search through the research paper database
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
