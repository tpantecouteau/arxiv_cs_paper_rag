import PapersList from "./components/PaperLists";
import RagChat from "./components/RagChat";

function App() {
  console.log("App component rendered");
  return (
    <div className="min-h-screen bg-gray-50">
      <PapersList />
      <RagChat />
    </div>
  );
}

export default App;
