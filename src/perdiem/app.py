from dotenv import load_dotenv

from fastmcp import FastMCP

from typing import Annotated
from pydantic import Field 

from perdiem.utils import handle_api_error, sanitize_city, make_api_request, parse_rates_response, format_monthly_lodging, handle_api_error

load_dotenv()

mcp = FastMCP("perdiem_mcp")

@mcp.tool()
async def perdiem_get_rates_by_city(
    city: Annotated[str, Field(description="The name of the city to get per diem rates for.")],
    state: Annotated[str, Field(description="The two letter abbreviation of the state (e.g. MA or VA) to get perdiem rates for.")],
    year: Annotated[int, Field(description="The fiscal year to get per diem rates for.")],
) -> str:
    """
    Get perdiem rates for a given city, state, and year.
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

        lines = [f"# Per Diem Rates: {city}, {state.upper()} — FY{year}", ""]
        lines.append(format_monthly_lodging(entry))
        return "\n".join(lines)
    
    except Exception as e:
        return handle_api_error(e)

if __name__ == "__main__":
    mcp.run(transport='stdio')