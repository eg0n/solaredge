from solaredge import SolaredgeMeter, SolaredgeInverter, METER_BASES
from pymodbus.client import AsyncModbusTcpClient
from argparse import ArgumentParser
import asyncio
import logging

logger = logging.getLogger(__name__)


async def main():
    p = ArgumentParser()
    p.add_argument("--verbose", "-v", action="store_true")
    args = p.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    c = AsyncModbusTcpClient("192.168.153.2", port=1502)
    await c.connect()

    # get data from all our devices
    i1 = SolaredgeInverter(id=1)
    await i1.update(c)
    i2 = SolaredgeInverter(id=2)
    await i2.update(c)
    m = SolaredgeMeter(id=1, base=METER_BASES[0])
    await m.update(c)
    for d in (i1, i2, m):
        [
            print(f"{k:<20s} => {str(v):20s}")
            for k, v in d.registers.items()
            if not k.endswith("_sf")
        ]


if __name__ == "__main__":
    asyncio.run(main())
