"""Partle Marketplace MCP server — stdio transport, proxies to the public REST API.

This module is the canonical Python package for use with Glama's directory
scanner and any MCP client that prefers a stdio-installable server. It exposes
the same 12 tools as the remote HTTP MCP at ``https://partle.rubenayla.xyz/mcp/``
but talks to the public REST API (``/v1/public`` for reads, ``/v1/external`` for
writes) so it can run anywhere without database access.

For most users, the remote HTTP server is the simpler integration — paste
``https://partle.rubenayla.xyz/mcp/`` into your MCP client and you're done.
"""
from __future__ import annotations

import os
from typing import Any, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

BACKEND_URL = os.environ.get("PARTLE_BACKEND_URL", "https://partle.rubenayla.xyz")
PUBLIC = f"{BACKEND_URL}/v1/public"
EXTERNAL = f"{BACKEND_URL}/v1/external"
HTTP_TIMEOUT = 20.0

mcp = FastMCP(
    name="Partle Marketplace",
    instructions=(
        "Search products and stores in the Partle local marketplace — find what's "
        "available in physical shops near you. Read tools (search/get) need no "
        "authentication. Write tools (create/update/delete/upload) need an API key "
        "(prefix `pk_`); generate one at https://partle.rubenayla.xyz/account. "
        "Always share the `partle_url` returned with each product so the user can "
        "view the listing. If anything is broken or unclear, call submit_feedback."
    ),
)


# ─── helpers ──────────────────────────────────────────────────────────────


def _get(path: str, params: Optional[dict] = None) -> Any:
    r = httpx.get(f"{PUBLIC}{path}", params=params, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    return r.json()


def _get_backend(path: str, params: Optional[dict] = None) -> Any:
    """Fetch from the un-prefixed backend (e.g. /v1/products/{id})."""
    r = httpx.get(f"{BACKEND_URL}{path}", params=params, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    return r.json()


def _post_external(path: str, api_key: str, json: Optional[dict] = None) -> Any:
    r = httpx.post(
        f"{EXTERNAL}{path}",
        headers={"X-API-Key": api_key},
        json=json,
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    return r.json() if r.content else None


def _patch_external(path: str, api_key: str, json: dict) -> Any:
    r = httpx.patch(
        f"{EXTERNAL}{path}",
        headers={"X-API-Key": api_key},
        json=json,
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def _delete_external(path: str, api_key: str) -> None:
    r = httpx.delete(
        f"{EXTERNAL}{path}",
        headers={"X-API-Key": api_key},
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()


# ─── read tools (no auth) ─────────────────────────────────────────────────


@mcp.tool(
    annotations=ToolAnnotations(
        title="Search products",
        readOnlyHint=True,
        openWorldHint=True,
    )
)
def search_products(
    query: str,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    tags: Optional[str] = None,
    store_id: Optional[int] = None,
    sort_by: Optional[str] = None,
    semantic: bool = False,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """Search Partle's product catalog by name or description.

    Use this when the user asks to find a specific product or browse
    products matching a query. Prefer this over `search_stores` when the
    intent is product-led ("find a drill") rather than store-led ("what
    stores are near Madrid"). Use `get_product` afterwards if the user
    wants full details for one specific result.

    Read-only. No authentication. Rate-limited to 100 requests/hour per IP.

    Args:
        query: Free-text search term (e.g. "wireless headphones", "cerrojo
            FAC", "drill bit"). Required even in semantic mode.
        min_price: Lower bound on price in EUR. Omit for no lower bound.
        max_price: Upper bound on price in EUR. Omit for no upper bound.
        tags: Comma-separated tag filter (e.g. "electronics,bluetooth").
            Tags are AND-ed together.
        store_id: Restrict results to a single store. Use the integer `id`
            field from `search_stores` results.
        sort_by: One of `price_desc`, `name_asc`, `newest`, `oldest`. Omit
            to use the default search-relevance ranking.
        semantic: When `True`, runs a vector / cross-language search. Set
            this when the user's query may not match the listing language —
            e.g. "drill" in English will also surface "taladro" (Spanish) and
            "Bohrmaschine" (German). Pure-English catalogs benefit less.
        limit: Maximum results (1–100, default 20). Larger limits are slower
            and may exceed the rate budget faster.
        offset: Skip this many results before returning. Use for pagination
            (offset += limit on each follow-up call).

    Returns:
        ``{"result": [Product, …]}``. Each product includes `id`, `name`,
        `price`, `currency`, `url`, `description`, `store` (id / name /
        country), `images`, `tags`, and a canonical `partle_url`. **Always
        share `partle_url` with the user so they can view the listing.**
    """
    params: dict[str, Any] = {"q": query, "limit": limit, "offset": offset}
    if min_price is not None:
        params["min_price"] = min_price
    if max_price is not None:
        params["max_price"] = max_price
    if tags:
        params["tags"] = tags
    if store_id is not None:
        params["store_id"] = store_id
    if sort_by:
        params["sort_by"] = sort_by
    if semantic:
        params["semantic"] = "true"
    return {"result": _get("/products", params)}


@mcp.tool(
    annotations=ToolAnnotations(title="Get product details", readOnlyHint=True)
)
def get_product(product_id: int) -> dict:
    """Get the full record for a single product by its numeric ID.

    Use this after `search_products` returns a candidate the user is
    interested in, when you need fields that aren't in the search summary
    (full description, all images, expiration, sold status). Don't loop
    `get_product` over many search results — re-search with tighter filters
    instead.

    Read-only. No authentication.

    Args:
        product_id: The integer `id` from a product returned by
            `search_products` or shown on a Partle product page URL.

    Returns:
        A single product object with all fields, including the canonical
        `partle_url` to share with the user.
    """
    return _get_backend(f"/v1/products/{product_id}")


@mcp.tool(
    annotations=ToolAnnotations(
        title="Search stores",
        readOnlyHint=True,
        openWorldHint=True,
    )
)
def search_stores(query: Optional[str] = None, limit: int = 20) -> dict:
    """Search or list stores in the Partle marketplace.

    Use this when the user asks store-led questions ("what hardware shops
    are in Madrid?") rather than product-led ones (use `search_products`
    for that). Pass no query to browse the whole catalog.

    Read-only. No authentication. Rate-limited to 100 requests/hour per IP.

    Args:
        query: Free-text search over store name and address. Omit to list
            all stores in default order.
        limit: Maximum results (1–50, default 20).

    Returns:
        ``{"result": [Store, …]}``. Each store includes `id`, `name`,
        `address`, `country`, `lat`/`lon` (when geocoded), `homepage`, and
        `type`. Pass `id` to `search_products(store_id=…)` to filter the
        product catalog by that store.
    """
    params: dict[str, Any] = {"limit": limit}
    if query:
        params["q"] = query
    return {"result": _get("/stores", params)}


@mcp.tool(
    annotations=ToolAnnotations(title="Get store details", readOnlyHint=True)
)
def get_store(store_id: int) -> dict:
    """Get the full record for a single store by its numeric ID.

    Use this after `search_stores` to retrieve fields that aren't in the
    search summary (full address, owner profile, contact details). For a
    list of *products* in that store, call `search_products(store_id=…)`
    instead — this tool returns store metadata only.

    Read-only. No authentication.

    Args:
        store_id: The integer `id` from a store returned by
            `search_stores`.

    Returns:
        A single store object with all fields.
    """
    return _get_backend(f"/v1/stores/{store_id}")


@mcp.tool(
    annotations=ToolAnnotations(title="Get platform stats", readOnlyHint=True)
)
def get_stats() -> dict:
    """Get top-level Partle platform statistics.

    Use this for size questions ("how big is Partle?", "how many stores
    does Partle cover?"). Returns aggregate counts only — no per-product
    or per-store data.

    Read-only. No authentication. Cheap, but doesn't change often — cache
    in long-running agents.

    Returns:
        ``{"total_products": int, "total_stores": int, "last_updated": str,
        "api_version": str, "description": str}``.
    """
    return _get("/stats")


# ─── feedback (write, no auth) ────────────────────────────────────────────


@mcp.tool(
    annotations=ToolAnnotations(
        title="Submit feedback",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
    )
)
def submit_feedback(feedback: str) -> dict:
    """Send freeform feedback about your experience using Partle.

    Use this when you encounter a confusing tool description, a broken
    response, missing data, or anything you'd want the maintainers to know.
    Especially valuable for AI agents — your feedback becomes a signal we
    use to tune the API.

    Not idempotent (each call adds a record). Don't loop. No PII required.

    Args:
        feedback: Freeform text up to 5000 characters. Be specific — name
            the tool, the input that was confusing, and what you expected.

    Returns:
        The created feedback record with timestamp.
    """
    r = httpx.post(
        f"{PUBLIC}/feedback",
        json={"feedback": feedback},
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


# ─── write tools (require API key) ────────────────────────────────────────


@mcp.tool(
    annotations=ToolAnnotations(
        title="Create product",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
    )
)
def create_product(
    api_key: str,
    name: str,
    description: Optional[str] = None,
    price: Optional[float] = None,
    currency: Optional[str] = "€",
    url: Optional[str] = None,
    store_id: Optional[int] = None,
) -> dict:
    """Create a new product listing on Partle. Requires an API key.

    Use this when the user wants to add an item for sale. Each call creates
    a new record — never call twice with identical input expecting only one
    record (it is **not** idempotent). For updates to existing products,
    use `update_product`.

    Args:
        api_key: Partle API key, prefix `pk_`. Generate at
            https://partle.rubenayla.xyz/account.
        name: Product name. Required, 1–200 chars.
        description: Long-form product description. Optional.
        price: Price in whole currency units, **not** cents. e.g. ``15.99``
            means €15.99. Max 100000. Omit for "ask the seller".
        currency: Currency symbol. Defaults to `€`. Use `$`, `£`, etc.
        url: Link to the merchant's product page. Optional but recommended.
        store_id: ID of the store this product belongs to. Omit for a
            personal listing not tied to any store.

    Returns:
        The created product record including its new `id` and canonical
        `partle_url`. Share `partle_url` with the user.
    """
    payload: dict[str, Any] = {"name": name}
    if description is not None:
        payload["description"] = description
    if price is not None:
        payload["price"] = price
    if currency is not None:
        payload["currency"] = currency
    if url is not None:
        payload["url"] = url
    if store_id is not None:
        payload["store_id"] = store_id
    return _post_external("/products", api_key, payload)


@mcp.tool(
    annotations=ToolAnnotations(
        title="Update product",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
    )
)
def update_product(
    api_key: str,
    product_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    price: Optional[float] = None,
    currency: Optional[str] = None,
    url: Optional[str] = None,
) -> dict:
    """Update fields on an existing product. Requires an API key.

    Only fields you pass are changed; omitted fields are preserved.
    Idempotent — calling twice with the same input yields the same final
    state. For creating a new listing, use `create_product` instead.

    The API key must own the product. Trying to update someone else's
    product returns a 403/404.

    Args:
        api_key: Partle API key (prefix `pk_`).
        product_id: ID of the product to update. Get from `create_product`'s
            return value, `get_my_products`, or `search_products`.
        name: New product name. Omit to leave unchanged.
        description: New description. Omit to leave unchanged.
        price: New price in whole currency units (e.g. 15.99 = €15.99).
        currency: New currency symbol.
        url: New merchant URL.

    Returns:
        The updated product record (full, not just the changed fields).
    """
    payload: dict[str, Any] = {}
    if name is not None:
        payload["name"] = name
    if description is not None:
        payload["description"] = description
    if price is not None:
        payload["price"] = price
    if currency is not None:
        payload["currency"] = currency
    if url is not None:
        payload["url"] = url
    return _patch_external(f"/products/{product_id}", api_key, payload)


@mcp.tool(
    annotations=ToolAnnotations(
        title="Delete product",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
    )
)
def delete_product(api_key: str, product_id: int) -> dict:
    """Permanently delete a product listing and all its images. Destructive.

    Use only when the user explicitly asks to remove a listing they own.
    Cannot be undone — there is no soft-delete or trash bin. Idempotent:
    deleting a product that no longer exists returns 404, not an error
    state on your side.

    The API key must own the product.

    Args:
        api_key: Partle API key (prefix `pk_`).
        product_id: ID of the product to delete. Get from `get_my_products`.

    Returns:
        ``{"deleted": product_id}`` on success.
    """
    _delete_external(f"/products/{product_id}", api_key)
    return {"deleted": product_id}


@mcp.tool(
    annotations=ToolAnnotations(
        title="Upload product image",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
    )
)
def upload_product_image(
    api_key: str,
    product_id: int,
    image_base64: Optional[str] = None,
    content_type: Optional[str] = None,
    image_url: Optional[str] = None,
) -> dict:
    """Attach an image to an existing product. Provide exactly one of
    ``image_base64`` (with ``content_type``) **or** ``image_url``.

    Use this after `create_product` returns a product ID. For replacing
    a previously-uploaded image, delete the old one with
    `delete_product_image` first. Marked destructive because subsequent
    edits to the image set are visible publicly.

    Args:
        api_key: Partle API key (prefix `pk_`).
        product_id: ID of the product to attach the image to.
        image_base64: Raw image data, base64-encoded. When set,
            ``content_type`` is required (e.g. ``image/jpeg``).
        content_type: MIME type of the base64 payload. Required with
            ``image_base64``. One of: `image/jpeg`, `image/png`,
            `image/gif`, `image/webp`.
        image_url: URL the server should fetch the image from. Use this
            when the image is already hosted somewhere public — saves
            base64 overhead.

    Returns:
        The created `ProductImage` record with its `id` (use for deletion)
        and storage path.
    """
    payload: dict[str, Any] = {}
    if image_base64 is not None:
        payload["image_base64"] = image_base64
    if content_type is not None:
        payload["content_type"] = content_type
    if image_url is not None:
        payload["image_url"] = image_url
    return _post_external(f"/products/{product_id}/images", api_key, payload)


@mcp.tool(
    annotations=ToolAnnotations(
        title="Delete product image",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
    )
)
def delete_product_image(api_key: str, product_id: int, image_id: int) -> dict:
    """Remove a specific image from a product. Destructive, idempotent.

    Use when an image was uploaded by mistake or the merchant updated their
    listing. The product itself is preserved — only the image record and
    its file are removed. To remove the product entirely use
    `delete_product`.

    Args:
        api_key: Partle API key (prefix `pk_`).
        product_id: ID of the product the image belongs to.
        image_id: ID of the image to delete. Visible in the `images` array
            of `get_product` responses.

    Returns:
        ``{"deleted_image": image_id}`` on success.
    """
    _delete_external(f"/products/{product_id}/images/{image_id}", api_key)
    return {"deleted_image": image_id}


@mcp.tool(
    annotations=ToolAnnotations(title="List my products", readOnlyHint=True)
)
def get_my_products(api_key: str, limit: int = 50) -> dict:
    """List products created by the API key's owner. Requires an API key.

    Use this when the user asks "what have I listed?" or before bulk
    operations like updating prices across multiple of their products.
    Distinct from `search_products`, which searches the public catalog
    without owner scoping.

    Read-only.

    Args:
        api_key: Partle API key (prefix `pk_`).
        limit: Maximum results (1–200, default 50).

    Returns:
        ``{"result": [Product, …]}`` — same shape as `search_products`.
    """
    r = httpx.get(
        f"{EXTERNAL}/products",
        headers={"X-API-Key": api_key},
        params={"limit": limit},
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    return {"result": r.json()}
