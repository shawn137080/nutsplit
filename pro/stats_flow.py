"""Pro: /stats — cross-month spending trends by category."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

import database

logger = logging.getLogger(__name__)

_PRO_UPSELL = (
    "⭐ <b>/stats is a Pro feature</b>\n\n"
    "Upgrade to SplitBot Pro to unlock:\n"
    "  • Monthly spending trends by category\n"
    "  • Budget alerts\n"
    "  • Cloud backup\n\n"
    "Self-host for free or contact us for hosted Pro."
)

_BAR_WIDTH = 12  # chars for the bar chart


def _bar(value: float, max_value: float, width: int = _BAR_WIDTH) -> str:
    if max_value == 0:
        return "░" * width
    filled = round((value / max_value) * width)
    return "█" * filled + "░" * (width - filled)


async def handle_stats_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    is_pro: bool = False,
) -> None:
    """Handle /stats — show spending trends across months."""
    if update.effective_chat is None or update.effective_message is None:
        return

    if not is_pro:
        await update.effective_message.reply_text(_PRO_UPSELL, parse_mode="HTML")
        return

    group_id = str(update.effective_chat.id)
    group = database.get_group(group_id)
    if group is None:
        await update.effective_message.reply_text(
            "Please run /start first to set up your household."
        )
        return

    currency: str = group.get("currency") or "CAD"

    # Fetch the last N months with data
    all_months = database.get_all_months_summary(group_id)
    if not all_months:
        await update.effective_message.reply_text("No expense data yet.")
        return

    recent_months = [m["month_label"] for m in all_months[:6]]  # newest first

    # --- Build per-month totals ---
    month_totals: dict[str, float] = {}
    category_sums: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for ml in recent_months:
        expenses = database.get_expenses(group_id, ml)
        total = sum(float(e.get("total", 0)) for e in expenses)
        month_totals[ml] = total
        for e in expenses:
            cat = (e.get("category") or "Other").title()
            category_sums[cat][ml] += float(e.get("total", 0))

    max_month_total = max(month_totals.values()) if month_totals else 1

    # --- Monthly totals bar chart ---
    lines = [f"📊 <b>Spending Trends</b> ({currency})\n"]

    lines.append("<b>Monthly Total</b>")
    for ml in recent_months:
        total = month_totals[ml]
        bar = _bar(total, max_month_total)
        lines.append(f"<code>{ml[:7]:7} {bar} ${total:,.0f}</code>")

    # --- Top categories across all months ---
    cat_totals_all = {
        cat: sum(months.values()) for cat, months in category_sums.items()
    }
    top_cats = sorted(cat_totals_all, key=lambda c: cat_totals_all[c], reverse=True)[:5]

    lines.append("\n<b>Top Categories (all time)</b>")
    max_cat = max(cat_totals_all[c] for c in top_cats) if top_cats else 1
    for cat in top_cats:
        amt = cat_totals_all[cat]
        bar = _bar(amt, max_cat)
        lines.append(f"<code>{cat[:7]:7} {bar} ${amt:,.0f}</code>")

    # --- Average monthly spend ---
    avg = sum(month_totals.values()) / len(month_totals) if month_totals else 0
    lines.append(f"\n📅 Avg/month: <b>${avg:,.2f} {currency}</b>")

    await update.effective_message.reply_text("\n".join(lines), parse_mode="HTML")
