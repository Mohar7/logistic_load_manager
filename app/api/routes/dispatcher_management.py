# app/api/routes/dispatcher_management.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.dispatchers import AddDispatcher, DispatcherResponse
from app.services.dispatcher_service import DispatcherService

router = APIRouter(
    prefix="/dispatchers",
    tags=["dispatchers"],
    responses={404: {"description": "Not found"}},
)

# -------------------------------
# Create a new dispatcher
# -------------------------------


@router.post(
    "/", response_model=DispatcherResponse, status_code=status.HTTP_201_CREATED
)
async def create_dispatcher(
    dispatcher_data: AddDispatcher,
    db: AsyncSession = Depends(get_db),
):
    service = DispatcherService(db)
    try:
        return await service.add_dispatcher(dispatcher_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


# -------------------------------
# Get dispatcher by ID
# -------------------------------


@router.get("/{dispatcher_id}", response_model=DispatcherResponse)
async def read_dispatcher(dispatcher_id: int, db: AsyncSession = Depends(get_db)):
    service = DispatcherService(db)
    dispatcher = await service.get_dispatcher_by_id(dispatcher_id)
    if not dispatcher:
        raise HTTPException(status_code=404, detail="Dispatcher not found")
    return dispatcher


# -------------------------------
# Get dispatcher by Telegram ID
# -------------------------------


@router.get("/telegram/{telegram_id}", response_model=DispatcherResponse)
async def get_dispatcher_by_telegram(
    telegram_id: int, db: AsyncSession = Depends(get_db)
):
    service = DispatcherService(db)
    dispatcher = await service.get_dispatcher_by_telegram_id(telegram_id)
    if not dispatcher:
        raise HTTPException(status_code=404, detail="Dispatcher not found")
    return dispatcher


# -------------------------------
# Get list of dispatchers
# -------------------------------


@router.get("/", response_model=list[DispatcherResponse])
async def read_dispatchers(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    service = DispatcherService(db)
    return await service.get_dispatchers(skip=skip, limit=limit)


# -------------------------------
# Update a dispatcher
# -------------------------------


@router.put("/{dispatcher_id}", response_model=DispatcherResponse)
async def update_dispatcher(
    dispatcher_id: int,
    name: str | None = None,
    telegram_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = DispatcherService(db)
    try:
        updated = await service.update_dispatcher(
            dispatcher_id=dispatcher_id, name=name, telegram_id=telegram_id
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Dispatcher not found")
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


# -------------------------------
# Delete a dispatcher
# -------------------------------


@router.delete("/{dispatcher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dispatcher(dispatcher_id: int, db: AsyncSession = Depends(get_db)):
    service = DispatcherService(db)
    try:
        deleted = await service.delete_dispatcher(dispatcher_id)
        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to delete dispatcher")
        return
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
