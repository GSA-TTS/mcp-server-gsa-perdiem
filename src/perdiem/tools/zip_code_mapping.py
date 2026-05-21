import json
from typing import Annotated, Optional
from fastmcp import FastMCP
from pydantic import Field
from perdiem.models import ResponseFormat
from perdiem.utils import (
    handle_api_error,
    make_api_request,
    paginate,
    build_pagination_envelope,
    truncate_if_needed,
)


def register_zip_code_mapping(mcp: FastMCP) -> None:
    @mcp.tool(
        name="perdiem_get_zip_code_mapping",
        annotations={
            "title": "Get ZIP Code to Destination ID Mapping",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def perdiem_get_zip_code_mapping(
        year: Annotated[int, Field(description="Federal fiscal year", ge=2010, le=2035)],
        limit: Annotated[Optional[int], Field(description="Maximum ZIP entries to return, 1–500 (default: 100)", ge=1, le=500)] = 100,
        offset: Annotated[Optional[int], Field(description="Number of entries to skip for pagination (default: 0)", ge=0)] = 0,
        response_format: Annotated[ResponseFormat, Field(description="Output format: 'markdown' for human-readable or 'json' for machine-readable")] = ResponseFormat.MARKDOWN,
    ) -> str:
        """Get the mapping of ZIP codes to GSA Destination IDs (DIDs) for a fiscal year.

        Returns a paginated list of ZIP codes and their corresponding GSA Destination IDs
        and state codes. DIDs are the internal GSA identifiers linking ZIP codes to per diem
        rate destinations. Useful for programmatic lookups or verifying which GSA destination
        covers a given ZIP code.

        Use when: "Which GSA destination ID covers ZIP code 90210?"
        Use when: Building a local lookup table of ZIP-to-per-diem-destination mappings.
        Don't use when: You want actual per diem rates (use perdiem_get_rates_by_zip).
        """
        try:
            path = f"/rates/conus/zipcodes/{year}"
            data = await make_api_request(path)

            if not data:
                return f"No ZIP code mapping data found for FY{year}."

            all_items = data if isinstance(data, list) else [data]
            effective_limit = limit or 100
            effective_offset = offset or 0
            page, has_more, next_offset = paginate(all_items, effective_limit, effective_offset)

            if not page:
                return f"No more entries. Total ZIP mappings: {len(all_items)}."

            if response_format == ResponseFormat.JSON:
                envelope = build_pagination_envelope(
                    page, len(all_items), effective_limit, effective_offset, has_more, next_offset
                )
                result = json.dumps(envelope, indent=2)
                return truncate_if_needed(result, f"use offset={next_offset} for next page" if has_more else "")

            lines = [
                f"# ZIP Code to GSA Destination ID Mapping — FY{year}",
                f"Showing {len(page)} of {len(all_items)} entries "
                f"(offset={effective_offset}, limit={effective_limit})",
                "",
                "| ZIP Code | Destination ID (DID) | State |",
                "|----------|----------------------|-------|",
            ]
            for entry in page:
                zip_code = entry.get("Zip", entry.get("zip", ""))
                did = entry.get("DID", entry.get("did", ""))
                state = entry.get("ST", entry.get("state", ""))
                lines.append(f"| {zip_code} | {did} | {state} |")

            if has_more:
                lines.append("")
                lines.append(f"*More entries available — use offset={next_offset} to continue.*")

            result = "\n".join(lines)
            return truncate_if_needed(result, f"use offset={next_offset} for next page" if has_more else "")

        except Exception as e:
            return handle_api_error(e)
