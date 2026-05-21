import json
import os
import re
from typing import Any

import httpx

API_BASE_URL = "https://api.gsa.gov/travel/perdiem/v2"
CHARACTER_LIMIT = 25000

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_KEYS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def get_api_key() -> str:
    key = os.environ.get("PERDIEM_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "PERDIEM_API_KEY environment variable is not set. "
            "Register for a free key at https://open.gsa.gov/api/perdiem/ and set PERDIEM_API_KEY."
        )
    return key


async def make_api_request(path: str) -> Any:
    api_key = get_api_key()
    url = f"{API_BASE_URL}{path}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers={"x-api-key": api_key})
        response.raise_for_status()
        return response.json()


def handle_api_error(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 400:
            return (
                "Error: Bad request — check that city, state, ZIP, and year are valid. "
                "City names should not contain special characters (remove periods, apostrophes, hyphens)."
            )
        if status == 403:
            return (
                "Error: Invalid or missing API key. "
                "Set the PERDIEM_API_KEY environment variable with a valid key from https://open.gsa.gov/api/perdiem/"
            )
        if status == 404:
            return (
                "Error: No per diem rates found for the requested location/year. "
                "Try a nearby city or use perdiem_get_rates_by_state to browse available destinations."
            )
        if status == 429:
            return "Error: Rate limit exceeded (1,000 requests/hour). Please wait before making more requests."
        return f"Error: API request failed with status {status}."
    if isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. Please try again."
    if isinstance(e, ValueError):
        return f"Error: {e}"
    return f"Error: Unexpected error — {type(e).__name__}: {e}"


def sanitize_city(city: str) -> str:
    """Remove or replace characters the API cannot handle."""
    cleaned = re.sub(r"[.\'\-]", " ", city)
    cleaned = re.sub(r"\s+", "%20", cleaned.strip())
    return cleaned


def parse_rates_response(data: Any) -> list[dict[str, Any]]:
    """Normalize the nested city/state/zip response into a flat list of rate entries.

    The city/state/zip endpoints return a nested structure:
      {"rates": [{"state": "CA", "year": 2024, "rate": [{"city": ..., "meals": ...,
                  "months": {"month": [{"value": 333, "short": "Jan"}, ...]}}]}]}

    This function flattens it into a list of dicts with keys:
      city, state, county, year, meals, Jan, Feb, ..., Dec
    """
    if not isinstance(data, dict) or "rates" not in data:
        return []

    results = []
    for rates_entry in data.get("rates") or []:
        state = rates_entry.get("state", "")
        year = rates_entry.get("year", "")
        for rate in rates_entry.get("rate") or []:
            entry: dict[str, Any] = {
                "city": rate.get("city", ""),
                "state": state,
                "county": rate.get("county", ""),
                "year": year,
                "meals": rate.get("meals", ""),
                "standardRate": rate.get("standardRate", ""),
            }
            months = (rate.get("months") or {}).get("month") or []
            for m in months:
                short = m.get("short", "")
                value = m.get("value")
                if short:
                    entry[short] = value
            results.append(entry)
    return results


def format_monthly_lodging(entry: dict[str, Any]) -> str:
    """Format a single destination's monthly lodging rates as a markdown table.

    Handles both the flat CONUS format (keys: City, State, County, Meals, Jan..Dec)
    and the normalized nested format (keys: city, state, county, meals, Jan..Dec).
    """
    lines = []
    city = entry.get("City", entry.get("city", ""))
    state = entry.get("State", entry.get("state", ""))
    county = entry.get("County", entry.get("county", ""))
    meals = entry.get("Meals", entry.get("meals", ""))
    year = entry.get("Year", entry.get("year", ""))

    lines.append(f"**Location:** {city}, {state} ({county} County)  ")
    if year:
        lines.append(f"**Fiscal Year:** {year}  ")
    lines.append(f"**M&IE Rate:** ${meals}/day  ")
    lines.append("")
    lines.append("| Month | Lodging Rate |")
    lines.append("|-------|-------------|")
    for month in MONTH_KEYS:
        rate = entry.get(month)
        if rate is not None:
            lines.append(f"| {month} | ${rate} |")
    return "\n".join(lines)


def paginate(items: list[Any], limit: int, offset: int) -> tuple[list[Any], bool, int | None]:
    """Return a page of items and pagination metadata."""
    total = len(items)
    page = items[offset : offset + limit]
    has_more = total > offset + len(page)
    next_offset = offset + len(page) if has_more else None
    return page, has_more, next_offset


def build_pagination_envelope(
    items: list[Any], total: int, limit: int, offset: int, has_more: bool, next_offset: int | None
) -> dict[str, Any]:
    return {
        "total": total,
        "count": len(items),
        "offset": offset,
        "has_more": has_more,
        **({"next_offset": next_offset} if next_offset is not None else {}),
        "items": items,
    }


def truncate_if_needed(text: str, context: str = "") -> str:
    if len(text) <= CHARACTER_LIMIT:
        return text
    truncated = text[:CHARACTER_LIMIT]
    note = (
        f"\n\n[Response truncated at {CHARACTER_LIMIT} characters. "
        f"Use the 'offset' parameter to see more results{f' ({context})' if context else ''}.]"
    )
    return truncated + note