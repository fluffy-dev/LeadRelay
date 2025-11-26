from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status

from src.crm import schemas, service, exceptions
from src.crm.dependencies import get_crm_service

router = APIRouter(tags=["CRM"])


@router.post("/operators", response_model=schemas.OperatorResponse)
async def create_operator(
        data: schemas.OperatorCreate,
        svc: Annotated[service.CRMService, Depends(get_crm_service)]
):
    """Creates a new operator."""
    return await svc.create_operator(data)


@router.get("/operators", response_model=List[schemas.OperatorResponse])
async def list_operators(
        svc: Annotated[service.CRMService, Depends(get_crm_service)]
):
    """Lists all operators."""
    return await svc.get_operators()


@router.post("/sources", response_model=schemas.SourceResponse)
async def create_source(
        data: schemas.SourceCreate,
        svc: Annotated[service.CRMService, Depends(get_crm_service)]
):
    """Creates a new source (bot)."""
    return await svc.create_source(data)


@router.put("/sources/{source_id}/distribution")
async def configure_distribution(
        source_id: int,
        config: schemas.SourceConfigUpdate,
        svc: Annotated[service.CRMService, Depends(get_crm_service)]
):
    """Configures operator weights for a specific source."""
    try:
        await svc.configure_source_distribution(source_id, config)
        return {"status": "updated"}
    except exceptions.SourceNotFound:
        raise HTTPException(status_code=404, detail="Source not found")


@router.post("/cases", response_model=schemas.CaseResponse)
async def register_case(
        data: schemas.CaseCreate,
        svc: Annotated[service.CRMService, Depends(get_crm_service)]
):
    """
    Registers a new case/appeal.

    - Finds or creates a Lead.
    - Distributes to an Operator based on source config, weights, and current load.
    - If no operator available, operator_id will be null.
    """
    case = await svc.process_new_case(data)

    # Enrich response manually for identifier since schema expects flattened structure
    response = schemas.CaseResponse(
        id=case.id,
        lead_identifier=data.lead_identifier,  # simplified for response
        source_id=case.source_id,
        operator_id=case.operator_id,
        status=case.status.value,
        created_at=case.created_at
    )
    return response


@router.get("/cases", response_model=List[schemas.CaseResponse])
async def list_cases(
        svc: Annotated[service.CRMService, Depends(get_crm_service)]
):
    """Lists all cases for monitoring."""
    cases = await svc.get_all_cases()
    # Manual mapping needed because Pydantic needs flattened identifier from related Lead
    return [
        schemas.CaseResponse(
            id=c.id,
            lead_identifier=c.lead.identifier,
            source_id=c.source_id,
            operator_id=c.operator_id,
            status=c.status.value,
            created_at=c.created_at
        )
        for c in cases
    ]