import asyncio

import main


async def probe() -> None:
    async with main.lifespan(main.app):
        print("lifespan-entered")


if __name__ == "__main__":
    asyncio.run(probe())
