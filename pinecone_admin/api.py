from fastapi import APIRouter, HTTPException
from app.pinecone import pc, index, BotNamespace, INDEX_NAME, query_text
from typing import List, Dict, Any, Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stats")
async def get_pinecone_stats():
    """Get statistics about the Pinecone index"""
    try:
        # Get index statistics
        stats = index.describe_index_stats()
        
        # Extract namespaces and their vector counts
        namespaces = {}
        total_vector_count = 0
        dimension = 384  # Default dimension for llama-text-embed-v2
        
        # Check stats structure based on the Pinecone SDK version
        if isinstance(stats, dict):
            # For the newer SDK structure
            namespaces = stats.get("namespaces", {})
            total_vector_count = stats.get("total_vector_count", 0)
            dimension = stats.get("dimension", dimension)
        else:
            # For the object-based response in newer SDKs
            namespaces = getattr(stats, "namespaces", {})
            total_vector_count = getattr(stats, "total_vector_count", 0)
            dimension = getattr(stats, "dimension", dimension)
        
        # Format response
        response = {
            "index_name": getattr(index, "index_name", INDEX_NAME),
            "total_vectors": total_vector_count,
            "dimension": dimension,
            "namespaces": {
                ns: {"vector_count": info.get("vector_count", 0) if isinstance(info, dict) else getattr(info, "vector_count", 0)}
                for ns, info in namespaces.items()
            }
        }
        
        # Add bot display names for known namespaces
        for bot in BotNamespace:
            if bot.value in response["namespaces"]:
                response["namespaces"][bot.value]["display_name"] = BotNamespace.get_display_name(bot)
        
        return response
    except Exception as e:
        logger.exception(f"Error fetching Pinecone stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching Pinecone stats: {str(e)}")

@router.get("/namespace/{namespace}/sample")
async def get_namespace_sample(namespace: str, limit: int = 10):
    """Get sample vectors from a namespace"""
    if namespace not in BotNamespace.values():
        raise HTTPException(status_code=404, detail=f"Namespace '{namespace}' not found or not recognized")
    
    try:
        # First get stats to determine the dimension
        stats = index.describe_index_stats()
        dimension = 384  # Default for llama-text-embed-v2
        
        # Extract dimension based on response structure
        if isinstance(stats, dict):
            dimension = stats.get("dimension", dimension)
        else:
            dimension = getattr(stats, "dimension", dimension)
        
        # Log the dimension we're using
        logger.info(f"Using dimension {dimension} for namespace {namespace}")
        
        try:
            # Fetch sample vectors using a dummy query to get some vectors
            # This is a workaround as Pinecone doesn't have a "list vectors" endpoint
            result = index.query(
                vector=[0.0] * dimension,  # Use the detected dimension
                top_k=limit,
                namespace=namespace,
                include_metadata=True
            )
            
            # Format the response
            matches = []
            if isinstance(result, dict):
                matches = result.get("matches", [])
            else:
                # Handle object-based response in newer SDKs
                matches = getattr(result, "matches", [])
                
            samples = []
            for match in matches:
                if isinstance(match, dict):
                    samples.append({
                        "id": match["id"],
                        "score": match["score"],
                        "metadata": match.get("metadata", {})
                    })
                else:
                    # Handle object-based response
                    samples.append({
                        "id": getattr(match, "id", ""),
                        "score": getattr(match, "score", 0.0),
                        "metadata": getattr(match, "metadata", {})
                    })
            
            return {
                "namespace": namespace,
                "display_name": next((BotNamespace.get_display_name(bot) for bot in BotNamespace if bot.value == namespace), namespace),
                "samples": samples
            }
        except Exception as query_error:
            logger.exception(f"Error during vector query: {query_error}")
            # Return empty samples rather than failing completely
            return {
                "namespace": namespace,
                "display_name": next((BotNamespace.get_display_name(bot) for bot in BotNamespace if bot.value == namespace), namespace),
                "samples": [],
                "error": str(query_error)
            }
            
    except Exception as e:
        logger.exception(f"Error fetching samples: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching samples: {str(e)}")

@router.get("/namespace/{namespace}/search")
async def search_namespace(namespace: str, query: str, top_k: int = 10):
    """Search within a namespace using a text query"""
    if namespace not in BotNamespace.values():
        raise HTTPException(status_code=404, detail=f"Namespace '{namespace}' not found or not recognized")
    
    try:
        # Use the query_text function from app.pinecone to perform a semantic search
        results = query_text(query=query, bot=namespace, top_k=top_k)
        
        return {
            "namespace": namespace,
            "display_name": next((BotNamespace.get_display_name(bot) for bot in BotNamespace if bot.value == namespace), namespace),
            "query": query,
            "results": results
        }
    except Exception as e:
        logger.exception(f"Error searching namespace: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching namespace: {str(e)}")

@router.delete("/namespace/{namespace}")
async def delete_namespace(namespace: str):
    """Delete all vectors in a namespace"""
    if namespace not in BotNamespace.values():
        raise HTTPException(status_code=404, detail=f"Namespace '{namespace}' not found or not recognized")
    
    try:
        # Delete all vectors in the namespace
        index.delete(delete_all=True, namespace=namespace)
        
        # Return success response
        return {
            "status": "success",
            "message": f"All vectors in namespace '{namespace}' have been deleted"
        }
    except Exception as e:
        logger.exception(f"Error deleting namespace data: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting namespace data: {str(e)}")