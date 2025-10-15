from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx

CONNECT_TIMEOUT = 5.0
WRITE_TIMEOUT = 10.0
POOL_TIMEOUT = 60.0
MAX_CONNECTIONS = 50
KEEP_ALIVE_EXPIRY = 60.0


@asynccontextmanager
async def get_async_http_client(base_url: str, read_timeout: float) -> AsyncGenerator[httpx.AsyncClient, None]:
    client: httpx.AsyncClient | None = None
    try:
        client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(
                connect=CONNECT_TIMEOUT,
                write=WRITE_TIMEOUT,
                read=read_timeout + 10.0,
                pool=POOL_TIMEOUT,
            ),
            limits=httpx.Limits(
                max_connections=MAX_CONNECTIONS,
                max_keepalive_connections=MAX_CONNECTIONS // 2,
                keepalive_expiry=KEEP_ALIVE_EXPIRY,
            ),
            http2=True,
            trust_env=True,
        )
        yield client
    finally:
        if client:
            await client.aclose()
