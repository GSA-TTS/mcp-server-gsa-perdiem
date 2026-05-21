import json
from typing import Annotated, Optional
from fastmcp import FastMCP
from pydantic import Field
from perdiem.models import ResponseFormat
from perdiem.utils import (
    handle_api_error,
    make_api_request,
    format_monthly_lodging,
    parse_rates_response,
    paginate,
    build_pagination_envelope,
    truncate_if_needed,
)


def register_rates_by_state(mcp: FastMCP) -> None:
    @mcp.tool(
        name="perdiem_get_rates_by_state",
        annotations={
            "title": "Get Per Diem Rates by State",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def perdiem_get_rates_by_state(
        state: Annotated[str, Field(description="Two-letter state abbreviation (e.g., 'CA', 'TX')", min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$")],
        year: Annotated[int, Field(description="Federal fiscal year", ge=2010, le=2035)],
        limit: Annotated[Optional[int], Field(description="Maximum destinations to return, 1–200 (default: 50)", ge=1, le=200)] = 50,
        offset: Annotated[Optional[int], Field(description="Number of destinations to skip for pagination (default: 0)", ge=0)] = 0,
        response_format: Annotated[ResponseFormat, Field(description="Output format: 'markdown' for human-readable or 'json' for machine-readable")] = ResponseFormat.MARKDOWN,
    ) -> str:
        """Get all federal per diem destinations and rates for an entire state and fiscal year.

        Returns a paginated list of all city/county destinations in the state with monthly
        lodging rates and daily M&IE rates. Useful for browsing available destinations,
        finding the highest-rate cities, or checking if a city is in the GSA database.

        Use when: "List all per diem destinations in California for FY2024".
        Use when: "Which cities in Texas have the highest lodging rates?"
        Use when: "Is Austin, TX a designated per diem city for FY2023?"
        Don't use when: You want a single city (use perdiem_get_rates_by_city — faster).
        """
        try:
            path = f"/rates/state/{state.upper()}/year/{year}"
            data = await make_api_request(path)
            all_items = parse_rates_response(data)

            if not all_items:
                return (
                    f"No per diem destinations found for state {state.upper()} in FY{year}. "
                    "Verify the state abbreviation is correct."
                )
            effective_limit = limit or 50
            effective_offset = offset or 0
            page, has_more, next_offset = paginate(all_items, effective_limit, effective_offset)

            if not page:
                return f"No more destinations. Total destinations in {state.upper()}: {len(all_items)}."

            if response_format == ResponseFormat.JSON:
                envelope = build_pagination_envelope(
                    page, len(all_items), effective_limit, effective_offset, has_more, next_offset
                )
                result = json.dumps(envelope, indent=2)
                return truncate_if_needed(result, f"use offset={next_offset} for next page" if has_more else "")

            lines = [
                f"# Per Diem Destinations: {state.upper()} — FY{year}",
                f"Showing {len(page)} of {len(all_items)} destinations "
                f"(offset={effective_offset}, limit={effective_limit})",
                "",
            ]
            for entry in page:
                city = entry.get("City", entry.get("city", ""))
                county = entry.get("County", entry.get("county", ""))
                meals = entry.get("Meals", entry.get("meals", ""))
                lines.append(f"## {city} ({county} County)")
                lines.append(f"- **M&IE:** ${meals}/day")
                lines.append(format_monthly_lodging(entry))
                lines.append("")

            if has_more:
                lines.append(f"*More destinations available — use offset={next_offset} to continue.*")

            result = "\n".join(lines)
            return truncate_if_needed(result, f"use offset={next_offset} for next page" if has_more else "")

        except Exception as e:
            return handle_api_error(e)
