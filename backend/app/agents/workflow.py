from typing import Dict, Any, List, TypedDict
import time

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
    def run(self, client_info: Dict[str, Any]) -> Dict[str, Any]:
        industry = client_info.get("industry", "General Industry")
        competitors = client_info.get("competitors", "Main Competitors")
        return {
            "industry_trends": [f"Increasing digital automation in {industry}", "High demand for video content"],
            "competitor_analysis": f"Analyzed top competitors including {competitors}.",
            "target_audience_summary": client_info.get("target_audience", "General audience"),
            "status": "completed"
        }

class StrategyAgent:
    def run(self, client_info: Dict[str, Any], research_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "positioning": f"Leading high-value brand in {client_info.get('industry', 'tech')}",
            "recommended_channels": ["Instagram", "LinkedIn", "Blog", "SEO"],
            "monthly_plan": "4 Instagram posts, 2 LinkedIn articles, 1 Long-form Blog post per week",
            "goals": client_info.get("marketing_goals", "Brand awareness & lead generation"),
            "status": "completed"
        }

class ContentAgent:
    def run(self, client_info: Dict[str, Any], strategy_data: Dict[str, Any], topic: str) -> Dict[str, Any]:
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
    def run(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "grammar_check": "Passed",
            "brand_consistency": "Verified",
            "fact_check": "Verified",
            "approved": True,
            "notes": "Content aligns with brand voice guidelines.",
            "status": "completed"
        }

class SupervisorAgent:
    def __init__(self):
        self.research_agent = ResearchAgent()
        self.strategy_agent = StrategyAgent()
        self.content_agent = ContentAgent()
        self.qa_agent = QAAgent()

    def execute_workflow(self, client_info: Dict[str, Any], service_requested: str, target_topic: str = "") -> Dict[str, Any]:
        logs = []
        logs.append(f"Supervisor initiated workflow for service: {service_requested}")
        
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
        content_res = self.content_agent.run(client_info, strategy_res, target_topic)
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
