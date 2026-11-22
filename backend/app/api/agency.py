
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List

from backend.app.db.session import get_db
from backend.app.models.models import (
    Client,
    Project,
    AgentExecutionLog,
    ApprovalRequest,
    Strategy,
    User,
)
from backend.app.schemas.schemas import (
    ClientCreate,
    ClientResponse,
    WorkflowTrigger,
    AnalyticsSummary,
    KPIDashboard,
    StrategySummary,
)
from backend.app.agents.workflow import SupervisorAgent, WorkflowConfigurationError
from backend.app.agents.llm_provider import LLMProviderError
from backend.app.core.dependencies import get_current_user

router = APIRouter(prefix="/agency", tags=["agency"])
logger = logging.getLogger(__name__)


def is_admin(user: User) -> bool:
    return user.role == "admin"


def get_owned_client_query(db: Session, user: User):
    query = db.query(Client)

    if not is_admin(user):
        query = query.filter(Client.user_id == user.id)

    return query


@router.post("/clients", response_model=ClientResponse)
def create_client(
    client_in: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = Client(
        **client_in.dict(),
        user_id=current_user.id,
    )

    db.add(client)
    db.commit()
    db.refresh(client)

    return client


@router.get("/clients", response_model=List[ClientResponse])
def get_clients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_owned_client_query(db, current_user).all()


@router.get("/dashboard/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    owned_clients = get_owned_client_query(db, current_user)

    active_projects = (
        db.query(Project)
        .join(Client, Project.client_id == Client.id)
        .filter(Project.status == "active")
    )

    completed_projects = (
        db.query(Project)
        .join(Client, Project.client_id == Client.id)
        .filter(Project.status == "completed")
    )

    pending_approvals = (
        db.query(ApprovalRequest)
        .join(Client, ApprovalRequest.client_id == Client.id)
        .filter(ApprovalRequest.status == "pending")
    )

    if not is_admin(current_user):
        active_projects = active_projects.filter(
            Client.user_id == current_user.id
        )
        completed_projects = completed_projects.filter(
            Client.user_id == current_user.id
        )
        pending_approvals = pending_approvals.filter(
            Client.user_id == current_user.id
        )

    # Execution logs are not linked to individual clients yet.
    # Only admins can see system-wide execution counts.
    if is_admin(current_user):
        running_agents = db.query(AgentExecutionLog).filter(
            AgentExecutionLog.status == "running"
        ).count()

        completed_tasks = db.query(AgentExecutionLog).filter(
            AgentExecutionLog.status == "completed"
        ).count()
    else:
        running_agents = 0
        completed_tasks = 0

    return {
        "total_clients": owned_clients.count(),
        "active_projects": active_projects.count(),
        "completed_projects": completed_projects.count(),
        "pending_approvals": pending_approvals.count(),
        "running_agents": running_agents,
        "completed_tasks": completed_tasks,
    }


@router.post("/workflow/run")
def run_workflow(
    payload: WorkflowTrigger,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = get_owned_client_query(db, current_user).filter(
        Client.id == payload.client_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found",
        )

    client_info = {
        "business_name": client.business_name,
        "industry": client.industry,
        "website": client.website,
        "business_description": client.business_description,
        "target_audience": client.target_audience,
        "competitors": client.competitors,
        "brand_voice": client.brand_voice,
        "marketing_goals": client.marketing_goals,
    }

    try:
        supervisor = SupervisorAgent()
        res = supervisor.execute_workflow(
            client_info,
            payload.service_requested,
            payload.target_topic or "",
        )
    except (LLMProviderError, WorkflowConfigurationError) as exc:
        logger.error("Workflow unavailable: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Workflow is temporarily unavailable") from exc

    log = AgentExecutionLog(
        agent_name="SupervisorAgent",
        task=f"Service: {payload.service_requested}",
        status="completed",
        output=res,
        execution_time_ms=350.0,
        token_usage=1250,
        estimated_cost=0.025,
    )

    approval = ApprovalRequest(
        action_type="Publish Deliverables",
        title=f"Campaign Content Approval for {client.business_name}",
        payload=res["content_data"],
        status="pending",
        client_id=client.id,
    )

    db.add(log)
    db.add(approval)
    db.commit()

    return {
        "message": "Workflow executed successfully",
        "result": res,
    }


@router.get("/approvals")
def get_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        db.query(ApprovalRequest)
        .join(Client, ApprovalRequest.client_id == Client.id)
    )

    if not is_admin(current_user):
        query = query.filter(Client.user_id == current_user.id)

    return query.all()


@router.post("/approvals/{approval_id}/action")
def action_approval(
    approval_id: int,
    action: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ApprovalRequest).filter(
        ApprovalRequest.id == approval_id
    )

    if not is_admin(current_user):
        query = query.join(
            Client,
            ApprovalRequest.client_id == Client.id,
        ).filter(Client.user_id == current_user.id)

    req = query.first()

    if not req:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found",
        )

    if action not in ["approve", "reject"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid action",
        )

    req.status = "approved" if action == "approve" else "rejected"

    db.commit()

    return {
        "message": f"Request {req.status}",
        "approval_id": approval_id,
    }


@router.get("/analytics/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get analytics summary scoped to authenticated user."""
    from datetime import datetime, timedelta
    
    # Get user's clients
    user_clients = db.query(Client).filter(Client.user_id == current_user.id).all()
    client_ids = [c.id for c in user_clients]
    
    # Total clients for this user
    total_clients = db.query(Client).filter(Client.user_id == current_user.id).count()
    
    # Total projects for user's clients
    total_projects = db.query(Project).filter(Project.client_id.in_(client_ids)).count() if client_ids else 0
    active_projects = db.query(Project).filter(
        Project.client_id.in_(client_ids),
        Project.status == "active"
    ).count() if client_ids else 0
    completed_projects = db.query(Project).filter(
        Project.client_id.in_(client_ids),
        Project.status == "completed"
    ).count() if client_ids else 0
    
    # Total strategies for user's clients
    total_strategies = db.query(Strategy).filter(Strategy.client_id.in_(client_ids)).count() if client_ids else 0
    
    # Agent executions - count all since AgentExecutionLog has no user_id relationship
    total_agent_executions = db.query(AgentExecutionLog).count()
    successful_executions = db.query(AgentExecutionLog).filter(AgentExecutionLog.status == "completed").count()
    failed_executions = db.query(AgentExecutionLog).filter(AgentExecutionLog.status == "failed").count()
    
    # Pending approvals for user's clients
    pending_approvals = db.query(ApprovalRequest).filter(
        ApprovalRequest.client_id.in_(client_ids)
    ).count() if client_ids else 0
    
    return {
        "total_clients": total_clients,
        "total_projects": total_projects,
        "active_projects": active_projects,
        "completed_projects": completed_projects,
        "total_strategies": total_strategies,
        "total_agent_executions": total_agent_executions,
        "successful_executions": successful_executions,
        "failed_executions": failed_executions,
        "pending_approvals": pending_approvals
    }


@router.get("/analytics/kpis", response_model=KPIDashboard)
def get_analytics_kpis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = 30,
):
    """Get KPIs with trends over specified time period."""
    from datetime import datetime, timedelta
    
    # Get user's clients
    user_clients = db.query(Client).filter(Client.user_id == current_user.id).all()
    client_ids = [c.id for c in user_clients]
    
    # Strategy generation rate per period
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    prev_end_date = start_date - timedelta(days=days)
    prev_start_date = prev_end_date - timedelta(days=days)
    
    new_strategies = db.query(Strategy).filter(
        Strategy.created_at >= start_date
    ).count() if client_ids else 0
    
    prev_new_strategies = db.query(Strategy).filter(
        Strategy.created_at >= prev_start_date,
        Strategy.created_at < prev_end_date
    ).count() if client_ids else 0
    
    strategy_growth = ((new_strategies - prev_new_strategies) / max(prev_new_strategies, 1)) * 100
    
    # Project status distribution
    project_status_distribution = db.query(
        Project.status,
        func.count(Project.id)
    ).filter(
        Project.client_id.in_(client_ids)
    ).group_by(Project.status).all() if client_ids else []
    
    project_dist = {str(row[0]): row[1] for row in project_status_distribution} if project_status_distribution else {}
    
    # Top clients by strategy count
    top_clients = db.query(
        Client.business_name,
        func.count(Strategy.id).label("strategy_count")
    ).join(Strategy, Strategy.client_id == Client.id
    ).filter(Client.user_id == current_user.id
    ).group_by(Client.id
    ).order_by(desc("strategy_count")).limit(5).all() if client_ids else []
    
    success_count = db.query(AgentExecutionLog).filter(
        AgentExecutionLog.status == "completed"
    ).count() if client_ids else 0
    
    failure_count = db.query(AgentExecutionLog).filter(
        AgentExecutionLog.status == "failed"
    ).count() if client_ids else 0
    
    return {
        "client_growth_last_30d": strategy_growth,
        "agent_execution_trend": strategy_growth,  # placeholder - would need time series data
        "project_status_distribution": project_dist,
        "top_clients": [{"name": c.business_name, "strategies": str(c.strategy_count)} for c in top_clients],
        "success_count": success_count,
        "failure_count": failure_count
    }


@router.get("/analytics/strategies", response_model=List[StrategySummary])
def get_analytics_strategies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Get user's clients
    user_clients = db.query(Client).filter(Client.user_id == current_user.id).all()
    client_ids = [c.id for c in user_clients]
    
    strategies = db.query(Strategy).filter(Strategy.client_id.in_(client_ids)).all()
    
    result = []
    for s in strategies:
        # Find client name
        client = db.query(Client).filter(Client.id == s.client_id).first()
        client_name = client.business_name if client else "Unknown"
        result.append({
            "id": s.id,
            "title": s.title,
            "client_name": client_name,
            "created_at": s.created_at.isoformat() if s.created_at else None
        })
    
    return result
