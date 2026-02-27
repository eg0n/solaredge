from solaredge import SolaredgeMeter, SolaredgeInverter, METER_BASES
from pymodbus.client import AsyncModbusTcpClient
from argparse import ArgumentParser
import asyncio
import json
import logging
import sys

logger = logging.getLogger(__name__)


async def main():
    p = ArgumentParser()
    p.add_argument("--verbose", "-v", action="store_true")
    args = p.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    c = AsyncModbusTcpClient("192.168.153.2", port=1502)
    await c.connect()

    # get data from all our devices
    i1 = SolaredgeInverter(id=1, name="Inverter")
    i2 = SolaredgeInverter(id=2, name="EV Charger")
    m = SolaredgeMeter(id=1, base=METER_BASES[0], name="Meter")
    for d in [i1, i2, m]:
        await d.update(client=c)
    json.dump({d.name: d.report() for d in [i1, i2, m]}, fp=sys.stdout, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
