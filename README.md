# Partle Marketplace MCP Server

A remote [Model Context Protocol](https://modelcontextprotocol.io/) server for the Partle local marketplace — find products in physical stores near you.

**Server URL:** `https://partle.rubenayla.xyz/mcp/`

**Transport:** Streamable HTTP

## What is Partle?

Partle helps you find specific products in physical stores near you. Instead of waiting for online delivery, find what you need at a local store today. Currently focused on hardware stores in Spain (~2400 products, ~4000 stores).

## Tools

### Read (no auth required)

| Tool | Description | Parameters |
|------|-------------|------------|
| `search_products` | Search products by name or description | `query` (required), `min_price`, `max_price`, `tags`, `sort_by`, `limit` |
| `get_product` | Get product details by ID | `product_id` |
| `search_stores` | Search or list stores | `query`, `limit` |
| `get_store` | Get store details by ID | `store_id` |
| `get_stats` | Platform statistics | (none) |

### Write (API key required)

Generate an API key at [partle.rubenayla.xyz/account](https://partle.rubenayla.xyz/account).

| Tool | Description | Parameters |
|------|-------------|------------|
| `create_product` | Create a new product listing | `api_key`, `name`, `description`, `price`, `currency`, `url`, `store_id` |
| `upload_product_image` | Upload an image for a product (base64 or URL) | `api_key`, `product_id`, `image_base64`, `content_type`, `image_url` |

## Configuration

### Claude Code / Claude Desktop

Add to your MCP settings:

```json
{
  "mcpServers": {
    "partle": {
      "url": "https://partle.rubenayla.xyz/mcp/"
    }
  }
}
```

### Discovery

MCP discovery file: `https://partle.rubenayla.xyz/.well-known/mcp.json`

## Public REST API

No-auth REST endpoints are also available:

- `GET /v1/public/products?q=cerrojo&limit=10` — search products
- `GET /v1/public/stores?limit=10` — list stores
- `GET /v1/public/stats` — platform statistics
- `GET /openapi.json` — full OpenAPI spec

Base URL: `https://partle.rubenayla.xyz`

Rate limit: 100 requests/hour per IP.

## Example

Ask an AI agent: "Where can I buy a cerrojo FAC lock near me?"

The agent calls `search_products(query="cerrojo FAC")` and gets back product details with store names, addresses, and prices.
