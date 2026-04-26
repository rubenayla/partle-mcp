# Partle Marketplace MCP Server

[Model Context Protocol](https://modelcontextprotocol.io/) server for the Partle local marketplace — find products in physical stores near you, ask an AI to add a listing for you, all without leaving your assistant.

**130,000+ products** across **~16,000 stores**. Reads need no auth. Writes need a `pk_…` API key.

## Two ways to run it

### Remote (recommended — zero setup)

Point your MCP client at:

```
https://partle.rubenayla.xyz/mcp/
```

That's it. Streamable HTTP transport, MCP spec 2025-06-18. Per-client install instructions: [`/documentation/mcp-setup/`](https://partle.rubenayla.xyz/documentation/mcp-setup/).

### Local stdio (for clients that prefer installable servers, or for Glama / Smithery scoring)

```bash
pip install partle-mcp
partle-mcp
```

Or with `uvx` (no install):

```bash
uvx partle-mcp
```

Or with Docker:

```bash
docker run --rm -i ghcr.io/rubenayla/partle-mcp
```

The stdio package proxies to the public REST API at `https://partle.rubenayla.xyz`, so you don't need a database or local backend.

#### Claude Desktop / Claude Code (stdio)

```json
{
  "mcpServers": {
    "partle": {
      "command": "uvx",
      "args": ["partle-mcp"]
    }
  }
}
```

## Tools (12 total)

### Read (no auth)

| Tool | Purpose |
|------|---------|
| `search_products` | Search the catalog by name, price range, tags, store. Supports cross-language semantic search. |
| `get_product` | Full record for one product by ID. |
| `search_stores` | Search/list stores by name or address. |
| `get_store` | Full record for one store by ID. |
| `get_stats` | Platform-wide totals. |

### Write (API key)

Generate a key at [partle.rubenayla.xyz/account](https://partle.rubenayla.xyz/account). Keys start with `pk_`.

| Tool | Purpose |
|------|---------|
| `create_product` | Add a new listing. |
| `update_product` | Edit a listing you own. |
| `delete_product` | Remove a listing you own. |
| `upload_product_image` | Attach an image (base64 or URL). |
| `delete_product_image` | Remove an image from a product. |
| `get_my_products` | List products you've created. |

### Feedback

| Tool | Purpose |
|------|---------|
| `submit_feedback` | Send freeform feedback about your integration experience. |

## Public REST API

Same data, also reachable as plain HTTP for clients without MCP support:

- `GET /v1/public/products?q=cerrojo&limit=10` — search products
- `GET /v1/public/stores?q=Madrid&limit=10` — search stores
- `GET /v1/public/stats` — platform totals
- `POST /v1/public/feedback` — submit feedback

Base URL: `https://partle.rubenayla.xyz`. Rate-limited to 100 req/hour per IP.

Full docs: [`/documentation/`](https://partle.rubenayla.xyz/documentation/) · OpenAPI: [`/openapi.json`](https://partle.rubenayla.xyz/openapi.json) · Discovery: [`/.well-known/mcp.json`](https://partle.rubenayla.xyz/.well-known/mcp.json).

## Example

> **You:** "Use Partle to find a drill under €50."
>
> **Claude:** *(calls `search_products(query="drill", max_price=50)`)*
>
> Returns Blackspur 13pc High Speed Drill Bit Set at €4.99 (Lenehans, IE), Flotec Drill Pump 225 GPH at €17.14 (Kooyman Megastore, NL), and a few more — each with a `partle_url` to view the listing.

More examples in the [setup guide](https://partle.rubenayla.xyz/documentation/mcp-setup/#example-queries).

## License

MIT — see [LICENSE](LICENSE).
