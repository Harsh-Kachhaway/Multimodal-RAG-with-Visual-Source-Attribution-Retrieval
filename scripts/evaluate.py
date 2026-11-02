import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unittest.mock import MagicMock
sys.modules['langchain_community.chat_models.vertexai'] = MagicMock()

import requests
import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import Faithfulness, AnswerRelevancy, ContextPrecision
from langchain_ollama import ChatOllama, OllamaEmbeddings
from app.core.config import settings
from app.core.logging import logger


def run_ragas_evaluation():
    logger.info("Initializing local evaluator models")
    evaluator_language_model = ChatOllama(
        model=settings.llm_model,
        base_url=settings.ollama_base_url
    )
    evaluator_embedding_model = OllamaEmbeddings(
        model=settings.embedding_model,
        base_url=settings.ollama_base_url
    )

    test_questions = [
        "What is the ethnic composition of Belgium?",
        "Why is power sharing desirable according to the textbook?"
    ]

    reference_ground_truths = [
        "59% lives in Flemish region speaking Dutch, 40% in Wallonia speaking French, 1% speak German.",
        "It helps reduce conflict between social groups and ensures the stability of political order."
    ]

    generated_answers = []
    retrieved_contexts_list = []

    api_endpoint = f"{settings.api_base_url}/query"
    logger.info(f"Querying backend API at {api_endpoint}")

    for single_question in test_questions:
        api_response = requests.post(
            api_endpoint,
            json={"question": single_question},
            timeout=300.0
        )
        api_response.raise_for_status()
        payload = api_response.json()

        generated_answers.append(payload["answer"])
        text_snippets = [source["text"] for source in payload.get("sources", [])]
        retrieved_contexts_list.append(text_snippets)

    dataset_dictionary = {
        "user_input": test_questions,
        "response": generated_answers,
        "retrieved_contexts": retrieved_contexts_list,
        "reference": reference_ground_truths
    }

    ragas_dataset = Dataset.from_dict(dataset_dictionary)

    logger.info("Running evaluation with Ragas metrics")
    evaluation_result = evaluate(
        dataset=ragas_dataset,
        metrics=[Faithfulness(), AnswerRelevancy(), ContextPrecision()],
        llm=evaluator_language_model,
        embeddings=evaluator_embedding_model
    )

    results_table = evaluation_result.to_pandas()
    logger.info("Evaluation complete")
    
    selected_columns = [col for col in ["user_input", "faithfulness", "answer_relevancy", "context_precision"] if col in results_table.columns]
    print(results_table[selected_columns])
    return results_table


if __name__ == "__main__":
    run_ragas_evaluation()

