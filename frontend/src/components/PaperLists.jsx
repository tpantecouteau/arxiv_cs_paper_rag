import { useEffect, useState } from "react";

export default function PapersList() {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    async function fetchPapers() {
      try {
        const res = await fetch("http://localhost:8000/papers");
        if (!res.ok) throw new Error("Failed to load papers");
        const data = await res.json();
        setPapers(data);
      } catch (err) {
        console.error("❌ Error:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchPapers();
  }, []);

  const filteredPapers = papers.filter((paper) =>
    paper.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    paper.authors?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="h-full flex flex-col">
        <div className="p-6 border-b border-white/10">
          <div className="h-8 w-48 skeleton rounded" />
        </div>
        <div className="p-6 space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 skeleton rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-white/10 space-y-4">
        <div>
          <h2 className="text-2xl font-bold gradient-text">
            📚 Research Papers
          </h2>
          <p className="text-sm text-gray-400 mt-1">
            {papers.length} papers in database
          </p>
        </div>

        {/* Search */}
        <input
          type="text"
          placeholder="Search papers by title or author..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:bg-white/10 focus:border-purple-500 transition-all"
        />
      </div>

      {/* Papers Grid */}
      <div className="flex-1 overflow-y-auto p-6">
        {filteredPapers.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-12">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-xl font-semibold text-gray-300 mb-2">
              No papers found
            </h3>
            <p className="text-gray-500">
              Try a different search term
            </p>
          </div>
        ) : (
          <div className="grid gap-4">
            {filteredPapers.map((paper, index) => (
              <div
                key={paper.id}
                className="glass rounded-xl p-5 hover:bg-white/10 transition-all group cursor-pointer animate-fadeIn"
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                {/* Title */}
                <h3 className="text-lg font-semibold text-white group-hover:text-purple-400 transition-colors line-clamp-2">
                  {paper.title}
                </h3>

                {/* Authors */}
                <p className="text-sm text-gray-400 mt-2 line-clamp-1">
                  {paper.authors}
                </p>

                {/* Metadata Row */}
                <div className="flex items-center gap-3 mt-3 text-xs text-gray-500">
                  {paper.year && (
                    <span className="flex items-center gap-1">
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      {paper.year}
                    </span>
                  )}
                  {paper.categories && (
                    <span className="flex items-center gap-1">
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                      </svg>
                      {paper.categories.split(',')[0].trim()}
                    </span>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-2 mt-4">
                  {paper.pdf_url && (
                    <a
                      href={paper.pdf_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 px-3 py-1.5 bg-purple-500/20 text-purple-300 rounded-lg hover:bg-purple-500/30 transition-all text-sm font-medium"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      View PDF
                    </a>
                  )}
                  <button
                    onClick={() => {
                      // Scroll to RAG chat and focus
                      document.querySelector('textarea')?.focus();
                    }}
                    className="flex items-center gap-2 px-3 py-1.5 bg-white/5 border border-white/10 text-gray-300 rounded-lg hover:bg-white/10 hover:border-purple-500 transition-all text-sm font-medium"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                    Ask about this
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
