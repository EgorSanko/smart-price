"""Image proxy to bypass hotlink protection on marketplace images."""

from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Query
from fastapi.responses import Response


router = APIRouter(tags=["images"])

_ALLOWED_HOSTS = {
    "wbbasket.ru",
    "wbcontent.net",
    "avatars.mds.yandex.net",
    "imgproxy.onliner.by",
    "content.onliner.by",
    "cdn1.ozone.ru",
    "ir.ozone.ru",
    "regard.ru",
    "www.regard.ru",
    "citilink.ru",
    "www.citilink.ru",
    "static.citilink.ru",
    "cdn-img.citilink.ru",
    "images.citilink.ru",
    "world-devices.ru",
    "www.world-devices.ru",
}

_REFERERS = {
    "wbbasket.ru": "https://www.wildberries.ru/",
    "wbcontent.net": "https://www.wildberries.ru/",
    "avatars.mds.yandex.net": "https://market.yandex.ru/",
    "imgproxy.onliner.by": "https://catalog.onliner.by/",
    "content.onliner.by": "https://catalog.onliner.by/",
    "cdn1.ozone.ru": "https://www.ozon.ru/",
    "ir.ozone.ru": "https://www.ozon.ru/",
    "regard.ru": "https://www.regard.ru/",
    "www.regard.ru": "https://www.regard.ru/",
    "citilink.ru": "https://www.citilink.ru/",
    "www.citilink.ru": "https://www.citilink.ru/",
    "static.citilink.ru": "https://www.citilink.ru/",
    "cdn-img.citilink.ru": "https://www.citilink.ru/",
    "images.citilink.ru": "https://www.citilink.ru/",
    "world-devices.ru": "https://world-devices.ru/",
    "www.world-devices.ru": "https://world-devices.ru/",
}


def _match_host(hostname: str) -> str | None:
    """Check if hostname belongs to an allowed domain."""
    for allowed in _ALLOWED_HOSTS:
        if hostname == allowed or hostname.endswith("." + allowed):
            return allowed
    return None


@router.get("/image-proxy")
async def image_proxy(
    url: str = Query(..., description="Image URL to proxy"),
) -> Response:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return Response(status_code=400, content=b"Bad scheme")

    domain = _match_host(parsed.hostname or "")
    if not domain:
        return Response(status_code=403, content=b"Host not allowed")

    referer = _REFERERS.get(domain, "")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                url,
                headers={
                    "Referer": referer,
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                    "Accept": "image/webp,image/avif,image/*,*/*;q=0.8",
                },
                follow_redirects=True,
            )

            if r.status_code != 200:
                return Response(status_code=r.status_code, content=b"Upstream error")

            content_type = r.headers.get("content-type", "image/webp")

            return Response(
                content=r.content,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=86400",
                    "Access-Control-Allow-Origin": "*",
                },
            )

    except Exception:
        return Response(status_code=502, content=b"Proxy error")
