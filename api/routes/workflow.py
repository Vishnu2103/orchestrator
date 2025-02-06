import logging
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel, Field
import json

from ..services.workflow_manager import WorkflowManager
from ..services.state_store import StateStore
from ..services.event_bus import EventBus

logger = logging.getLogger(__name__)

# Initialize services
state_store = StateStore()
event_bus = EventBus()
workflow_manager = WorkflowManager(state_store, event_bus)

router = APIRouter()


class ModuleConfig(BaseModel):
    """Module configuration"""
    identifier: str
    user_config: Dict = Field(default_factory=dict)


class WorkflowRequest(BaseModel):
    """Workflow creation request"""
    workflow_name: str = Field(alias="canvas_name")
    modules: Dict[str, ModuleConfig]

    class Config:
        populate_by_name = True


class WorkflowResponse(BaseModel):
    """Workflow creation response"""
    workflow_id: str
    status: str
    message: str


@router.post("/workflow", response_model=WorkflowResponse)
async def create_workflow(request: WorkflowRequest):
    """Create and start a new workflow"""
    try:
        workflow_id = workflow_manager.create_workflow(request.model_dump(by_alias=True))
        return WorkflowResponse(
            workflow_id=workflow_id,
            status="CREATED",
            message="Workflow started successfully"
        )
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post("/workflow/internal", response_model=WorkflowResponse)
async def create_workflow(request: WorkflowRequest):
    """Create and start a new workflow"""
    try:
        workflow_id = workflow_manager.create_workflow_internal(request.model_dump(by_alias=True))
        return WorkflowResponse(
            workflow_id=workflow_id,
            status="CREATED",
            message="Workflow started successfully"
        )
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get("/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get current workflow status"""
    try:
        status = workflow_manager.get_workflow_status(workflow_id)
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow {workflow_id} not found"
            )
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/workflow/{workflow_id}/stream")
async def stream_workflow(workflow_id: str, request: Request):
    """Stream workflow execution events"""
    try:
        queue = workflow_manager.stream_events(workflow_id)

        async def event_generator():
            try:
                while True:
                    if await request.is_disconnected():
                        break

                    try:
                        # Non-blocking get with timeout
                        event = queue.get(timeout=1.0)
                        yield {
                            "event": event["type"],
                            "data": json.dumps(event)
                        }
                    except:
                        # No event available, continue waiting
                        continue

            except Exception as e:
                logger.error(f"Error in event stream: {e}")
            finally:
                # Clean up
                event_bus.unsubscribe(workflow_id, queue)

        return EventSourceResponse(event_generator())

    except Exception as e:
        logger.error(f"Failed to create event stream: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
