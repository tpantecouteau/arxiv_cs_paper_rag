import pandas as pd
from llama_index.core import PromptTemplate, StorageContext, VectorStoreIndex
from llama_index.core.evaluation import FaithfulnessEvaluator, RelevancyEvaluator
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.opensearch import (
    OpensearchVectorClient,
    OpensearchVectorStore,
)

# -------------------------
#  QUESTIONS / GROUND TRUTH
# -------------------------
qa_pairs = [
    {
        "query": "What is the main idea behind end-to-end speaker diarization in the paper 'End-to-End Speaker Diarization as Post-Processing'?",
        "ground_truth": "The paper proposes an end-to-end speaker diarization system that performs post-processing on speaker embeddings to refine diarization results.",
    },
    {
        "query": "What problem does the Regularized Attentive Capsule Network aim to solve?",
        "ground_truth": "It improves overlapped relation extraction by introducing an attentive capsule network with regularization to better detect multiple overlapping relations.",
    },
    {
        "query": "What is the goal of the paper 'Should I visit this place?'",
        "ground_truth": "The paper extracts inclusion and exclusion phrases from reviews to help users decide whether a place matches their preferences.",
    },
    {
        "query": "How is speech synthesis used in the paper about low-resource ASR?",
        "ground_truth": "The paper uses speech synthesis as data augmentation to improve ASR models in low-resource languages.",
    },
    {
        "query": "What does the QUACKIE dataset provide?",
        "ground_truth": "QUACKIE is a classification task that includes ground-truth explanations for each instance.",
    },
    {
        "query": "What contradiction problem does 'I like fish, especially dolphins' address?",
        "ground_truth": "It studies contradictions in dialogue modeling and how models handle inconsistent or conflicting statements.",
    },
    {
        "query": "What does the Panarchy paper investigate?",
        "ground_truth": "It investigates panarchy dynamics, focusing on how ecological and social systems influence each other through cross-scale interactions.",
    },
    {
        "query": "What is the main contribution of 'My Teacher Thinks the World is Flat'?",
        "ground_truth": "It interprets automatic essay scoring mechanisms and analyzes how models form judgments, highlighting biases and reasoning failures.",
    },
    {
        "query": "What method is used to measure university impact in the Wikipedia approach?",
        "ground_truth": "The paper measures impact based on how universities appear, are linked, and referenced in Wikipedia articles.",
    },
    {
        "query": "What does 'Neural document expansion' aim to improve?",
        "ground_truth": "It improves ad-hoc information retrieval by expanding documents using neural models to make them more matchable to diverse queries.",
    },
    {
        "query": "How does the adversarial domain adaptation help spoken question answering?",
        "ground_truth": "It mitigates ASR errors by training the model to be robust to mismatches between clean text and ASR transcripts.",
    },
    {
        "query": "What does the paper on cross-language question re-ranking study?",
        "ground_truth": "It explores query expansion techniques for re-ranking questions in cross-language QA settings.",
    },
    {
        "query": "What does posterior-regularized REINFORCE help with in distant supervision?",
        "ground_truth": "It improves instance selection by constraining policy learning using posterior regularization to filter noisy training samples.",
    },
    {
        "query": "How does the speech translation paper use knowledge distillation?",
        "ground_truth": "It transfers knowledge from a text translation model to an end-to-end speech translation model to significantly boost performance.",
    },
    {
        "query": "What is the approach behind FAQ retrieval in the BERT-based paper?",
        "ground_truth": "It combines query-question similarity with BERT-based query-answer relevance to improve FAQ retrieval accuracy.",
    },
    {
        "query": "What does the SMT-based minimalist grammar inference paper achieve?",
        "ground_truth": "It automatically infers minimalist grammars using an SMT solver to search for structures consistent with linguistic constraints.",
    },
    {
        "query": "What does ShapeGlot aim to learn?",
        "ground_truth": "ShapeGlot learns a language representation that aligns human descriptions with 3D shape differences.",
    },
    {
        "query": "What does Text2Node try to map?",
        "ground_truth": "It maps arbitrary phrases to nodes in a taxonomy across different domains.",
    },
    {
        "query": "What challenge does the 'Who wrote this book?' paper address?",
        "ground_truth": "It identifies authors behind books in e-commerce settings using metadata and textual signals.",
    },
    {
        "query": "What does the AI-powered text generation survey discuss?",
        "ground_truth": "It reviews AI-powered text generation systems and their role in enabling harmonious human-machine interaction, along with future research directions.",
    },
]


# -------------------------
#  PROMPT TEMPLATE
# -------------------------
QA_TEMPLATE = PromptTemplate(
    "You are an expert research assistant.\n"
    "Use ONLY the provided context.\n\n"
    "Context:\n{context_str}\n\n"
    "Question: {query_str}\n\n"
    "Answer:"
)


# -------------------------
#  LOADING COMPONENTS
# -------------------------
def load_index():
    embed_model = OllamaEmbedding(
        model_name="nomic-embed-text", base_url="http://localhost:11434"
    )

    client = OpensearchVectorClient(
        endpoint=["http://localhost:9200"],
        index="paper_chunks_llama",
        dim=768,
        text_field="text",
        embedding_field="embedding",
    )

    vector_store = OpensearchVectorStore(client)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    return VectorStoreIndex.from_vector_store(
        vector_store, storage_context=storage_context, embed_model=embed_model
    )


def load_llm():
    return Ollama(
        model="mistral",
        base_url="http://localhost:11434",
        temperature=0.2,
        request_timeout=300.0,
    )


def build_query_engine(index, llm):
    return index.as_query_engine(
        llm=llm, similarity_top_k=2, text_qa_template=QA_TEMPLATE
    )


def load_evaluators(llm):
    return {
        "faithfulness": FaithfulnessEvaluator(llm=llm),
        "relevance": RelevancyEvaluator(llm=llm),
    }


# -------------------------
#  EVALUATION LOOP
# -------------------------
def evaluate_rag():
    index = load_index()
    llm = load_llm()
    q_engine = build_query_engine(index, llm)
    evaluators = load_evaluators(llm)

    results = []

    for pair in qa_pairs:
        question = pair["query"]

        print("\n" + "=" * 80)
        print(f"❓ QUESTION:\n{question}")

        # Run RAG
        response = q_engine.query(question)
        print(f"\n🧠 ANSWER:\n{response}")

        # Extract contexts
        contexts = [node.node.text for node in response.source_nodes]
        print("\n📄 CONTEXTS USED:")
        for c in contexts:
            print("-", c[:200].replace("\n", " "), "...")

        row = {
            "question": question,
            "answer": str(response),
        }

        # Evaluate
        for name, evaluator in evaluators.items():
            score = evaluator.evaluate(
                query=question, response=str(response), contexts=contexts
            )
            row[name] = score.score

        results.append(row)

    return results


def export_results(results):
    df = pd.DataFrame(results)
    df.to_csv("rag_eval_report.csv", index=False)
    print("\n📊 Report saved as rag_eval_report.csv")


# -------------------------
#  RUN
# -------------------------
if __name__ == "__main__":
    results = evaluate_rag()
    export_results(results)
