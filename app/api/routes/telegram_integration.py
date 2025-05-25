# app/api/routes/telegram_integration.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import TelegramChat, Driver
from pydantic import BaseModel
from typing import Optional, List

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


@router.post("/link-driver")
async def link_driver_to_chat(
    request: LinkDriverToChatRequest, db: Session = Depends(get_db)
):
    """Link a driver to a Telegram chat"""
    try:
        # Check if driver exists
        driver = db.query(Driver).filter(Driver.id == request.driver_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")

        # Check if chat exists
        chat = (
            db.query(TelegramChat)
            .filter(TelegramChat.chat_token == request.chat_token)
            .first()
        )
        if not chat:
            raise HTTPException(status_code=404, detail="Telegram chat not found")

        # Link driver to chat
        driver.chat_id = chat.id
        db.commit()

        return {
            "message": f"Driver {driver.name} linked to chat {chat.group_name}",
            "driver_id": driver.id,
            "chat_id": chat.id,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error linking driver: {str(e)}")


@router.post("/unlink-driver")
async def unlink_driver_from_chat(
    request: UnlinkDriverRequest, db: Session = Depends(get_db)
):
    """Unlink a driver from Telegram chat"""
    try:
        driver = db.query(Driver).filter(Driver.id == request.driver_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")

        driver.chat_id = None
        db.commit()

        return {"message": f"Driver {driver.name} unlinked from Telegram chat"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error unlinking driver: {str(e)}")


@router.get("/driver-chat-links", response_model=List[DriverChatLinkResponse])
async def get_driver_chat_links(db: Session = Depends(get_db)):
    """Get all driver-chat links"""
    try:
        drivers_with_chats = db.query(Driver).filter(Driver.chat_id.isnot(None)).all()

        links = []
        for driver in drivers_with_chats:
            chat = (
                db.query(TelegramChat).filter(TelegramChat.id == driver.chat_id).first()
            )
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
        raise HTTPException(status_code=500, detail=f"Error retrieving links: {str(e)}")


@router.get("/available-drivers")
async def get_available_drivers(db: Session = Depends(get_db)):
    """Get drivers not linked to any Telegram chat"""
    try:
        available_drivers = db.query(Driver).filter(Driver.chat_id.is_(None)).all()

        return [
            {"id": driver.id, "name": driver.name, "company_id": driver.company_id}
            for driver in available_drivers
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving available drivers: {str(e)}"
        )


@router.get("/available-chats")
async def get_available_chats(db: Session = Depends(get_db)):
    """Get Telegram chats that can be used for driver linking"""
    try:
        chats = db.query(TelegramChat).all()

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
        raise HTTPException(status_code=500, detail=f"Error retrieving chats: {str(e)}")


@router.post("/send-test-message/{chat_token}")
async def send_test_message(
    chat_token: int,
    message: str = "🤖 Test message from Logistics Bot",
    db: Session = Depends(get_db),
):
    """Send a test message to a specific Telegram chat"""
    try:
        from aiogram import Bot
        from app.config import get_settings

        settings = get_settings()
        bot = Bot(token=settings.telegram_bot_token)

        # Verify chat exists in database
        chat = (
            db.query(TelegramChat).filter(TelegramChat.chat_token == chat_token).first()
        )
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
                "message": f"Failed to send message: {str(telegram_error)}",
                "chat_token": chat_token,
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error sending test message: {str(e)}"
        )


@router.get("/chat-info/{chat_token}")
async def get_chat_info(chat_token: int, db: Session = Depends(get_db)):
    """Get information about a specific Telegram chat"""
    try:
        from aiogram import Bot
        from app.config import get_settings

        # Get chat from database
        chat = (
            db.query(TelegramChat).filter(TelegramChat.chat_token == chat_token).first()
        )
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found in database")

        # Get live chat info from Telegram
        settings = get_settings()
        bot = Bot(token=settings.telegram_bot_token)

        try:
            telegram_chat = await bot.get_chat(chat_id=chat_token)
            await bot.session.close()

            # Get linked drivers
            linked_drivers = db.query(Driver).filter(Driver.chat_id == chat.id).all()

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
                    "error": f"Could not fetch live info: {str(telegram_error)}"
                },
                "linked_drivers": [],
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting chat info: {str(e)}"
        )


@router.delete("/chat/{chat_token}")
async def remove_telegram_chat(chat_token: int, db: Session = Depends(get_db)):
    """Remove a Telegram chat from the system"""
    try:
        chat = (
            db.query(TelegramChat).filter(TelegramChat.chat_token == chat_token).first()
        )
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        # Unlink any drivers first
        drivers = db.query(Driver).filter(Driver.chat_id == chat.id).all()
        for driver in drivers:
            driver.chat_id = None

        # Delete the chat
        db.delete(chat)
        db.commit()

        return {
            "message": f"Chat {chat.group_name} removed successfully",
            "unlinked_drivers": len(drivers),
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error removing chat: {str(e)}")


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
