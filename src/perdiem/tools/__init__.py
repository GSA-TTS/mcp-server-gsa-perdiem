from perdiem.tools.rates_by_city import register_rates_by_city
from perdiem.tools.rates_by_state import register_rates_by_state
from perdiem.tools.rates_by_zip import register_rates_by_zip
from perdiem.tools.conus_lodging import register_conus_lodging
from perdiem.tools.mie_rates import register_mie_rates
from perdiem.tools.zip_code_mapping import register_zip_code_mapping


def register_tools(mcp) -> None:
    register_rates_by_city(mcp)
    register_rates_by_state(mcp)
    register_rates_by_zip(mcp)
    register_conus_lodging(mcp)
    register_mie_rates(mcp)
    register_zip_code_mapping(mcp)
