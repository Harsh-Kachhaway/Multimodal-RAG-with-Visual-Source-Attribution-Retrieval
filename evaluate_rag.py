import sys
from unittest.mock import MagicMock
sys.modules['langchain_community.chat_models.vertexai'] = MagicMock()

import requests
import pandas as pd
from datasets import Dataset
from ragas import evaluate
# Updated Ragas imports to fix the DeprecationWarnings
from ragas.metrics import Faithfulness, AnswerRelevancy, ContextPrecision
# Updated Langchain imports to point to the new dedicated Ollama package
from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings
# 1. Setup Local Evaluator Models for Ragas
# Ragas natively uses Langchain wrappers to connect to local models
print("Initializing local evaluator models...")
evaluator_llm = ChatOllama(model="qwen2.5")
evaluator_embeddings = OllamaEmbeddings(model="nomic-embed-text")

# 2. Define the Test Set (Ground Truth)
test_questions = [
    "What is the ethnic composition of Belgium?",
    "Why is power sharing desirable according to the textbook?"
]

# The exact answers based purely on the NCERT text
ground_truths = [
    ["59% lives in Flemish region speaking Dutch, 40% in Wallonia speaking French, 1% speak German."],
    ["It helps reduce conflict between social groups and ensures the stability of political order."]
]

# 3. Fetch Answers from your running FastAPI Microservice
answers = []
contexts = []

print("Querying your local RAG API...")
for q in test_questions:
    response = requests.post("http://127.0.0.1:8000/query", json={"question": q})
    data = response.json()
    
    answers.append(data["answer"])
    # Ragas expects a list of context strings per question
    contexts.append([source["text"] for source in data["sources"]])

# 4. Format into HuggingFace Dataset
data_dict = {
    "question": test_questions,
    "answer": answers,
    "contexts": contexts,
    "ground_truth": ground_truths
}
dataset = Dataset.from_dict(data_dict)

# 5. Run the Evaluation
print("Running Ragas Evaluation (This will take a few minutes locally)...")
result = evaluate(
    dataset=dataset,
    metrics=[Faithfulness(), AnswerRelevancy(), ContextPrecision()],
    llm=evaluator_llm,
    embeddings=evaluator_embeddings
)

# 6. Output the Metrics
print("\n--- Evaluation Results ---")
df = result.to_pandas()

# Drop the bulky context columns for a clean terminal output
print(df[["question", "faithfulness", "answer_relevancy", "context_precision"]])