import json
from typing import Annotated
from fastmcp import FastMCP
from pydantic import Field
from perdiem.models import ResponseFormat
from perdiem.utils import handle_api_error, make_api_request, sanitize_city, format_monthly_lodging, parse_rates_response


def register_rates_by_city(mcp: FastMCP) -> None:
    @mcp.tool(
        name="perdiem_get_rates_by_city",
        annotations={
            "title": "Get Per Diem Rates by City",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def perdiem_get_rates_by_city(
        city: Annotated[str, Field(description="Destination city name (e.g., 'San Francisco', 'New York'). Special characters are handled automatically.", min_length=1, max_length=100)],
        state: Annotated[str, Field(description="Two-letter state abbreviation (e.g., 'CA', 'TX')", min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$")],
        year: Annotated[int, Field(description="Federal fiscal year (e.g., 2024 covers Oct 2023 – Sep 2024). Up to 3 years available.", ge=2010, le=2035)],
        response_format: Annotated[ResponseFormat, Field(description="Output format: 'markdown' for human-readable or 'json' for machine-readable")] = ResponseFormat.MARKDOWN,
    ) -> str:
        """Get federal per diem lodging and M&IE rates for a specific city and fiscal year.

        Returns monthly lodging rates and daily M&IE rate for the destination.
        If the city is not found, try perdiem_get_rates_by_state to browse available
        destinations or perdiem_get_rates_by_zip with a specific ZIP code.

        Use when: "What is the per diem rate for Chicago, IL in FY2024?"
        Use when: "How much can I claim for lodging in Seattle in October 2023?"
        Don't use when: You have a ZIP code (use perdiem_get_rates_by_zip instead).
        Don't use when: You want all cities in a state (use perdiem_get_rates_by_state).
        """
        try:
            city_param = sanitize_city(city)
            path = f"/rates/city/{city_param}/state/{state.upper()}/year/{year}"
            data = await make_api_request(path)
            entries = parse_rates_response(data)

            if not entries:
                return (
                    f"No per diem rates found for {city}, {state.upper()} in FY{year}. "
                    "Try perdiem_get_rates_by_state to see available destinations in that state, "
                    "or perdiem_get_rates_by_zip with a specific ZIP code."
                )

            entry = entries[0]

            if response_format == ResponseFormat.JSON:
                return json.dumps(entry, indent=2)

            lines = [f"# Per Diem Rates: {city}, {state.upper()} — FY{year}", ""]
            lines.append(format_monthly_lodging(entry))
            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)
