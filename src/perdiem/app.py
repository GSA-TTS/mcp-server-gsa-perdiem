from fastmcp import FastMCP
from perdiem.tools import register_tools

mcp = FastMCP("perdiem_mcp")
register_tools(mcp)
