from typing import Any, Optional
import httpx


class HttpxClient:
    def __init__(
        self,
        base_url: str,
        time_out: Optional[httpx.Timeout] = None,
    ):
        self.client = httpx.AsyncClient(
            timeout=time_out
            or httpx.Timeout(
                connect=5.0,
                read=60,
                write=5.0,
                pool=5.0,
            ),
            base_url=base_url,
        )

    async def get(
        self,
        path: str,
        headers: dict,
        params: httpx._types.QueryParamTypes | None = None,
        cookies: httpx._types.CookieTypes | None = None,
    ):
        response = await self.client.get(
            path,
            headers=headers,
            params=params,
            cookies=cookies,
        )
        return response

    async def post(
        self,
        path: str,
        headers: dict,
        content: Optional[httpx._types.RequestContent] = None,
        data: httpx._types.RequestData | None = None,
        files: httpx._types.RequestFiles | None = None,
        json: Any | None = None,
        params: httpx._types.QueryParamTypes | None = None,
        cookies: httpx._types.CookieTypes | None = None,
    ):
        response = await self.client.post(
            path,
            headers=headers,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            cookies=cookies,
        )
        return response

    async def put(
        self,
        path: str,
        headers: dict,
        content: Optional[httpx._types.RequestContent] = None,
        data: httpx._types.RequestData | None = None,
        files: httpx._types.RequestFiles | None = None,
        json: Any | None = None,
        params: httpx._types.QueryParamTypes | None = None,
        cookies: httpx._types.CookieTypes | None = None,
    ):
        response = await self.client.put(
            path,
            headers=headers,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            cookies=cookies,
        )
        return response

    async def delete(
        self,
        path: str,
        headers: dict,
        params: httpx._types.QueryParamTypes | None = None,
        cookies: httpx._types.CookieTypes | None = None,
    ):
        response = await self.client.delete(
            path,
            headers=headers,
            params=params,
            cookies=cookies,
        )
        return response
