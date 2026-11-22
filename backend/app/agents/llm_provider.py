
"""Modular LLM Provider Abstraction for AgentFlow AI.

This module provides a configurable LLM provider abstraction that supports
FreeLLMAPI (OpenAI-compatible) and can be extended to support OpenAI or
other providers in the future.

Environment variables (via .env):
- FREELLMAPI_BASE_URL: OpenAI-compatible base URL
- FREELLMAPI_API_KEY: API key for FreeLLMAPI
- FREELLMAPI_MODEL: Model name to use
- FREELLMAPI_TEMPERATURE: Sampling temperature
- FREELLMAPI_MAX_TOKENS: Maximum tokens to generate
"""

import logging
from typing import Optional, Dict, Any, List

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class LLMProviderError(Exception):
    """Raised when LLM provider operation fails."""
    pass


class LLMProvider:
    """Abstract base class for LLM providers."""
    
    def __init__(self):
        self.base_url = settings.FREELLMAPI_BASE_URL.rstrip("/")
        self.api_key = settings.FREELLMAPI_API_KEY
        self.model = settings.FREELLMAPI_MODEL
        self.temperature = settings.FREELLMAPI_TEMPERATURE
        self.max_tokens = settings.FREELLMAPI_MAX_TOKENS
    
    def chat_completion(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Send a chat completion request to the LLM provider.
        
        Args:
            messages: List of message dicts with role and content
            **kwargs: Additional provider-specific options
            
        Returns:
            Dict with response content, token usage, and metadata
        """
        raise NotImplementedError("Subclasses must implement chat_completion")
    
    def get_model(self) -> str:
        """Return the configured model name."""
        return self.model
    
    def get_token_usage(self, response: Dict[str, Any]) -> Optional[int]:
        """Extract token usage from response. Returns None if unavailable."""
        usage = response.get("usage", {})
        if isinstance(usage, dict):
            return usage.get("total_tokens")
        return None
    
    def get_cost_estimate(self, token_usage: int, model: Optional[str] = None) -> Optional[float]:
        """Estimate cost based on token usage. Returns None if unavailable."""
        # Cost calculation would depend on the specific model pricing
        # This is a placeholder that can be overridden by subclasses
        return None


class FreeLLMAPIProvider(LLMProvider):
    """FreeLLMAPI (OpenAI-compatible) provider implementation.
    
    Supports any OpenAI-compatible API endpoint, including local deployments
    and managed services like OpenRouter, TogetherAI, etc.
    """
    
    def chat_completion(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Send chat completion via FreeLLMAPI OpenAI-compatible endpoint."""
        import httpx
        
        if not self.base_url or not self.api_key:
            raise LLMProviderError("FreeLLMAPI is not configured")
        endpoint = "/chat/completions" if self.base_url.endswith("/v1") else "/v1/chat/completions"
        url = self.base_url + endpoint
        
        headers = {
            "Content-Type": "application/json",
        }
        
        headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Build request payload
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }
        
        try:
            import httpx
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=headers, json=payload)
            if not response.is_success:
                logger.error("FreeLLMAPI returned HTTP %s", response.status_code)
                raise LLMProviderError("FreeLLMAPI request failed")
            
            result = response.json()
            
            choices = result.get("choices")
            if not isinstance(choices, list) or not choices:
                raise LLMProviderError("FreeLLMAPI returned an invalid response")
            message = choices[0].get("message") if isinstance(choices[0], dict) else None
            content = message.get("content") if isinstance(message, dict) else None
            if not isinstance(content, str) or not content.strip():
                raise LLMProviderError("FreeLLMAPI returned an invalid response")

            # Extract token usage if available
            token_usage = self.get_token_usage(result)
            
            return {
                "content": content,
                "role": message.get("role", "assistant"),
                "model": result.get("model", self.model),
                "token_usage": token_usage,
                "raw_response": result,
                "success": True,
            }
            
        except LLMProviderError:
            raise
        except Exception as exc:
            logger.error("FreeLLMAPI request failed: %s", type(exc).__name__)
            raise LLMProviderError("FreeLLMAPI request failed") from exc
    
    def generate_strategy(self, client_info: Dict[str, Any], strategy_type: str = "marketing") -> Dict[str, Any]:
        """Generate a marketing strategy based on client information.
        
        Args:
            client_info: Dict with client business information
            strategy_type: Type of strategy to generate
            
        Returns:
            Dict with generated strategy content
        """
        # Build prompt using client information
        business_name = client_info.get("business_name", "the business")
        industry = client_info.get("industry", "your industry")
        target_audience = client_info.get("target_audience", "your target audience")
        competitors = client_info.get("competitors", "your competitors")
        brand_voice = client_info.get("brand_voice", "professional")
        marketing_goals = client_info.get("marketing_goals", "growth")
        
        prompt = f"""Generate a comprehensive marketing strategy for {business_name} in the {industry} industry.

Client Information:
- Business: {business_name}
- Industry: {industry}
- Target Audience: {target_audience}
- Competitors: {competitors}
- Brand Voice: {brand_voice}
- Marketing Goals: {marketing_goals}

Please provide a structured marketing strategy with the following sections:
1. Executive Summary
2. Business Analysis
3. Target Audience Personas
4. Competitor Positioning
5. Brand Positioning
6. Marketing Objectives
7. Recommended Marketing Channels
8. Content Pillars
9. Campaign Ideas
10. KPIs and Success Metrics
11. 30-Day Marketing Action Plan

The strategy should use the client's actual information and be tailored to their specific business context. Return the result as AI-generated output."""
        
        messages = [{"role": "user", "content": prompt}]
        
        response = self.chat_completion(messages=messages)
        return {
            "content": response["content"],
            "model": response["model"],
            "token_usage": response["token_usage"],
            "_ai_generated": True,
        }
