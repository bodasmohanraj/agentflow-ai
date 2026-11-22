
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

import os
import json
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class LLMProviderError(Exception):
    """Raised when LLM provider operation fails."""
    pass


class LLMProvider:
    """Abstract base class for LLM providers."""
    
    def __init__(self):
        self.base_url = os.getenv("FREELLMAPI_BASE_URL", "")
        self.api_key = os.getenv("FREELLMAPI_API_KEY", "")
        self.model = os.getenv("FREELLMAPI_MODEL", "gpt-3.5-turbo")
        self.temperature = float(os.getenv("FREELLMAPI_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("FREELLMAPI_MAX_TOKENS", "1000"))
        
        # Validate required credentials
        if not self.api_key:
            logger.warning("No FREELLMAPI_API_KEY configured - mock mode enabled")
    
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
        
        url = self.base_url.rstrip("/") + "/v1/chat/completions" if self.base_url else "https://api.openai.com/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
        }
        
        # Add API key if available
        if self.api_key:
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
            client = httpx.Client(timeout=30.0)
            response = client.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"LLM provider error {response.status_code}: {error_detail}")
                raise LLMProviderError(f"LLM provider failed: {error_detail}")
            
            result = response.json()
            
            # Extract token usage if available
            token_usage = self.get_token_usage(result)
            
            return {
                "content": result.get("choices", [{}])[0].get("message", {}).get("content", ""),
                "role": result.get("choices", [{}])[0].get("message", {}).get("role", "assistant"),
                "model": result.get("model", self.model),
                "token_usage": token_usage,
                "raw_response": result,
                "success": True,
            }
            
        except LLMProviderError:
            raise
        except Exception as e:
            logger.error(f"LLM provider request failed: {e}")
            raise LLMProviderError(f"LLM provider request failed: {e}")
    
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

The strategy should use the client's actual information and be tailored to their specific business context. Clearly identify the strategy as AI-generated mock output.'''
        
        messages = [{"role": "user", "content": prompt}]
        
        response = self.chat_completion(messages=messages)
        
        # Since we're using mock output until real AI is connected,
        # return a structured mock strategy
        strategy = self._create_mock_strategy(client_info)
        strategy["_ai_generated"] = True
        strategy["_mock_note"] = "AI-generated mock output - real AI provider not configured"
        
        return strategy
    
    def _create_mock_strategy(self, client_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create a structured mock strategy using client information."""
        business_name = client_info.get("business_name", "the business")
        industry = client_info.get("industry", "your industry")
        target_audience = client_info.get("target_audience", "your target audience")
        competitors = client_info.get("competitors", "your competitors")
        brand_voice = client_info.get("brand_voice", "professional")
        marketing_goals = client_info.get("marketing_goals", "growth")
        
        return {
            "executive_summary": f"AI-generated marketing strategy for {business_name}, a {industry} business targeting {target_audience}.",
            "business_analysis": f"{business_name} operates in the {industry} industry, competing with {competitors}. The business focuses on serving {target_audience} with a {brand_voice} brand voice.",
            "target_audience_personas": [
                {
                    "name": "Primary Persona",
                    "demographics": f"{target_audience} aged 25-50",
                    "goals": "Seeks growth and value",
                    "pain_points": "Limited marketing resources, unclear channel strategy",
                },
                {
                    "name": "Secondary Persona", 
                    "demographics": "Early career professionals",
                    "goals": "Career advancement and networking",
                    "pain_points": "Time-constrained, seeking efficient marketing",
                }
            ],
            "competitor_positioning": f"{business_name} differentiates itself from {competitors} through its {brand_voice} brand voice and customer-centric approach.",
            "brand_positioning": f"{business_name} is positioned as a {brand_voice} brand in the {industry} space, focusing on {marketing_goals}.",
            "marketing_objectives": [
                f"Increase brand awareness among {target_audience}",
                f"Generate qualified leads for {business_name}",
                f"Improve customer engagement and retention"
            ],
            "recommended_channels": ["Instagram", "LinkedIn", "Blog", "Email Marketing"],
            "content_pillars": [
                f"Industry insights and trends",
                f"Customer success stories",
                f"Product education and features",
                f"Thought leadership content",
            ],
            "campaign_ideas": [
                f"30-day {marketing_goals} campaign featuring customer testimonials",
                f"Weekly LinkedIn thought leadership articles from {business_name}",
                f"Instagram Reels showcasing behind-the-scenes operations",
            ],
            "kpis_and_metrics": {
                "website_traffic_goal": "20% increase month-over-month",
                "lead_generation_target": "50 new leads per month",
                "social_engagement_rate": "3% average engagement rate",
                "content_performance": "Top 3 pieces achieve 1000+ views",
            },
            "thirty_day_action_plan": [
                "Week 1: Audit current marketing assets and competitor landscape",
                "Week 2: Develop content pillars and channel strategy",
                "Week 3: Create and schedule first wave of content",
                "Week 4: Launch paid advertising campaigns",
                "Week 5: Monitor KPIs and optimize underperforming assets",
                "Week 6: Review results and plan quarterly strategy",
            ],
            "generated_at": __import__('datetime').datetime.now().isoformat(),
        }
        
        return strategy
