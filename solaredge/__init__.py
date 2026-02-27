from .battery import SolaredgeBattery
from .inverter import SolaredgeInverter
from .meter import SolaredgeMeter

# when going through an inverter to get to a meter/battery, this is
# where the it begins in the inverter's address space

METER_BASES = [0x9CBB, 0x9D69, 0x9E17]
BATTERY_BASES = [0xE100, 0xE200]

__all__ = [
    SolaredgeBattery,
    SolaredgeInverter,
    SolaredgeMeter,
    BATTERY_BASES,
    METER_BASES,
]
