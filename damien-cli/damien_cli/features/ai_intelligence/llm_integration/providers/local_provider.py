import httpx # HTTP client for making requests to local LLM server
import json
import time
from typing import Dict, List, Optional, Any, AsyncGenerator

from ..base import BaseLLMService, LLMRequest, LLMResponse, LLMProvider
from damien_cli.core.app_logging import get_logger

logger = get_logger(__name__)

class LocalLLMProvider(BaseLLMService):
    """
    Provider for interfacing with a local LLM server (e.g., Ollama).
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        self.base_url = self.config.get('base_url', 'http://localhost:11434') # Default Ollama URL
        self.model = self.config.get('default_model', 'llama3') # Default model
        self.client = httpx.AsyncClient(timeout=60.0) # Longer timeout for local models
        
        # Ollama specific endpoint (can be made configurable if supporting other local servers)
        self.generate_endpoint = f"{self.base_url}/api/generate"
        self.chat_endpoint = f"{self.base_url}/api/chat" # For conversational models

        print(f"LocalLLMProvider initialized: base_url='{self.base_url}', model='{self.model}'")

    async def complete(self, request: LLMRequest) -> LLMResponse:
        start_time = time.time()
        
        # Determine if we should use chat or generate endpoint based on system_prompt
        use_chat_endpoint = bool(request.system_prompt)
        
        payload = {
            "model": self.config.get("model", self.model), # Allow overriding model per request via config if needed
            "prompt": request.prompt,
            "stream": False, # For non-streaming completion
            "options": {
                "temperature": request.temperature,
                "top_p": request.top_p,
                # Ollama uses num_predict for max_tokens equivalent for /api/generate
                # For /api/chat, it's implicitly handled or part of message history.
                # This might need adjustment based on Ollama's specific behavior for max output.
                "num_predict": request.max_tokens 
            }
        }
        
        if use_chat_endpoint:
            messages = [{"role": "user", "content": request.prompt}]
            if request.system_prompt:
                messages.insert(0, {"role": "system", "content": request.system_prompt})
            
            chat_payload = {
                "model": payload["model"],
                "messages": messages,
                "stream": False,
                "options": payload["options"]
            }
            endpoint = self.chat_endpoint
            actual_payload = chat_payload
        else:
            # /api/generate doesn't directly support system_prompt in the same way
            # It might need to be prepended to the user prompt if no system field exists.
            if request.system_prompt:
                 payload["prompt"] = f"{request.system_prompt}\n\nUser: {request.prompt}\nAssistant:" # Basic way to include system prompt
            endpoint = self.generate_endpoint
            actual_payload = payload


        try:
            logger.debug(f"Sending request to Local LLM: {endpoint} with payload: {actual_payload}")
            response_http = await self.client.post(endpoint, json=actual_payload)
            response_http.raise_for_status() # Raise an exception for HTTP error codes (4xx or 5xx)
            
            data = response_http.json()
            logger.debug(f"Received response from Local LLM: {data}")

            content = ""
            finish_reason = "unknown"
            prompt_tokens = data.get('prompt_eval_count', 0) # Ollama specific
            completion_tokens = data.get('eval_count', 0) # Ollama specific for /api/generate

            if use_chat_endpoint:
                content = data.get("message", {}).get("content", "")
                # For chat, eval_count is for the completion. prompt_eval_count might not be present or accurate for total input.
                # This part of token counting for chat might need refinement based on Ollama's exact response structure.
            else: # /api/generate
                content = data.get("response", "")
            
            if data.get("done", True): # Assuming 'done' indicates completion
                 finish_reason = "stop"


            return LLMResponse(
                content=content.strip(),
                model=payload["model"],
                provider=LLMProvider.LOCAL,
                usage={
                    'prompt_tokens': prompt_tokens,
                    'completion_tokens': completion_tokens,
                    'total_tokens': prompt_tokens + completion_tokens,
                    'estimated_cost': 0.0 # Local models are free
                },
                latency_ms=(time.time() - start_time) * 1000,
                finish_reason=finish_reason,
                metadata={"raw_response": data}
            )

        except httpx.RequestError as e:
            logger.error(f"HTTPX RequestError connecting to Local LLM ({endpoint}): {e}")
            raise ConnectionError(f"Failed to connect to local LLM server at {self.base_url}: {e}") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"Local LLM API error ({endpoint}): {e.response.status_code} - {e.response.text}")
            raise ValueError(f"Local LLM API error: {e.response.status_code} - {e.response.text}") from e
        except Exception as e:
            logger.error(f"Error processing local LLM response ({endpoint}): {e}")
            raise

    async def stream_complete(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        # Placeholder - Ollama supports streaming, this would need to be implemented
        # by setting "stream": True in the payload and handling the streaming response.
        logger.warning("Streaming not yet fully implemented for LocalLLMProvider. Using non-streaming completion as fallback.")
        # Fallback to non-streaming for now, or raise NotImplementedError
        response_obj = await self.complete(request)
        yield response_obj.content
        # raise NotImplementedError("Streaming is not yet implemented for LocalLLMProvider.")

    def estimate_cost(self, request: LLMRequest) -> float:
        return 0.0 # Local models typically have no direct API cost

    def validate_request(self, request: LLMRequest) -> bool:
        if not request.prompt:
            logger.warning("LocalLLMProvider: Prompt cannot be empty.")
            return False
        # Add other local model specific validations if any (e.g. model availability check)
        return True