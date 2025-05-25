# app/bot/utils/formatters.py
from datetime import datetime
from typing import Dict, Any
from app.db.models import Load, Leg, Driver


def escape_markdown(text: str) -> str:
    """Escape special characters for Telegram markdown"""
    if not text:
        return ""

    # Escape characters that have special meaning in Telegram markdown
    special_chars = [
        "_",
        "*",
        "[",
        "]",
        "(",
        ")",
        "~",
        "`",
        ">",
        "#",
        "+",
        "-",
        "=",
        "|",
        "{",
        "}",
        ".",
        "!",
    ]
    escaped_text = str(text)

    for char in special_chars:
        escaped_text = escaped_text.replace(char, f"\\{char}")

    return escaped_text


class MessageFormatters:
    """Utility class for formatting bot messages"""

    @staticmethod
    def format_load_summary(load: Load) -> str:
        """Format load information for summary display"""
        trip_id = escape_markdown(str(load.trip_id))
        pickup = escape_markdown(str(load.pickup_address))
        dropoff = escape_markdown(str(load.dropoff_address))

        text = f"🚛 *{trip_id}*\n"
        text += f"📍 {pickup} → {dropoff}\n"
        text += f"🕐 {load.start_time_str} - {load.end_time_str}\n"
        text += f"💰 ${float(load.rate):,.2f}"

        if load.assigned_driver:
            driver_name = escape_markdown(str(load.assigned_driver))
            text += f"\n👤 {driver_name}"

        return text

    @staticmethod
    def format_load_details(load: Load, legs: list = None) -> str:
        """Format detailed load information"""
        trip_id = escape_markdown(str(load.trip_id))
        pickup = escape_markdown(str(load.pickup_address))
        dropoff = escape_markdown(str(load.dropoff_address))

        text = f"🚛 *Load Details: {trip_id}*\n\n"
        text += f"*Route:* {pickup} → {dropoff}\n"
        text += f"*Start:* {load.start_time_str}\n"
        text += f"*End:* {load.end_time_str}\n"
        text += f"*Rate:* ${float(load.rate):,.2f}\n"
        text += f"*Rate/Mile:* ${float(load.rate_per_mile):,.2f}\n"

        if load.distance:
            text += f"*Distance:* {float(load.distance):,.1f} mi\n"

        if load.assigned_driver:
            driver_name = escape_markdown(str(load.assigned_driver))
            text += f"*Driver:* {driver_name}\n"
        else:
            text += f"*Driver:* Not assigned\n"

        if load.is_team_load:
            text += "*Type:* Team Load\n"

        if legs:
            text += f"\n*Legs ({len(legs)}):*\n"
            for i, leg in enumerate(legs, 1):
                pickup_facility = escape_markdown(str(leg.pickup_facility_name))
                dropoff_facility = escape_markdown(str(leg.dropoff_facility_name))
                text += f"{i}. {pickup_facility} → {dropoff_facility}\n"
                text += f"   {leg.pickup_time_str} - {leg.dropoff_time_str}\n"
                if leg.distance:
                    text += f"   Distance: {float(leg.distance):,.1f} mi\n"

        return text

    @staticmethod
    def format_driver_info(driver: Driver) -> str:
        """Format driver information"""
        driver_name = escape_markdown(str(driver.name))
        text = f"👤 *{driver_name}*\n"

        if driver.company:
            company_name = escape_markdown(str(driver.company.name))
            text += f"🏢 {company_name}\n"
        if driver.chat:
            chat_name = escape_markdown(str(driver.chat.group_name))
            text += f"💬 Connected to: {chat_name}\n"

        return text

    @staticmethod
    def format_company_summary(
        company, driver_count: int = 0, load_count: int = 0, telegram_count: int = 0
    ) -> str:
        """Format company summary information"""
        company_name = escape_markdown(str(company.name))
        carrier_id = escape_markdown(str(company.carrier_identifier))

        text = f"🏢 *{company_name}*\n"
        text += f"• DOT: {company.usdot}\n"
        text += f"• MC: {company.mc}\n"
        text += f"• Carrier ID: {carrier_id}\n"

        if driver_count > 0:
            text += f"• Drivers: {driver_count}"
            if telegram_count > 0:
                text += f" ({telegram_count} 📱)"
            text += "\n"

        if load_count > 0:
            text += f"• Loads: {load_count}\n"

        return text

    @staticmethod
    def format_system_stats(stats: Dict[str, Any]) -> str:
        """Format system-wide statistics"""
        text = "📊 *System Statistics*\n\n"

        if "loads" in stats:
            text += "*📋 Load Statistics:*\n"
            text += f"• Total Loads: {stats['loads'].get('total', 0)}\n"
            text += f"• Assigned: {stats['loads'].get('assigned', 0)}\n"
            text += f"• Unassigned: {stats['loads'].get('unassigned', 0)}\n\n"

        if "drivers" in stats:
            text += "*👥 Driver Statistics:*\n"
            text += f"• Total Drivers: {stats['drivers'].get('total', 0)}\n"
            text += f"• Telegram-Enabled: {stats['drivers'].get('telegram', 0)}\n"
            if stats["drivers"].get("total", 0) > 0:
                coverage = (
                    stats["drivers"].get("telegram", 0)
                    / stats["drivers"].get("total", 1)
                ) * 100
                text += f"• Coverage: {coverage:.1f}%\n\n"

        if "companies" in stats:
            text += "*🏢 Company Statistics:*\n"
            text += f"• Total Companies: {stats['companies'].get('total', 0)}\n"
            text += f"• Active Companies: {stats['companies'].get('active', 0)}\n\n"

        text += "*🔄 Cross-Company Status:*\n"
        text += "• Cross-Company Access: ✅ Enabled\n"
        text += "• Multi-Company Operations: ✅ Active\n"

        return text
