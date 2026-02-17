from fastapi import Request
from fastapi.responses import JSONResponse
from openai import APIConnectionError, APIStatusError, RateLimitError


async def openai_rate_limit_handler(request: Request, exc: RateLimitError) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "AI service is temporarily rate-limited. Please try again in a moment."},
    )


async def openai_api_handler(request: Request, exc: APIStatusError) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={"detail": "AI service returned an error. Please try again."},
    )


async def openai_connection_handler(request: Request, exc: APIConnectionError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": "Could not reach AI service. Please try again shortly."},
    )
