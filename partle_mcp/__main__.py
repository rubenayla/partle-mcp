"""Entry point: `python -m partle_mcp` runs the MCP server in stdio mode."""

from partle_mcp.server import mcp


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
