
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.app.db.session import get_db
from backend.app.models.models import (
    Client,
    Project,
    AgentExecutionLog,
    ApprovalRequest,
    User,
)
from backend.app.schemas.schemas import (
    ClientCreate,
    ClientResponse,
    WorkflowTrigger,
)
from backend.app.agents.workflow import SupervisorAgent
from backend.app.core.dependencies import get_current_user

router = APIRouter(prefix="/agency", tags=["agency"])


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

    supervisor = SupervisorAgent()

    res = supervisor.execute_workflow(
        client_info,
        payload.service_requested,
        payload.target_topic or "",
    )

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

