import asyncio
from pathlib import Path

from eibon.debuger import GDBObject


async def main():
    binary = Path(__file__).parent.resolve() / 'buff'
    args = [
        'a' * 400,
    ]

    async with await GDBObject().launch(str(binary), args) as proc:
        stdout, stderr = await proc.communicate()
        print(stdout)
        print(stderr)


if __name__ == '__main__':
    asyncio.run(main(), debug=True)
