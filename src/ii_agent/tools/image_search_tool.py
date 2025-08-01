from ii_agent.llm.message_history import MessageHistory
from ii_agent.tools.base import (
    LLMTool,
    ToolImplOutput,
)
from ii_agent.tools.clients.web_search_client import create_image_search_client
from ii_agent.core.storage.models.settings import Settings
from typing import Any, Optional
import aiohttp
import asyncio


class ImageSearchTool(LLMTool):
    name = "image_search"
    description = """Performs an image search using a search engine API and returns a list of image URLs."""
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query to perform."},
        },
        "required": ["query"],
    }
    output_type = "array"

    def __init__(self, settings: Optional[Settings] = None, max_results=5, **kwargs):
        self.max_results = max_results
        self.image_search_client = create_image_search_client(
            settings=settings, max_results=max_results, **kwargs
        )

    def is_available(self):
        return self.image_search_client

    async def _check_image_url(self, url: str) -> bool:
        """Check if an image URL is accessible and returns a valid image."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        return content_type.startswith('image/')
                    return False
        except Exception:
            return False

    async def _get_valid_images(self, query: str, max_attempts: int = 3) -> list:
        """Get valid images by checking URLs and searching again if needed."""
        valid_images = []
        attempts = 0
        
        while len(valid_images) == 0 and attempts < max_attempts:
            attempts += 1
            search_query = query if attempts == 1 else f"{query} high quality"
            
            try:
                # Get initial search results
                search_results = await self.image_search_client.forward_async(search_query)
                
                if not search_results:
                    continue
                    
                # Check each image URL
                check_tasks = []
                for item in search_results[:min(10, len(search_results))]:  # Check up to 10 images
                    if isinstance(item, dict) and 'url' in item:
                        check_tasks.append(self._check_image_url(item['url']))
                    elif isinstance(item, str):
                        check_tasks.append(self._check_image_url(item))
                
                if check_tasks:
                    url_validity = await asyncio.gather(*check_tasks, return_exceptions=True)
                    
                    # Filter valid images
                    for i, is_valid in enumerate(url_validity):
                        if is_valid is True and i < len(search_results):
                            valid_images.append(search_results[i])
                            if len(valid_images) >= self.max_results:
                                break
                                
            except Exception as e:
                print(f"Error in attempt {attempts}: {str(e)}")
                continue
        
        return valid_images

    async def run_impl(
        self,
        tool_input: dict[str, Any],
        message_history: Optional[MessageHistory] = None,
    ) -> ToolImplOutput:
        query = tool_input["query"]
        try:
            # Get valid images with URL checking
            valid_images = await self._get_valid_images(query)
            
            if not valid_images:
                return ToolImplOutput(
                    f"No valid images found for query: {query}",
                    f"Failed to find valid images for query: {query}",
                    auxiliary_data={"success": False, "reason": "no_valid_images"}
                )
            
            return ToolImplOutput(
                valid_images,
                f"Image Search Results with query: {query} successfully retrieved using {self.image_search_client.name}. Found {len(valid_images)} valid images.",
                auxiliary_data={"success": True, "valid_images_count": len(valid_images)}
            )
        except Exception as e:
            return ToolImplOutput(
                f"Error searching the web with {self.image_search_client.name}: {str(e)}",
                f"Failed to search the web with query: {query}",
                auxiliary_data={"success": False},
            )
