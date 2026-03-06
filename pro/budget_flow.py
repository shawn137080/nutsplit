"""Pro: /budget — set monthly category budgets and get spending alerts."""

from __future__ import annotations

import json
import logging
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

import database

logger = logging.getLogger(__name__)

_PRO_UPSELL = (
    "⭐ <b>/budget is a Pro feature</b>\n\n"
    "Upgrade to SplitBot Pro to set monthly category budgets "
    "and receive alerts when you're over. "
    "Contact us for hosted Pro."
)

# Budget limits are stored as a JSON blob in the group's settings (using notes field hack)
# We use a dedicated key in database's conversation_state for group-level config.
# Key: "budget_config", stored as JSON: {"Groceries": 500.0, "Dining": 300.0}

_BUDGET_STATE_KEY = "budget_config"


async def _get_budgets(group_id: str) -> dict[str, float]:
    """Read budget config from conversation_state using a special system user."""
    row = database.get_state("__budget__", group_id)
    if row and row.get("context"):
        return row["context"]
    return {}


async def _save_budgets(group_id: str, budgets: dict[str, float]) -> None:
    database.set_state("__budget__", group_id, _BUDGET_STATE_KEY, budgets)


async def handle_budget_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    is_pro: bool = False,
) -> None:
    """
    /budget                    → show current budgets + status
    /budget <category> <amount> → set budget for a category
    /budget <category> off      → remove budget for a category
    """
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
    timezone: str = group.get("timezone") or "America/Toronto"
    args: list[str] = list(context.args) if context.args else []

    budgets = await _get_budgets(group_id)

    # --- Set/remove a budget ---
    if len(args) >= 2:
        category = args[0].title()
        value_raw = args[1].lower()
        if value_raw == "off":
            budgets.pop(category, None)
            await _save_budgets(group_id, budgets)
            await update.effective_message.reply_text(
                f"✅ Budget for <b>{category}</b> removed.", parse_mode="HTML"
            )
            return
        try:
            limit = float(value_raw.replace("$", "").replace(",", ""))
        except ValueError:
            await update.effective_message.reply_text(
                "⚠️ Usage: /budget <category> <amount> or /budget <category> off"
            )
            return
        budgets[category] = limit
        await _save_budgets(group_id, budgets)
        await update.effective_message.reply_text(
            f"✅ Budget for <b>{category}</b> set to <b>${limit:,.2f} {currency}/month</b>.",
            parse_mode="HTML",
        )
        return

    # --- Show current budgets and status ---
    import pytz
    from datetime import datetime
    tz = pytz.timezone(timezone)
    month_label = datetime.now(tz).strftime("%b %Y")

    expenses = database.get_expenses(group_id, month_label)
    cat_spent: dict[str, float] = {}
    for e in expenses:
        cat = (e.get("category") or "Other").title()
        cat_spent[cat] = cat_spent.get(cat, 0.0) + float(e.get("total", 0))

    if not budgets:
        await update.effective_message.reply_text(
            "No budgets set.\n\n"
            "<b>Usage:</b> /budget Groceries 500\n"
            "To remove: /budget Groceries off",
            parse_mode="HTML",
        )
        return

    lines = [f"💰 <b>Budgets — {month_label}</b> ({currency})\n"]
    for cat, limit in sorted(budgets.items()):
        spent = cat_spent.get(cat, 0.0)
        pct = (spent / limit * 100) if limit else 0
        status = "🔴" if pct >= 100 else ("🟡" if pct >= 80 else "🟢")
        lines.append(
            f"{status} <b>{cat}</b>\n"
            f"   ${spent:,.2f} / ${limit:,.2f} ({pct:.0f}%)"
        )

    lines.append("\n<i>Use /budget &lt;category&gt; &lt;amount&gt; to add/update</i>")
    await update.effective_message.reply_text("\n".join(lines), parse_mode="HTML")
