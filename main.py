from solaredge.inverter import SolaredgeInverter
from pymodbus.client import AsyncModbusTcpClient
from argparse import ArgumentParser
import asyncio
import logging

logger = logging.getLogger(__name__)


async def main():
    p = ArgumentParser()
    p.add_argument("--verbose", "-v", action="store_true")
    p.add_argument("--device", "-d", default=1, type=int)
    args = p.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    c = AsyncModbusTcpClient("192.168.153.2", port=1502)
    await c.connect()
    d = SolaredgeInverter(args.device)
    await d.update(c)
    [
        print(f"{k:<20s} => {str(v):20s}")
        for k, v in d.registers.items()
        if not k.endswith("_sf")
    ]


if __name__ == "__main__":
    asyncio.run(main())
