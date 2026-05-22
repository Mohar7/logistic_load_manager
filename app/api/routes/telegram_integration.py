# app/api/routes/telegram_integration.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_any_authenticated, require_role
from app.db.database import get_db
from app.db.models import Driver, TelegramChat

router = APIRouter(
    prefix="/telegram",
    tags=["telegram-integration"],
    responses={404: {"description": "Not found"}},
)


class LinkDriverToChatRequest(BaseModel):
    driver_id: int
    chat_token: int


class UnlinkDriverRequest(BaseModel):
    driver_id: int


class DriverChatLinkResponse(BaseModel):
    driver_id: int
    driver_name: str
    chat_id: int
    chat_name: str
    chat_token: int


@router.post("/link-driver", dependencies=[Depends(require_any_authenticated)])
async def link_driver_to_chat(
    request: LinkDriverToChatRequest, db: AsyncSession = Depends(get_db)
):
    """Link a driver to a Telegram chat"""
    try:
        # Check if driver exists
        driver_result = await db.execute(
            select(Driver).where(Driver.id == request.driver_id)
        )
        driver = driver_result.scalar_one_or_none()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")

        # Check if chat exists
        chat_result = await db.execute(
            select(TelegramChat).where(TelegramChat.chat_token == request.chat_token)
        )
        chat = chat_result.scalar_one_or_none()
        if not chat:
            raise HTTPException(status_code=404, detail="Telegram chat not found")

        # Link driver to chat
        driver.chat_id = chat.id
        await db.commit()

        return {
            "message": f"Driver {driver.name} linked to chat {chat.group_name}",
            "driver_id": driver.id,
            "chat_id": chat.id,
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error linking driver: {e!s}")


@router.post("/unlink-driver", dependencies=[Depends(require_any_authenticated)])
async def unlink_driver_from_chat(
    request: UnlinkDriverRequest, db: AsyncSession = Depends(get_db)
):
    """Unlink a driver from Telegram chat"""
    try:
        result = await db.execute(
            select(Driver).where(Driver.id == request.driver_id)
        )
        driver = result.scalar_one_or_none()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")

        driver.chat_id = None
        await db.commit()

        return {"message": f"Driver {driver.name} unlinked from Telegram chat"}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error unlinking driver: {e!s}")


@router.get("/driver-chat-links", response_model=list[DriverChatLinkResponse])
async def get_driver_chat_links(db: AsyncSession = Depends(get_db)):
    """Get all driver-chat links"""
    try:
        result = await db.execute(select(Driver).where(Driver.chat_id.isnot(None)))
        drivers_with_chats = list(result.scalars().all())

        links = []
        for driver in drivers_with_chats:
            chat_result = await db.execute(
                select(TelegramChat).where(TelegramChat.id == driver.chat_id)
            )
            chat = chat_result.scalar_one_or_none()
            if chat:
                link_data = {
                    "driver_id": driver.id,
                    "driver_name": driver.name,
                    "chat_id": chat.id,
                    "chat_name": chat.group_name,
                    "chat_token": chat.chat_token,
                }
                links.append(DriverChatLinkResponse(**link_data))

        return links

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving links: {e!s}")


@router.get("/available-drivers")
async def get_available_drivers(db: AsyncSession = Depends(get_db)):
    """Get drivers not linked to any Telegram chat"""
    try:
        result = await db.execute(select(Driver).where(Driver.chat_id.is_(None)))
        available_drivers = list(result.scalars().all())

        return [
            {"id": driver.id, "name": driver.name, "company_id": driver.company_id}
            for driver in available_drivers
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving available drivers: {e!s}"
        )


@router.get("/available-chats")
async def get_available_chats(db: AsyncSession = Depends(get_db)):
    """Get Telegram chats that can be used for driver linking"""
    try:
        result = await db.execute(select(TelegramChat))
        chats = list(result.scalars().all())

        return [
            {
                "id": chat.id,
                "group_name": chat.group_name,
                "chat_token": chat.chat_token,
                "company_id": chat.company_id,
            }
            for chat in chats
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chats: {e!s}")


@router.post(
    "/send-test-message/{chat_token}",
    dependencies=[Depends(require_any_authenticated)],
)
async def send_test_message(
    chat_token: int,
    message: str = "🤖 Test message from Logistics Bot",
    db: AsyncSession = Depends(get_db),
):
    """Send a test message to a specific Telegram chat"""
    try:
        from aiogram import Bot

        from app.config import get_settings

        settings = get_settings()
        bot = Bot(token=settings.telegram_bot_token)

        # Verify chat exists in database
        chat_result = await db.execute(
            select(TelegramChat).where(TelegramChat.chat_token == chat_token)
        )
        chat = chat_result.scalar_one_or_none()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found in database")

        # Send test message
        try:
            await bot.send_message(
                chat_id=chat_token,
                text=f"🤖 **Test Message**\n\n{message}\n\n_Sent from Logistics Bot API_",
                parse_mode="Markdown",
            )
            await bot.session.close()

            return {
                "success": True,
                "message": f"Test message sent to {chat.group_name}",
                "chat_token": chat_token,
            }

        except Exception as telegram_error:
            await bot.session.close()
            return {
                "success": False,
                "message": f"Failed to send message: {telegram_error!s}",
                "chat_token": chat_token,
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error sending test message: {e!s}"
        )


@router.get("/chat-info/{chat_token}")
async def get_chat_info(chat_token: int, db: AsyncSession = Depends(get_db)):
    """Get information about a specific Telegram chat"""
    try:
        from aiogram import Bot

        from app.config import get_settings

        # Get chat from database
        chat_result = await db.execute(
            select(TelegramChat).where(TelegramChat.chat_token == chat_token)
        )
        chat = chat_result.scalar_one_or_none()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found in database")

        # Get live chat info from Telegram
        settings = get_settings()
        bot = Bot(token=settings.telegram_bot_token)

        try:
            telegram_chat = await bot.get_chat(chat_id=chat_token)
            await bot.session.close()

            # Get linked drivers
            linked_result = await db.execute(
                select(Driver).where(Driver.chat_id == chat.id)
            )
            linked_drivers = list(linked_result.scalars().all())

            return {
                "database_info": {
                    "id": chat.id,
                    "group_name": chat.group_name,
                    "chat_token": chat.chat_token,
                    "company_id": chat.company_id,
                },
                "telegram_info": {
                    "title": telegram_chat.title,
                    "type": telegram_chat.type,
                    "member_count": getattr(telegram_chat, "member_count", None),
                    "description": getattr(telegram_chat, "description", None),
                },
                "linked_drivers": [
                    {"id": driver.id, "name": driver.name} for driver in linked_drivers
                ],
            }

        except Exception as telegram_error:
            await bot.session.close()
            return {
                "database_info": {
                    "id": chat.id,
                    "group_name": chat.group_name,
                    "chat_token": chat.chat_token,
                    "company_id": chat.company_id,
                },
                "telegram_info": {
                    "error": f"Could not fetch live info: {telegram_error!s}"
                },
                "linked_drivers": [],
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting chat info: {e!s}"
        )


@router.delete("/chat/{chat_token}", dependencies=[Depends(require_role("admin"))])
async def remove_telegram_chat(chat_token: int, db: AsyncSession = Depends(get_db)):
    """Remove a Telegram chat from the system"""
    try:
        chat_result = await db.execute(
            select(TelegramChat).where(TelegramChat.chat_token == chat_token)
        )
        chat = chat_result.scalar_one_or_none()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        # Unlink any drivers first
        drivers_result = await db.execute(
            select(Driver).where(Driver.chat_id == chat.id)
        )
        drivers = list(drivers_result.scalars().all())
        for driver in drivers:
            driver.chat_id = None

        # Delete the chat
        await db.delete(chat)
        await db.commit()

        return {
            "message": f"Chat {chat.group_name} removed successfully",
            "unlinked_drivers": len(drivers),
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error removing chat: {e!s}")


@router.get("/bot-status")
async def get_bot_status():
    """Check if the Telegram bot is online and responsive"""
    try:
        from aiogram import Bot

        from app.config import get_settings

        settings = get_settings()
        bot = Bot(token=settings.telegram_bot_token)

        try:
            me = await bot.get_me()
            await bot.session.close()

            return {
                "status": "online",
                "bot_info": {
                    "id": me.id,
                    "username": me.username,
                    "first_name": me.first_name,
                    "can_join_groups": me.can_join_groups,
                    "can_read_all_group_messages": me.can_read_all_group_messages,
                    "supports_inline_queries": me.supports_inline_queries,
                },
            }

        except Exception as e:
            await bot.session.close()
            return {"status": "error", "error": str(e)}

    except Exception as e:
        return {"status": "configuration_error", "error": str(e)}
