from pymodbus.client.mixin import ModbusClientMixin as mcm
from typing import Any
import logging
import struct

logger = logging.getLogger(__name__)

TEXT_MAPS = {
    "i_status": {
        1: "Off",
        2: "Sleeping",
        3: "Starting",
        4: "Producing",
        5: "Throttled",
        6: "Shutting Down",
        7: "Fault",
        8: "Standby",
    },
    "c_sunspec_did": {
        101: "Single Phase Inverter",
        102: "Split Phase Inverter",
        103: "Three Phase Inverter",
        201: "Single Phase Meter",
        202: "Split Phase Meter",
        203: "Wye 3P1N Three Phase Meter",
        204: "Delta 3P Three Phase Meter",
        802: "Battery",
        803: "Lithium Ion Bank Battery",
        804: "Lithium Ion String Battery",
        805: "Lithium Ion Module Battery",
        806: "Flow Battery",
        807: "Flow String Battery",
        808: "Flow Module Battery",
        809: "Flow Stack Battery",
    },
    "b_status": {
        0: "Off",
        1: "Standby",
        2: "Init",
        3: "Charge",
        4: "Discharge",
        5: "Fault",
        6: "Idle",
    },
    "b_status_internal": {
        0: "Off",
        1: "Standby",
        2: "Init",
        3: "Charge",
        4: "Discharge",
        5: "Fault",
        6: "Idle",
    },
}


class HoldingRegister:
    """
    Read-only value storage
    """

    # Constants for SunSpec "Not Implemented" values
    INVALID_VALUES = {
        mcm.DATATYPE.INT16: {0x8000, -0x8000},
        mcm.DATATYPE.UINT16: {0xFFFF},
        mcm.DATATYPE.INT32: {0x80000000, -0x80000000},
        mcm.DATATYPE.UINT32: {0xFFFFFFFF},
        mcm.DATATYPE.INT64: {0x8000000000000000, -0x8000000000000000},
        mcm.DATATYPE.UINT64: {0xFFFFFFFFFFFFFFFF},
        mcm.DATATYPE.FLOAT32: {0x7FC00000},  # SunSpec NaN
    }

    def __init__(
        self,
        address: int,
        data_type: mcm.DATATYPE,
        device: object,  # "SolaredgeDevice"
        length: int = 1,
        word_order: str = "big",
        label: str | None = None,
        units: str | None = None,
        key: str | None = None,
        sf_key: str | None = None,
    ):
        self.address = address
        self.data_type = data_type
        self.device = device  # Reference back to the Inverter/Battery
        self.length = length
        self.word_order = word_order
        self.label = label
        self.units = units
        self.key = key  # e.g., "i_ac_power"
        self.sf_key = sf_key  # e.g., "i_ac_power_sf"

    @property
    def raw_value(self):
        """Pulls the latest raw decoded value from the device cache."""
        return self.device.data_cache.get(self.key)

    @property
    def value(self):
        """Calculates the scaled value using the device cache."""
        val = self.raw_value
        if val is None:
            return None

        # If there is a scale factor, apply it
        if self.sf_key:
            sf = self.device.data_cache.get(self.sf_key)
            if sf is not None:
                val = val * (10**sf)
                # Round based on the scale factor precision
                if sf < 0:
                    val = round(val, abs(sf))
        return val

    @property
    def text_value(self) -> str | None:
        """
        Looks up the text representation if the register key
        exists in the constant maps.
        """
        raw_val = self.device.data_cache.get(self.key)
        if raw_val is not None and self.key in TEXT_MAPS:
            return TEXT_MAPS[self.key].get(raw_val)
        return None

    def __str__(self):
        """The 'magic' print method."""
        val = self.value
        if val is None:
            return "N/A"
        if self.text_value:
            return self.text_value
        unit_str = f" {self.units}" if self.units else ""
        return f"{val}{unit_str}"

    def __repr__(self):
        if self.text_value:
            return f"<HoldingRegister({self.label}={self.value} ({self.text_value}))>"
        return f"<HoldingRegister({self.label}={self.value})>"

    def decode(self, registers: list[int]) -> Any:
        if not registers:
            return None

        # 1. Byte packing based on word order
        format_char = ">" if self.word_order == "big" else "<"
        byte_buffer = b"".join(
            [struct.pack(f"{format_char}H", r & 0xFFFF) for r in registers]
        )

        # 2. String Handling
        if self.data_type == mcm.DATATYPE.STRING:
            val = byte_buffer.decode("utf-8", errors="ignore").split("\0")[0].strip()
            # SunSpec strings filled with 0xFF or nulls should be treated as None
            return val if val and not all(b == 0xFF for b in byte_buffer) else None

        # 3. Numeric Mapping
        mapping = {
            mcm.DATATYPE.INT16: "h",
            mcm.DATATYPE.UINT16: "H",
            mcm.DATATYPE.INT32: "i",
            mcm.DATATYPE.UINT32: "I",
            mcm.DATATYPE.FLOAT32: "f",
            mcm.DATATYPE.UINT64: "Q",
        }

        fmt = mapping.get(self.data_type)
        if not fmt:
            return registers

        try:
            # Unpack raw value
            raw_val = struct.unpack(f"{format_char}{fmt}", byte_buffer)[0]

            # 4. SENTINEL CHECK
            # We check the raw integer bit-pattern against our invalid set
            # For floats, we convert the bytes to an int first to check the sentinel
            check_val = raw_val
            if self.data_type == mcm.DATATYPE.FLOAT32:
                check_val = struct.unpack(f"{format_char}I", byte_buffer)[0]

            if self.data_type in self.INVALID_VALUES:
                if check_val in self.INVALID_VALUES[self.data_type]:
                    return None

            return raw_val
        except struct.error:
            return None
