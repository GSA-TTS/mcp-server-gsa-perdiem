import json
from typing import Annotated, Optional
from fastmcp import FastMCP
from pydantic import Field
from perdiem.models import ResponseFormat
from perdiem.utils import (
    handle_api_error,
    make_api_request,
    format_monthly_lodging,
    paginate,
    build_pagination_envelope,
    truncate_if_needed,
)


def register_conus_lodging(mcp: FastMCP) -> None:
    @mcp.tool(
        name="perdiem_get_conus_lodging_rates",
        annotations={
            "title": "Get All CONUS Lodging Rates",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def perdiem_get_conus_lodging_rates(
        year: Annotated[int, Field(description="Federal fiscal year", ge=2010, le=2035)],
        limit: Annotated[Optional[int], Field(description="Maximum destinations to return, 1–200 (default: 50)", ge=1, le=200)] = 50,
        offset: Annotated[Optional[int], Field(description="Number of destinations to skip for pagination (default: 0)", ge=0)] = 0,
        response_format: Annotated[ResponseFormat, Field(description="Output format: 'markdown' for human-readable or 'json' for machine-readable")] = ResponseFormat.MARKDOWN,
    ) -> str:
        """Get federal per diem lodging rates for all CONUS (continental US) destinations.

        Returns a paginated list of all designated per diem destinations in the continental
        US with their monthly lodging rates, M&IE, and Destination IDs (DIDs). This is a
        large dataset — use limit/offset to page through, or use perdiem_get_rates_by_state
        for state-specific queries.

        Use when: "Show me the top per diem destinations for FY2024".
        Use when: Building a comprehensive lookup of all CONUS per diem rates.
        Don't use when: You want a single city or state (use the city/state tools — faster).
        """
        try:
            path = f"/rates/conus/lodging/{year}"
            data = await make_api_request(path)

            if not data:
                return f"No CONUS lodging rate data found for FY{year}."

            all_items = data if isinstance(data, list) else [data]
            effective_limit = limit or 50
            effective_offset = offset or 0
            page, has_more, next_offset = paginate(all_items, effective_limit, effective_offset)

            if not page:
                return f"No more destinations. Total CONUS destinations: {len(all_items)}."

            if response_format == ResponseFormat.JSON:
                envelope = build_pagination_envelope(
                    page, len(all_items), effective_limit, effective_offset, has_more, next_offset
                )
                result = json.dumps(envelope, indent=2)
                return truncate_if_needed(result, f"use offset={next_offset} for next page" if has_more else "")

            lines = [
                f"# CONUS Per Diem Lodging Rates — FY{year}",
                f"Showing {len(page)} of {len(all_items)} destinations "
                f"(offset={effective_offset}, limit={effective_limit})",
                "",
            ]
            for entry in page:
                city = entry.get("City", entry.get("city", ""))
                state = entry.get("State", entry.get("state", ""))
                did = entry.get("DID", entry.get("did", ""))
                lines.append(f"## {city}, {state}" + (f" (DID: {did})" if did else ""))
                lines.append(format_monthly_lodging(entry))
                lines.append("")

            if has_more:
                lines.append(f"*More destinations available — use offset={next_offset} to continue.*")

            result = "\n".join(lines)
            return truncate_if_needed(result, f"use offset={next_offset} for next page" if has_more else "")

        except Exception as e:
            return handle_api_error(e)
