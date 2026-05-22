# app/api/routes/company_management.py
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_any_authenticated, require_role
from app.db.database import get_db
from app.schemas.company import CompanyCreate, CompanyResponse
from app.services.company_service import CompanyService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/companies",
    tags=["companies"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/",
    response_model=CompanyResponse,
    dependencies=[Depends(require_any_authenticated)],
)
async def create_company(company: CompanyCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new company.

    Args:
        company (CompanyCreate): Company data
        db (AsyncSession): Database session

    Returns:
        CompanyResponse: Created company data
    """
    try:
        company_service = CompanyService(db)
        result = await company_service.create_company(
            name=company.name,
            usdot=company.usdot,
            carrier_identifier=company.carrier_identifier,
            mc=company.mc,
        )

        company_data = result["company"]
        return {
            "id": company_data.id,
            "name": company_data.name,
            "usdot": company_data.usdot,
            "carrier_identifier": company_data.carrier_identifier,
            "mc": company_data.mc,
            "drivers_count": result["drivers_count"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating company: {e!s}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a company by ID.

    Args:
        company_id (int): ID of the company to retrieve
        db (AsyncSession): Database session

    Returns:
        CompanyResponse: Company data
    """
    company_service = CompanyService(db)
    result = await company_service.get_company_by_id(company_id)

    if not result:
        raise HTTPException(status_code=404, detail=f"Company with ID {company_id} not found")

    company_data = result["company"]
    return {
        "id": company_data.id,
        "name": company_data.name,
        "usdot": company_data.usdot,
        "carrier_identifier": company_data.carrier_identifier,
        "mc": company_data.mc,
        "drivers_count": result["drivers_count"],
    }


@router.get("/", response_model=list[CompanyResponse])
async def get_companies(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """
    Get all companies with pagination.

    Args:
        skip (int): Number of records to skip
        limit (int): Maximum number of records to return
        db (AsyncSession): Database session

    Returns:
        List[CompanyResponse]: List of companies
    """
    company_service = CompanyService(db)
    results = await company_service.get_companies(skip, limit)

    return [
        {
            "id": result["company"].id,
            "name": result["company"].name,
            "usdot": result["company"].usdot,
            "carrier_identifier": result["company"].carrier_identifier,
            "mc": result["company"].mc,
            "drivers_count": result["drivers_count"],
        }
        for result in results
    ]


@router.put(
    "/{company_id}",
    response_model=CompanyResponse,
    dependencies=[Depends(require_any_authenticated)],
)
async def update_company(
    company_id: int,
    company_update: CompanyCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a company.

    Args:
        company_id (int): ID of the company to update
        company_update (CompanyCreate): Updated company data
        db (AsyncSession): Database session

    Returns:
        CompanyResponse: Updated company data
    """
    try:
        company_service = CompanyService(db)
        result = await company_service.update_company(
            company_id=company_id,
            name=company_update.name,
            usdot=company_update.usdot,
            carrier_identifier=company_update.carrier_identifier,
            mc=company_update.mc,
        )

        if not result:
            raise HTTPException(status_code=404, detail=f"Company with ID {company_id} not found")

        company_data = result["company"]
        return {
            "id": company_data.id,
            "name": company_data.name,
            "usdot": company_data.usdot,
            "carrier_identifier": company_data.carrier_identifier,
            "mc": company_data.mc,
            "drivers_count": result["drivers_count"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating company: {e!s}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{company_id}", dependencies=[Depends(require_role("admin"))])
async def delete_company(company_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a company.

    Args:
        company_id (int): ID of the company to delete
        db (AsyncSession): Database session

    Returns:
        dict: Success message
    """
    try:
        company_service = CompanyService(db)
        result = await company_service.delete_company(company_id)

        if not result:
            raise HTTPException(status_code=404, detail=f"Company with ID {company_id} not found")

        return {"message": f"Company with ID {company_id} successfully deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting company: {e!s}")
        raise HTTPException(status_code=500, detail="Internal server error")
