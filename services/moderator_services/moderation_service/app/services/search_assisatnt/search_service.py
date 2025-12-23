"""
Search Service - FastAPI endpoints for AI-powered search
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import time

from .category_matcher import get_matcher, CategoryMatcher


# Create router with search tag
router = APIRouter(prefix="/search", tags=["search"])


# Request/Response models
class SearchRequest(BaseModel):
    """AI-powered category search request."""
    query: str = Field(..., description="Search query (e.g., 'hungry', 'car', 'rent')", min_length=1, max_length=500)
    top_k: int = Field(5, description="Maximum number of results", ge=1, le=20)
    threshold: float = Field(0.25, description="Minimum similarity score (0.0-1.0)", ge=0.0, le=1.0)
    categories: Optional[List[Dict]] = Field(None, description="Custom categories to search against")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "I want to buy a car",
                "top_k": 3,
                "threshold": 0.3
            }
        }


class SearchResult(BaseModel):
    """Individual search result with category match."""
    slug: str = Field(..., description="Category slug identifier")
    name: str = Field(..., description="Category display name")
    score: float = Field(..., description="Similarity score (0.0-1.0)")
    match_type: str = Field(..., description="Match type: semantic, keyword, or partial")


class SearchResponse(BaseModel):
    """AI search response with matched categories."""
    success: bool = Field(..., description="Whether search succeeded")
    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field(..., description="Matched categories")
    count: int = Field(..., description="Number of results")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    model_type: str = Field(..., description="Model used: semantic or keyword")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "query": "I want to buy a car",
                "results": [
                    {"slug": "vehicles", "name": "Vehicles", "score": 0.92, "match_type": "semantic"},
                    {"slug": "automotive", "name": "Automotive", "score": 0.78, "match_type": "semantic"}
                ],
                "count": 2,
                "processing_time_ms": 45.2,
                "model_type": "semantic"
            }
        }


class CategoryListResponse(BaseModel):
    """List of all available categories."""
    success: bool
    categories: List[Dict] = Field(..., description="List of category objects")
    count: int = Field(..., description="Total category count")


class HealthResponse(BaseModel):
    """Search service health status."""
    status: str = Field(..., description="Service status: healthy or unhealthy")
    model_loaded: bool = Field(..., description="Whether ML model is loaded")
    categories_count: int = Field(..., description="Number of available categories")


# Endpoints
@router.post("/match", response_model=SearchResponse, summary="AI Category Matching",
             description="Match search queries to categories using semantic AI similarity.")
async def match_categories(request: SearchRequest):
    """
    ## AI-Powered Category Matching

    Uses multilingual sentence transformers to match user queries to categories.

    ### Supported Languages
    50+ languages including English, Spanish, French, German, Swahili, Arabic, Chinese.

    ### Example Queries
    - "hungry" → food
    - "TV" → electronics
    - "rent apartment" → housing
    - "chakula" (Swahili) → food

    ### Match Types
    - `semantic`: AI embedding similarity
    - `keyword`: Exact/partial keyword match
    - `partial`: Partial word match
    """
    start_time = time.time()

    try:
        matcher = get_matcher()

        # Set custom categories if provided
        if request.categories:
            custom_cats = {
                cat.get("slug", cat.get("name", "").lower().replace(" ", "_")): {
                    "name": cat.get("name", ""),
                    "description": cat.get("description", ""),
                    "keywords": cat.get("keywords", [])
                }
                for cat in request.categories
            }
            matcher.set_categories(custom_cats)

        # Perform matching
        results = matcher.match(
            query=request.query,
            top_k=request.top_k,
            threshold=request.threshold
        )

        processing_time = (time.time() - start_time) * 1000

        return SearchResponse(
            success=True,
            query=request.query,
            results=[SearchResult(**r) for r in results],
            count=len(results),
            processing_time_ms=round(processing_time, 2),
            model_type="semantic" if matcher.model else "keyword"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/quick/{query}", response_model=SearchResponse, summary="Quick Search",
             description="Fast semantic search for simple queries.")
async def quick_match(query: str, top_k: int = Query(3, description="Max results", ge=1, le=10)):
    """
    Quick search endpoint for simple queries.

    - **query**: The search term
    - **top_k**: Maximum results (default: 3)
    """
    start_time = time.time()

    try:
        matcher = get_matcher()
        results = matcher.match(query=query, top_k=top_k)

        processing_time = (time.time() - start_time) * 1000

        return SearchResponse(
            success=True,
            query=query,
            results=[SearchResult(**r) for r in results],
            count=len(results),
            processing_time_ms=round(processing_time, 2),
            model_type="semantic" if matcher.model else "keyword"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/categories", response_model=CategoryListResponse, summary="List Categories",
             description="Get all available categories for searching.")
async def list_categories():
    """
    ## List All Categories

    Returns all available categories that can be matched against.
    Each category includes name, description, and keywords.
    """
    try:
        matcher = get_matcher()
        categories = matcher.get_all_categories()

        return CategoryListResponse(
            success=True,
            categories=categories,
            count=len(categories)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list categories: {str(e)}")


@router.get("/health", response_model=HealthResponse, summary="Search Health",
            description="Check search service health and model status.")
async def search_health():
    try:
        matcher = get_matcher()
        categories = matcher.get_all_categories()
        return HealthResponse(
            status="healthy",
            model_loaded=bool(matcher.model),
            categories_count=len(categories)
        )
    except Exception:
        return HealthResponse(
            status="unhealthy",
            model_loaded=False,
            categories_count=0
        )


# Service class for direct Python usage
class SearchService:
    """Service class for direct integration."""

    def __init__(self):
        self.matcher = get_matcher()

    def search(self, query: str, top_k: int = 5, threshold: float = 0.25) -> Dict:
        """
        Search for matching categories.

        Args:
            query: Search term
            top_k: Max results
            threshold: Min similarity score

        Returns:
            Dict with results and metadata
        """
        start_time = time.time()

        results = self.matcher.match(query, top_k, threshold)

        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2)
        }

    def set_categories(self, categories: List[Dict]) -> None:
        """Set custom categories to match against."""
        custom_cats = {
            cat.get("slug", cat.get("name", "").lower().replace(" ", "_")): {
                "name": cat.get("name", ""),
                "description": cat.get("description", ""),
                "keywords": cat.get("keywords", [])
            }
            for cat in categories
        }
        self.matcher.set_categories(custom_cats)
