import json
from typing import Annotated
from fastmcp import FastMCP
from pydantic import Field
from perdiem.models import ResponseFormat
from perdiem.utils import handle_api_error, make_api_request, format_monthly_lodging, parse_rates_response


def register_rates_by_zip(mcp: FastMCP) -> None:
    @mcp.tool(
        name="perdiem_get_rates_by_zip",
        annotations={
            "title": "Get Per Diem Rates by ZIP Code",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def perdiem_get_rates_by_zip(
        zip_code: Annotated[str, Field(description="5-digit ZIP code of the destination (e.g., '94102')", pattern=r"^\d{5}$")],
        year: Annotated[int, Field(description="Federal fiscal year", ge=2010, le=2035)],
        response_format: Annotated[ResponseFormat, Field(description="Output format: 'markdown' for human-readable or 'json' for machine-readable")] = ResponseFormat.MARKDOWN,
    ) -> str:
        """Get federal per diem lodging and M&IE rates for a destination by ZIP code.

        Returns monthly lodging rates and daily M&IE for the GSA destination associated
        with the ZIP code. Useful when you know the ZIP code but not the exact GSA city name.

        Use when: "What is the per diem rate for ZIP code 10001 in FY2024?"
        Use when: You have a hotel ZIP code and need to verify the per diem allowance.
        Don't use when: You know the city name (use perdiem_get_rates_by_city — faster).
        """
        try:
            path = f"/rates/zip/{zip_code}/year/{year}"
            data = await make_api_request(path)
            entries = parse_rates_response(data)

            if not entries:
                return (
                    f"No per diem rates found for ZIP code {zip_code} in FY{year}. "
                    "This ZIP may not map to a GSA designated destination. "
                    "Try perdiem_get_zip_code_mapping to check available ZIP codes, "
                    "or use perdiem_get_rates_by_city with the nearest major city."
                )

            entry = entries[0]

            if response_format == ResponseFormat.JSON:
                return json.dumps(entry, indent=2)

            city = entry.get("City", entry.get("city", ""))
            state = entry.get("State", entry.get("state", ""))
            lines = [f"# Per Diem Rates: ZIP {zip_code} ({city}, {state}) — FY{year}", ""]
            lines.append(format_monthly_lodging(entry))
            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)
