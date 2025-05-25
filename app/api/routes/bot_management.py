# app/api/routes/bot_management.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.db.database import get_db
from app.bot.services.user_service import UserService
from app.bot.services.chat_service import ChatService
from app.services.notification_service import NotificationService
from app.db.models import TelegramChat, Dispatchers
from pydantic import BaseModel

router = APIRouter(
    prefix="/bot",
    tags=["bot-management"],
    responses={404: {"description": "Not found"}},
)


# Pydantic models for bot management
class TelegramChatCreate(BaseModel):
    group_name: str
    chat_token: int
    company_id: Optional[int] = None


class TelegramChatResponse(BaseModel):
    id: int
    group_name: str
    chat_token: int
    company_id: Optional[int] = None

    class Config:
        from_attributes = True


class BotUserResponse(BaseModel):
    id: int
    name: str
    telegram_id: int
    role: str
    status: Optional[str] = "active"

    class Config:
        from_attributes = True


class NotificationRequest(BaseModel):
    message: str
    target_type: str  # "all", "drivers", "dispatchers", "specific_chat"
    target_id: Optional[int] = None  # chat_id or user_id if specific


# Chat management endpoints
@router.post("/chats", response_model=TelegramChatResponse)
async def create_telegram_chat(
    chat_data: TelegramChatCreate, db: Session = Depends(get_db)
):
    """Create a new Telegram chat entry"""
    chat_service = ChatService(db)

    success = await chat_service.add_telegram_chat(
        chat_id=chat_data.chat_token,
        chat_title=chat_data.group_name,
        chat_type="group",
        company_id=chat_data.company_id,
    )

    if not success:
        raise HTTPException(
            status_code=400, detail="Chat already exists or creation failed"
        )

    # Fetch the created chat
    chat = await chat_service.get_chat_by_id(chat_data.chat_token)
    if not chat:
        raise HTTPException(status_code=500, detail="Failed to retrieve created chat")

    return TelegramChatResponse(
        id=chat.id,
        group_name=chat.group_name,
        chat_token=chat.chat_token,
        company_id=chat.company_id,
    )


@router.get("/chats", response_model=List[TelegramChatResponse])
async def get_telegram_chats(db: Session = Depends(get_db)):
    """Get all Telegram chats"""
    chat_service = ChatService(db)
    chats = await chat_service.get_all_chats()

    return [
        TelegramChatResponse(
            id=chat.id,
            group_name=chat.group_name,
            chat_token=chat.chat_token,
            company_id=chat.company_id,
        )
        for chat in chats
    ]


@router.delete("/chats/{chat_id}")
async def delete_telegram_chat(chat_id: int, db: Session = Depends(get_db)):
    """Delete a Telegram chat"""
    chat_service = ChatService(db)
    success = await chat_service.remove_telegram_chat(chat_id)

    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")

    return {"message": "Chat deleted successfully"}


# User management endpoints
@router.get("/users", response_model=List[BotUserResponse])
async def get_bot_users(db: Session = Depends(get_db)):
    """Get all bot users (dispatchers and managers)"""
    try:
        users = db.query(Dispatchers).all()

        return [
            BotUserResponse(
                id=user.id,
                name=user.name,
                telegram_id=user.telegram_id,
                role=user.role or "dispatcher",  # Default to dispatcher if role is None
                status="active",
            )
            for user in users
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving users: {str(e)}")


@router.get("/users/managers")
async def get_pending_managers(db: Session = Depends(get_db)):
    """Get all managers (for approval workflow)"""
    try:
        managers = db.query(Dispatchers).filter(Dispatchers.role == "manager").all()

        return [
            {
                "id": manager.id,
                "name": manager.name,
                "telegram_id": manager.telegram_id,
                "role": manager.role,
            }
            for manager in managers
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving managers: {str(e)}"
        )


@router.get("/users/dispatchers")
async def get_dispatchers(db: Session = Depends(get_db)):
    """Get all dispatchers"""
    try:
        dispatchers = (
            db.query(Dispatchers).filter(Dispatchers.role == "dispatcher").all()
        )

        return [
            {
                "id": dispatcher.id,
                "name": dispatcher.name,
                "telegram_id": dispatcher.telegram_id,
                "role": dispatcher.role,
            }
            for dispatcher in dispatchers
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving dispatchers: {str(e)}"
        )


@router.post("/users/{user_id}/approve")
async def approve_user(user_id: int, db: Session = Depends(get_db)):
    """Approve a pending user registration"""
    try:
        user = db.query(Dispatchers).filter(Dispatchers.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # For now, we'll just mark them as active
        # You could add a status column to track approval states

        return {"message": f"User {user.name} approved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error approving user: {str(e)}")


@router.delete("/users/{user_id}")
async def delete_bot_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a bot user"""
    try:
        user = db.query(Dispatchers).filter(Dispatchers.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        db.delete(user)
        db.commit()

        return {"message": f"User {user.name} deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")


# Notification endpoints
@router.post("/notifications/send")
async def send_notification(
    notification: NotificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Send notifications via Telegram bot"""

    async def send_notification_task():
        try:
            from aiogram import Bot
            from app.config import get_settings
            from app.db.models import Driver, TelegramChat

            settings = get_settings()
            bot = Bot(token=settings.telegram_bot_token)

            sent_count = 0
            failed_count = 0

            if notification.target_type == "all":
                # Send to all connected chats
                chats = db.query(TelegramChat).all()
                for chat in chats:
                    try:
                        await bot.send_message(
                            chat_id=chat.chat_token,
                            text=f"📢 System Notification:\n\n{notification.message}",
                        )
                        sent_count += 1
                    except Exception as e:
                        failed_count += 1
                        print(f"Failed to send to chat {chat.group_name}: {e}")

            elif notification.target_type == "drivers":
                # Send to all drivers
                drivers = db.query(Driver).filter(Driver.chat_id.isnot(None)).all()
                for driver in drivers:
                    try:
                        chat = (
                            db.query(TelegramChat)
                            .filter(TelegramChat.id == driver.chat_id)
                            .first()
                        )
                        if chat:
                            await bot.send_message(
                                chat_id=chat.chat_token,
                                text=f"👤 Message for {driver.name}:\n\n{notification.message}",
                            )
                            sent_count += 1
                    except Exception as e:
                        failed_count += 1
                        print(f"Failed to send to driver {driver.name}: {e}")

            elif notification.target_type == "specific_chat" and notification.target_id:
                # Send to specific chat
                try:
                    await bot.send_message(
                        chat_id=notification.target_id, text=notification.message
                    )
                    sent_count = 1
                except Exception as e:
                    failed_count = 1
                    print(f"Failed to send to chat {notification.target_id}: {e}")

            await bot.session.close()
            print(f"Notification sent - Success: {sent_count}, Failed: {failed_count}")

        except Exception as e:
            print(f"Error in notification task: {e}")

    background_tasks.add_task(send_notification_task)

    return {"message": "Notification queued for sending"}


@router.post("/notifications/load/{load_id}")
async def notify_load_assignment(
    load_id: int, driver_id: Optional[int] = None, db: Session = Depends(get_db)
):
    """Send load assignment notification"""

    async def notify_task():
        notification_service = NotificationService(db)
        success = await notification_service.notify_driver_about_load(
            load_id, driver_id
        )
        print(f"Load notification sent: {success}")

    await notify_task()

    return {"message": "Load notification queued"}


# Bot statistics endpoint
@router.get("/stats")
async def get_bot_stats(db: Session = Depends(get_db)):
    """Get bot usage statistics"""
    try:
        from app.db.models import Load, Driver, TelegramChat

        total_chats = db.query(TelegramChat).count()
        total_dispatchers = db.query(Dispatchers).count()
        total_drivers = db.query(Driver).count()
        total_loads = db.query(Load).count()

        # Active assignments
        assigned_loads = db.query(Load).filter(Load.driver_id.isnot(None)).count()
        unassigned_loads = db.query(Load).filter(Load.driver_id.is_(None)).count()

        # Drivers with telegram connections
        connected_drivers = db.query(Driver).filter(Driver.chat_id.isnot(None)).count()

        return {
            "telegram_chats": total_chats,
            "dispatchers": total_dispatchers,
            "drivers": {
                "total": total_drivers,
                "connected_to_telegram": connected_drivers,
            },
            "loads": {
                "total": total_loads,
                "assigned": assigned_loads,
                "unassigned": unassigned_loads,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")


# Webhook endpoint for Telegram (if you want to use webhooks instead of polling)
@router.post("/webhook")
async def telegram_webhook(request: dict, db: Session = Depends(get_db)):
    """Handle Telegram webhook updates"""
    # This would be used if you switch from polling to webhooks
    # Implementation depends on your deployment setup
    return {"status": "ok"}


# Health check for bot
@router.get("/health")
async def bot_health_check():
    """Check if bot is running and configured properly"""
    try:
        from app.config import get_settings
        from aiogram import Bot

        settings = get_settings()

        if (
            not settings.telegram_bot_token
            or settings.telegram_bot_token == "YOUR_TELEGRAM_BOT_TOKEN"
        ):
            return {"status": "error", "message": "Bot token not configured"}

        # Test bot connection
        bot = Bot(token=settings.telegram_bot_token)
        try:
            me = await bot.get_me()
            await bot.session.close()

            return {
                "status": "healthy",
                "bot_info": {
                    "username": me.username,
                    "first_name": me.first_name,
                    "id": me.id,
                },
            }
        except Exception as e:
            await bot.session.close()
            return {"status": "error", "message": f"Bot connection failed: {str(e)}"}

    except Exception as e:
        return {"status": "error", "message": f"Configuration error: {str(e)}"}
