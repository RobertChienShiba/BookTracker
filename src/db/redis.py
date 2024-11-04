import redis.asyncio as aioredis # type: ignore

from src.config import Config

JTI_EXPIRY = 3600

token_logout = aioredis.from_url(Config.REDIS_LOGOUT_URL)

async def add_jti_to_logout(jti: str) -> None:
    await token_logout.set(name=jti, value="", ex=JTI_EXPIRY)


async def token_in_logout(jti: str) -> bool:
    jti = await token_logout.get(jti)

    return jti is not None