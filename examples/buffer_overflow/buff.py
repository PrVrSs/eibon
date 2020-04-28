import asyncio
from pathlib import Path

from eibon.debuger import GDBObject


async def main():
    binary = Path(__file__).parent.resolve() / 'buff'
    response = await GDBObject().launch(str(binary), additional_args=['a' * 40])
    print(response)


if __name__ == '__main__':
    asyncio.run(main(), debug=True)
