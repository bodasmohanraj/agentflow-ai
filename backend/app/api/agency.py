from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.app.db.session import get_db
from backend.app.models.models import Client, Project, AgentExecutionLog, ApprovalRequest
from backend.app.schemas.schemas import ClientCreate, ClientResponse, WorkflowTrigger
from backend.app.agents.workflow import SupervisorAgent

router = APIRouter(prefix="/agency", tags=["agency"])

@router.post("/clients", response_model=ClientResponse)
def create_client(client_in: ClientCreate, db: Session = Depends(get_db)):
    client = Client(**client_in.dict())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

@router.get("/clients", response_model=List[ClientResponse])
def get_clients(db: Session = Depends(get_db)):
    return db.query(Client).all()

@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_clients = db.query(Client).count()
    active_projects = db.query(Project).filter(Project.status == "active").count()
    completed_projects = db.query(Project).filter(Project.status == "completed").count()
    pending_approvals = db.query(ApprovalRequest).filter(ApprovalRequest.status == "pending").count()
    running_agents = db.query(AgentExecutionLog).filter(AgentExecutionLog.status == "running").count()
    completed_tasks = db.query(AgentExecutionLog).filter(AgentExecutionLog.status == "completed").count()
    
    return {
        "total_clients": total_clients,
        "active_projects": active_projects,
        "completed_projects": completed_projects,
        "pending_approvals": pending_approvals,
        "running_agents": running_agents,
        "completed_tasks": completed_tasks,
        "monthly_revenue": 14500.0,
        "recent_activity": [
            {"id": 1, "action": "Research Agent finished competitor audit", "time": "10 mins ago"},
            {"id": 2, "action": "Content Agent generated social post", "time": "25 mins ago"},
            {"id": 3, "action": "New Client Onboarded: Apex Digital", "time": "1 hour ago"},
        ]
    }

@router.post("/workflow/run")
def run_workflow(payload: WorkflowTrigger, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == payload.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    client_info = {
        "business_name": client.business_name,
        "industry": client.industry,
        "website": client.website,
        "business_description": client.business_description,
        "target_audience": client.target_audience,
        "competitors": client.competitors,
        "brand_voice": client.brand_voice,
        "marketing_goals": client.marketing_goals
    }

    supervisor = SupervisorAgent()
    res = supervisor.execute_workflow(client_info, payload.service_requested, payload.target_topic or "")

    # Save log
    log = AgentExecutionLog(
        agent_name="SupervisorAgent",
        task=f"Service: {payload.service_requested}",
        status="completed",
        output=res,
        execution_time_ms=350.0,
        token_usage=1250,
        estimated_cost=0.025
    )
    db.add(log)

    # Save approval request
    approval = ApprovalRequest(
        action_type="Publish Deliverables",
        title=f"Campaign Content Approval for {client.business_name}",
        payload=res["content_data"],
        status="pending",
        client_id=client.id
    )
    db.add(approval)
    db.commit()

    return {"message": "Workflow executed successfully", "result": res}

@router.get("/approvals")
def get_approvals(db: Session = Depends(get_db)):
    return db.query(ApprovalRequest).all()

@router.post("/approvals/{approval_id}/action")
def action_approval(approval_id: int, action: str, db: Session = Depends(get_db)):
    req = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")
    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    req.status = "approved" if action == "approve" else "rejected"
    db.commit()
    return {"message": f"Request {req.status}", "approval_id": approval_id}
