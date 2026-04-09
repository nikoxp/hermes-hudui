"""Token cost endpoint — calculates estimated USD costs from token counts."""

from datetime import datetime
from fastapi import APIRouter

from hermes_hud.collectors.sessions import collect_sessions
from hermes_hud.collectors.config import collect_config

router = APIRouter()

# ── Pricing per 1M tokens (USD) ──────────────────────────
# Source: https://www.anthropic.com/pricing (April 2026)
# Source: https://openai.com/api/pricing/ (April 2026)

MODEL_PRICING: dict[str, dict] = {
    # Anthropic
    "claude-opus-4-6": {
        "input": 15.00, "output": 75.00,
        "cache_read": 1.50, "cache_write": 18.75,
        "reasoning": 15.00,
    },
    "claude-sonnet-4-6": {
        "input": 3.00, "output": 15.00,
        "cache_read": 0.30, "cache_write": 3.75,
        "reasoning": 3.00,
    },
    "claude-haiku-3-5": {
        "input": 0.80, "output": 4.00,
        "cache_read": 0.08, "cache_write": 1.00,
        "reasoning": 0.80,
    },
    # OpenAI
    "gpt-4o": {
        "input": 2.50, "output": 10.00,
        "cache_read": 1.25, "cache_write": 2.50,
        "reasoning": 2.50,
    },
    "gpt-4o-mini": {
        "input": 0.15, "output": 0.60,
        "cache_read": 0.075, "cache_write": 0.15,
        "reasoning": 0.15,
    },
    "o1": {
        "input": 15.00, "output": 60.00,
        "cache_read": 7.50, "cache_write": 15.00,
        "reasoning": 15.00,
    },
    "o3-mini": {
        "input": 1.10, "output": 4.40,
        "cache_read": 0.55, "cache_write": 1.10,
        "reasoning": 1.10,
    },
    # DeepSeek
    "deepseek-v3": {
        "input": 0.27, "output": 1.10,
        "cache_read": 0.07, "cache_write": 0.27,
        "reasoning": 0.27,
    },
    "deepseek-r1": {
        "input": 0.55, "output": 2.19,
        "cache_read": 0.14, "cache_write": 0.55,
        "reasoning": 0.55,
    },
    # xAI
    "grok-3": {
        "input": 3.00, "output": 15.00,
        "cache_read": 0.75, "cache_write": 3.00,
        "reasoning": 3.00,
    },
    "grok-3-mini-fast": {
        "input": 0.30, "output": 0.50,
        "cache_read": 0.075, "cache_write": 0.30,
        "reasoning": 0.30,
    },
    # Google
    "gemini-2.5-pro": {
        "input": 1.25, "output": 10.00,
        "cache_read": 0.31, "cache_write": 4.50,
        "reasoning": 1.25,
    },
}

# Default pricing for unknown models (Claude Opus rates)
DEFAULT_PRICING = MODEL_PRICING["claude-opus-4-6"]


def _get_pricing(model: str | None) -> dict:
    if not model:
        return DEFAULT_PRICING
    # Try exact match first
    if model in MODEL_PRICING:
        return MODEL_PRICING[model]
    # Try partial match (e.g. "claude-opus-4-6-20250514")
    for key, pricing in MODEL_PRICING.items():
        if model.startswith(key):
            return pricing
    return DEFAULT_PRICING


def _calc_session_cost(session: dict, pricing: dict) -> dict:
    """Calculate cost breakdown for a single session."""
    in_tok = session.get("input_tokens", 0)
    out_tok = session.get("output_tokens", 0)
    cache_r = session.get("cache_read_tokens", 0)
    cache_w = session.get("cache_write_tokens", 0)
    reasoning = session.get("reasoning_tokens", 0)

    in_cost = (in_tok / 1_000_000) * pricing["input"]
    out_cost = (out_tok / 1_000_000) * pricing["output"]
    cache_r_cost = (cache_r / 1_000_000) * pricing["cache_read"]
    cache_w_cost = (cache_w / 1_000_000) * pricing["cache_write"]
    reasoning_cost = (reasoning / 1_000_000) * pricing["reasoning"]

    total = in_cost + out_cost + cache_r_cost + cache_w_cost + reasoning_cost

    return {
        "input_cost": round(in_cost, 4),
        "output_cost": round(out_cost, 4),
        "cache_read_cost": round(cache_r_cost, 4),
        "cache_write_cost": round(cache_w_cost, 4),
        "reasoning_cost": round(reasoning_cost, 4),
        "total_cost": round(total, 4),
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "cache_read_tokens": cache_r,
        "cache_write_tokens": cache_w,
        "reasoning_tokens": reasoning,
    }


@router.get("/token-costs")
async def get_token_costs():
    """Token usage and estimated costs."""
    sessions_state = collect_sessions()
    config = collect_config()
    pricing = _get_pricing(config.model)
    today = datetime.now().strftime("%Y-%m-%d")

    # All-time totals
    all_input = 0
    all_output = 0
    all_cache_r = 0
    all_cache_w = 0
    all_reasoning = 0
    all_cost = 0.0
    all_messages = 0
    all_tool_calls = 0

    # Today's totals
    today_input = 0
    today_output = 0
    today_cache_r = 0
    today_cache_w = 0
    today_reasoning = 0
    today_cost = 0.0
    today_messages = 0
    today_session_count = 0

    # Daily cost trend (last 30 days)
    daily_costs: dict[str, float] = {}
    daily_tokens: dict[str, int] = {}
    daily_sessions: dict[str, int] = {}

    for sess in sessions_state.sessions:
        is_today = sess.started_at.strftime("%Y-%m-%d") == today
        day = sess.started_at.strftime("%Y-%m-%d")

        in_tok = sess.input_tokens
        out_tok = sess.output_tokens
        cache_r = sess.cache_read_tokens
        cache_w = sess.cache_write_tokens
        reasoning = sess.reasoning_tokens

        session_cost = (
            (in_tok / 1_000_000) * pricing["input"]
            + (out_tok / 1_000_000) * pricing["output"]
            + (cache_r / 1_000_000) * pricing["cache_read"]
            + (cache_w / 1_000_000) * pricing["cache_write"]
            + (reasoning / 1_000_000) * pricing["reasoning"]
        )

        all_input += in_tok
        all_output += out_tok
        all_cache_r += cache_r
        all_cache_w += cache_w
        all_reasoning += reasoning
        all_cost += session_cost
        all_messages += sess.message_count
        all_tool_calls += sess.tool_call_count

        if is_today:
            today_input += in_tok
            today_output += out_tok
            today_cache_r += cache_r
            today_cache_w += cache_w
            today_reasoning += reasoning
            today_cost += session_cost
            today_messages += sess.message_count
            today_session_count += 1

        daily_costs[day] = daily_costs.get(day, 0) + session_cost
        daily_tokens[day] = daily_tokens.get(day, 0) + in_tok + out_tok
        daily_sessions[day] = daily_sessions.get(day, 0) + 1

    # Sort daily trend
    sorted_days = sorted(daily_costs.keys())

    return {
        "model": config.model,
        "provider": config.provider,
        "pricing": pricing,
        "today": {
            "date": today,
            "session_count": today_session_count,
            "message_count": today_messages,
            "input_tokens": today_input,
            "output_tokens": today_output,
            "cache_read_tokens": today_cache_r,
            "cache_write_tokens": today_cache_w,
            "reasoning_tokens": today_reasoning,
            "total_tokens": today_input + today_output,
            "estimated_cost_usd": round(today_cost, 2),
        },
        "all_time": {
            "session_count": sessions_state.total_sessions,
            "message_count": all_messages,
            "tool_call_count": all_tool_calls,
            "input_tokens": all_input,
            "output_tokens": all_output,
            "cache_read_tokens": all_cache_r,
            "cache_write_tokens": all_cache_w,
            "reasoning_tokens": all_reasoning,
            "total_tokens": all_input + all_output,
            "estimated_cost_usd": round(all_cost, 2),
        },
        "cost_breakdown": {
            "input": round((all_input / 1_000_000) * pricing["input"], 2),
            "output": round((all_output / 1_000_000) * pricing["output"], 2),
            "cache_read": round((all_cache_r / 1_000_000) * pricing["cache_read"], 2),
            "cache_write": round((all_cache_w / 1_000_000) * pricing["cache_write"], 2),
            "reasoning": round((all_reasoning / 1_000_000) * pricing["reasoning"], 2),
        },
        "daily_trend": [
            {
                "date": day,
                "cost": round(daily_costs[day], 2),
                "tokens": daily_tokens[day],
                "sessions": daily_sessions[day],
            }
            for day in sorted_days
        ],
    }
