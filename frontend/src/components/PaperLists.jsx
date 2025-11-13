import { useEffect, useState } from "react";

export default function PapersList() {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchPapers() {
      try {
        const res = await fetch("http://localhost:8000/papers");
        if (!res.ok) throw new Error("Erreur API");
        const data = await res.json();
        setPapers(data);
      } catch (err) {
        console.error("❌ Erreur de chargement :", err);
      } finally {
        setLoading(false);
      }
    }
    fetchPapers();
  }, []);

  if (loading)
    return <p className="text-center text-gray-500 mt-10">Chargement...</p>;

  return (
    <div className="max-w-4xl mx-auto mt-10">
      <h1 className="text-2xl font-bold mb-6 text-center">
        📚 Liste des papiers
      </h1>
      <div className="grid gap-4">
        {papers.map((paper) => (
          <div
            key={paper.id}
            className="p-4 border rounded-lg shadow-sm bg-white"
          >
            <h2 className="text-lg font-semibold text-gray-800">
              {paper.title}
            </h2>
            <p className="text-sm text-gray-600">{paper.authors}</p>
            <p className="text-xs text-gray-400">{paper.year}</p>
            <button
              onClick={() => alert(`RAG sur ${paper.title}`)}
              className="mt-3 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Interroger avec RAG
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
