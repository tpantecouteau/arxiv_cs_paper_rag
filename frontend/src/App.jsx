import PapersList from "./components/PaperLists";
import RagChat from "./components/RagChat";

function App() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="glass border-b border-white/10 sticky top-0 z-10">
        <div className="max-w-screen-2xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-pink-600 rounded-xl flex items-center justify-center text-2xl">
              🧠
            </div>
            <div>
              <h1 className="text-xl font-bold gradient-text">
                arXiv RAG Assistant
              </h1>
              <p className="text-xs text-gray-500">
                AI-powered research paper search
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-lg text-xs font-medium">
              ● Online
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden">
        {/* Desktop: Side-by-side layout */}
        <div className="hidden lg:flex flex-1 gap-6 p-6 max-w-screen-2xl mx-auto w-full">
          {/* Papers List - Left Side */}
          <div className="w-1/2 glass rounded-2xl overflow-hidden">
            <PapersList />
          </div>

          {/* RAG Chat - Right Side */}
          <div className="w-1/2 glass rounded-2xl overflow-hidden">
            <RagChat />
          </div>
        </div>

        {/* Mobile/Tablet: Stacked layout */}
        <div className="lg:hidden flex flex-col flex-1 gap-6 p-4">
          <div className="glass rounded-2xl overflow-hidden h-[400px]">
            <PapersList />
          </div>
          <div className="glass rounded-2xl overflow-hidden flex-1">
            <RagChat />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 py-4 px-6 text-center text-xs text-gray-500">
        <p>
          Powered by{" "}
          <span className="text-purple-400 font-medium">Ollama</span>,{" "}
          <span className="text-purple-400 font-medium">OpenSearch</span>, and{" "}
          <span className="text-purple-400 font-medium">LlamaIndex</span>
        </p>
      </footer>
    </div>
  );
}

export default App;
