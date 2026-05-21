import os

from dotenv import load_dotenv
from fastmcp import FastMCP

from perdiem.tools import register_tools

load_dotenv()

mcp = FastMCP(
    "perdiem_mcp",
    instructions=(
        "This server provides access to official US federal government per diem rates "
        "from the GSA Per Diem API (https://open.gsa.gov/api/perdiem/). Per diem rates "
        "set the maximum lodging and Meals & Incidental Expenses (M&IE) reimbursements "
        "for federal employees traveling within the continental United States (CONUS).\n\n"
        "FISCAL YEAR CONVENTION: GSA fiscal years run October 1 – September 30. "
        "FY2024 covers October 2023 through September 2024. Always clarify which fiscal "
        "year applies when answering travel questions.\n\n"
        "TOOL SELECTION GUIDE:\n"
        "- Known city + state → perdiem_get_rates_by_city\n"
        "- Only have a ZIP code → perdiem_get_rates_by_zip\n"
        "- Browse or compare destinations within a state → perdiem_get_rates_by_state\n"
        "- M&IE meal/incidental breakdown or first/last day rate → perdiem_get_mie_rates\n"
        "- Full CONUS rate table → perdiem_get_conus_lodging_rates (paginated)\n"
        "- Look up which GSA destination a ZIP belongs to → perdiem_get_zip_code_mapping\n\n"
        "LODGING RATES: Non-Standard Areas (NSAs) have seasonal rates that vary by month. "
        "Always report the specific month's rate when answering lodging questions, not an average.\n\n"
        "M&IE: The daily M&IE rate is fixed per destination. On the first and last day of "
        "travel, only 75% of the M&IE rate may be claimed. Use perdiem_get_mie_rates to get "
        "the exact breakfast/lunch/dinner/incidental breakdown for any total rate.\n\n"
        "STANDARD RATE: Destinations not individually listed use the CONUS standard rate "
        "(currently $107 lodging / $59 M&IE). If a city lookup returns no results, the "
        "standard rate applies.\n\n"
        "AUTHENTICATION: Requires PERDIEM_API_KEY environment variable. Rate limit is "
        "1,000 requests per hour."
    ),
)

register_tools(mcp)

if __name__ == "__main__":
    # When run directly, check for a platform port env var.
    # If found, start an HTTP server (useful for Databricks local testing).
    # Otherwise fall back to stdio for local MCP clients (Claude Desktop, etc.).
    port_env = os.getenv("DATABRICKS_APP_PORT") or os.getenv("PORT")
    if port_env:
        mcp.run(transport="http", host="0.0.0.0", port=int(port_env))
    else:
        mcp.run(transport="stdio")
