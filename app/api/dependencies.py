from app.services.rag_service import rag_system, KnowledgeQueryEngine
from app.services.qdrant_service import database_manager, VectorDatabaseManager


def get_rag_engine() -> KnowledgeQueryEngine:
    return rag_system


def get_database_manager() -> VectorDatabaseManager:
    return database_manager

