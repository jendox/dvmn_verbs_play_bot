from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx


@asynccontextmanager
async def get_async_http_client(base_url: str, read_timeout: float) -> AsyncGenerator[httpx.AsyncClient, None]:
    client: httpx.AsyncClient | None = None
    try:
        client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(10.0, read=read_timeout),
        )
        yield client
    finally:
        if client:
            await client.aclose()
