import json
import logging
from typing import Dict, Any, List, TypedDict

from backend.app.agents.llm_provider import FreeLLMAPIProvider, LLMProviderError
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class WorkflowConfigurationError(Exception):
    """Raised when the selected workflow mode is unsafe for this environment."""


def _live_json(provider: FreeLLMAPIProvider, instruction: str, context: Dict[str, Any], fields: Dict[str, str]) -> Dict[str, Any]:
    """Ask the OpenAI-compatible chat endpoint for the agent's existing fields."""
    field_spec = ", ".join(f'"{name}": {kind}' for name, kind in fields.items())
    response = provider.chat_completion(messages=[
        {
            "role": "system",
            "content": (
                "You are one step in the AgentFlow workflow. Return only one valid JSON object, "
                "with exactly the requested keys and value types. Do not use markdown fences. "
                "Do not claim research or verification that was not performed."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Task: {instruction}\nRequired JSON fields: {{{field_spec}}}\n"
                f"Available context: {json.dumps(context, ensure_ascii=False, default=str)}"
            ),
        },
    ])
    try:
        result = json.loads(response["content"])
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise LLMProviderError("FreeLLMAPI returned an invalid workflow response") from exc
    if not isinstance(result, dict) or set(result) != set(fields):
        raise LLMProviderError("FreeLLMAPI returned an invalid workflow response")
    for key, expected_type in fields.items():
        value = result[key]
        valid = {
            "string": isinstance(value, str),
            "string_list": isinstance(value, list) and all(isinstance(item, str) for item in value),
            "boolean": isinstance(value, bool),
        }.get(expected_type, False)
        if not valid:
            raise LLMProviderError("FreeLLMAPI returned an invalid workflow response")
    result["status"] = "completed"
    return result

class AgentState(TypedDict):
    client_info: Dict[str, Any]
    service_requested: str
    target_topic: str
    research_data: Dict[str, Any]
    strategy_data: Dict[str, Any]
    content_data: Dict[str, Any]
    qa_data: Dict[str, Any]
    approval_required: bool
    status: str
    logs: List[str]

class ResearchAgent:
    def __init__(self, provider: FreeLLMAPIProvider = None):
        self.provider = provider

    def run(self, client_info: Dict[str, Any]) -> Dict[str, Any]:
        if self.provider:
            return _live_json(
                self.provider,
                "Summarize industry trends, competitor context, and the target audience. Be clear about assumptions and do not present unverified claims as researched facts.",
                client_info,
                {"industry_trends": "string_list", "competitor_analysis": "string", "target_audience_summary": "string"},
            )
        industry = client_info.get("industry", "General Industry")
        competitors = client_info.get("competitors", "Main Competitors")
        return {
            "industry_trends": [f"Increasing digital automation in {industry}", "High demand for video content"],
            "competitor_analysis": f"Analyzed top competitors including {competitors}.",
            "target_audience_summary": client_info.get("target_audience", "General audience"),
            "status": "completed"
        }

class StrategyAgent:
    def __init__(self, provider: FreeLLMAPIProvider = None):
        self.provider = provider

    def run(self, client_info: Dict[str, Any], research_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.provider:
            return _live_json(
                self.provider,
                "Create a marketing strategy from the provided client information and research summary.",
                {"client_info": client_info, "research_data": research_data},
                {"positioning": "string", "recommended_channels": "string_list", "monthly_plan": "string", "goals": "string"},
            )
        return {
            "positioning": f"Leading high-value brand in {client_info.get('industry', 'tech')}",
            "recommended_channels": ["Instagram", "LinkedIn", "Blog", "SEO"],
            "monthly_plan": "4 Instagram posts, 2 LinkedIn articles, 1 Long-form Blog post per week",
            "goals": client_info.get("marketing_goals", "Brand awareness & lead generation"),
            "status": "completed"
        }

class ContentAgent:
    def __init__(self, provider: FreeLLMAPIProvider = None):
        self.provider = provider

    def run(self, client_info: Dict[str, Any], strategy_data: Dict[str, Any], topic: str, service_requested: str = "") -> Dict[str, Any]:
        if self.provider:
            return _live_json(
                self.provider,
                f"Create the requested Instagram post, LinkedIn post, and blog article for the requested service ({service_requested or 'marketing'}), about {topic or 'the stated marketing goals'}. Follow the brand voice. Return the actual deliverable text, not explanations.",
                {"client_info": client_info, "strategy_data": strategy_data, "topic": topic, "service_requested": service_requested},
                {"instagram_post": "string", "linkedin_post": "string", "blog_article": "string", "brand_voice_used": "string"},
            )
        voice = client_info.get("brand_voice", "Professional & Engaging")
        topic_name = topic or "Growth Strategies"
        return {
            "instagram_post": f"🚀 Maximize your growth with {client_info.get('business_name', 'our brand')}! #{topic_name.replace(' ', '')} #Growth",
            "linkedin_post": f"In today's fast-evolving market, {topic_name} is crucial for businesses aiming for sustainable growth. Here is our perspective on {topic_name}...",
            "blog_article": f"# Guide to {topic_name}\n\nIn this article, we explore how modern strategies transform brand outcomes...",
            "brand_voice_used": voice,
            "status": "completed"
        }

class QAAgent:
    def __init__(self, provider: FreeLLMAPIProvider = None):
        self.provider = provider

    def run(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.provider:
            return _live_json(
                self.provider,
                "Review grammar, consistency with the provided content's brand voice, and whether factual claims are supported by available context. Do not claim external fact checking. Mark unsupported claims as unverified and set approved false when a material issue remains.",
                {"content_data": content_data},
                {"grammar_check": "string", "brand_consistency": "string", "fact_check": "string", "approved": "boolean", "notes": "string"},
            )
        return {
            "grammar_check": "Not run in development mock mode",
            "brand_consistency": "Not run in development mock mode",
            "fact_check": "Not run in development mock mode",
            "approved": False,
            "notes": "QA was not performed in development mock mode.",
            "status": "completed"
        }

class SupervisorAgent:
    def __init__(self, ai_mode: str = None):
        self.ai_mode = ai_mode or settings.WORKFLOW_AI_MODE
        if self.ai_mode == "mock" and settings.ENVIRONMENT.lower() == "production":
            raise WorkflowConfigurationError("Mock workflow mode is disabled in production")
        provider = FreeLLMAPIProvider() if self.ai_mode == "live" else None
        self.research_agent = ResearchAgent(provider)
        self.strategy_agent = StrategyAgent(provider)
        self.content_agent = ContentAgent(provider)
        self.qa_agent = QAAgent(provider)

    def execute_workflow(self, client_info: Dict[str, Any], service_requested: str, target_topic: str = "") -> Dict[str, Any]:
        logs = []
        logs.append(f"Supervisor initiated workflow for service: {service_requested}")
        logs.append("Workflow mode: live FreeLLMAPI" if self.ai_mode == "live" else "Workflow mode: explicit deterministic development mock")
        
        # Step 1: Research
        logs.append("Assigning task to Research Agent...")
        research_res = self.research_agent.run(client_info)
        logs.append("Research Agent completed task.")
        
        # Step 2: Strategy
        logs.append("Assigning task to Strategy Agent...")
        strategy_res = self.strategy_agent.run(client_info, research_res)
        logs.append("Strategy Agent completed task.")
        
        # Step 3: Content Creation
        logs.append("Assigning task to Content Creation Agent...")
        content_res = self.content_agent.run(client_info, strategy_res, target_topic, service_requested)
        logs.append("Content Creation Agent completed task.")
        
        # Step 4: Quality Assurance
        logs.append("Assigning task to Quality Assurance Agent...")
        qa_res = self.qa_agent.run(content_res)
        logs.append("QA Agent completed task.")
        
        logs.append("Workflow completed. Preparing approval item.")

        return {
            "client_info": client_info,
            "service_requested": service_requested,
            "research_data": research_res,
            "strategy_data": strategy_res,
            "content_data": content_res,
            "qa_data": qa_res,
            "approval_required": True,
            "status": "completed",
            "logs": logs
        }
