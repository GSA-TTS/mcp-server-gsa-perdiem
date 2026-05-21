import json
from typing import Annotated
from fastmcp import FastMCP
from pydantic import Field
from perdiem.models import ResponseFormat
from perdiem.utils import handle_api_error, make_api_request


def register_mie_rates(mcp: FastMCP) -> None:
    @mcp.tool(
        name="perdiem_get_mie_rates",
        annotations={
            "title": "Get M&IE Breakdown Rates",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def perdiem_get_mie_rates(
        year: Annotated[int, Field(description="Federal fiscal year", ge=2010, le=2035)],
        response_format: Annotated[ResponseFormat, Field(description="Output format: 'markdown' for human-readable or 'json' for machine-readable")] = ResponseFormat.MARKDOWN,
    ) -> str:
        """Get federal Meals & Incidental Expenses (M&IE) breakdown rates for a fiscal year.

        Returns M&IE rate tiers showing how each total daily rate is split among breakfast,
        lunch, dinner, and incidentals, plus the first/last travel day rate (typically 75%
        of the full daily rate). These tiers apply across all CONUS destinations.

        Use when: "What is the per diem meal breakdown for a $79 M&IE rate?"
        Use when: "How much can I claim for lunch on a federal trip?"
        Use when: "What is the first/last day M&IE rate for a $59 destination?"
        Don't use when: You need lodging rates (use perdiem_get_rates_by_city).
        """
        try:
            path = f"/rates/conus/mie/{year}"
            data = await make_api_request(path)

            if not data:
                return f"No M&IE rate data found for FY{year}."

            rates = data if isinstance(data, list) else [data]

            if response_format == ResponseFormat.JSON:
                return json.dumps(rates, indent=2)

            lines = [f"# Federal M&IE Breakdown Rates — FY{year}", ""]
            lines.append(
                "| Total | Breakfast | Lunch | Dinner | Incidentals | First/Last Day |"
            )
            lines.append("|-------|-----------|-------|--------|-------------|----------------|")
            for tier in rates:
                total = tier.get("total", tier.get("Total", ""))
                breakfast = tier.get("breakfast", tier.get("Breakfast", ""))
                lunch = tier.get("lunch", tier.get("Lunch", ""))
                dinner = tier.get("dinner", tier.get("Dinner", ""))
                incidental = tier.get("incidental", tier.get("Incidental", ""))
                first_last = tier.get("FirstLastDay", tier.get("firstLastDay", ""))
                lines.append(
                    f"| ${total} | ${breakfast} | ${lunch} | ${dinner} | ${incidental} | ${first_last} |"
                )

            lines.append("")
            lines.append(
                "*First/last day rate applies when you depart or return on a travel day. "
                "Typically 75% of the full daily rate.*"
            )
            return "\n".join(lines)

        except Exception as e:
            return handle_api_error(e)
