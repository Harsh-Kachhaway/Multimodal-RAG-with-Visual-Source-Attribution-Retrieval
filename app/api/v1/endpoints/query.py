from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import QueryRequest, QueryResponse
from app.api.dependencies import get_rag_engine, KnowledgeQueryEngine
from app.core.logging import logger

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def ask_textbook_question(
    request_data: QueryRequest,
    rag_engine: KnowledgeQueryEngine = Depends(get_rag_engine)
):
    try:
        user_question = request_data.question.strip()
        if not user_question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty"
            )

        logger.info(f"Processing query: {user_question}")
        response = await rag_engine.search_and_synthesize(
            user_question=user_question,
            top_k=request_data.top_k
        )
        return response
    except HTTPException:
        raise
    except Exception as query_error:
        logger.error(f"Error answering question: {query_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while answering your question: {str(query_error)}"
        )

