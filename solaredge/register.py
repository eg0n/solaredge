from pymodbus.client.mixin import ModbusClientMixin as mcm
from typing import Any
import logging
import struct

logger = logging.getLogger(__name__)


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
        device: object,
        length: int = 1,
        word_order: str = "big",
        label: str | None = None,
        units: str | None = None,
    ):
        self.address = address
        self.length = length
        self.word_order = word_order
        self.data_type = data_type
        self.device = device
        self.label = label
        self.units = units

    def decode(self, registers: list[int]) -> Any:
        if not registers:
            return None

        # 1. Byte packing based on word order
        format_char = ">" if self.word_order == "big" else "<"
        byte_buffer = b"".join([struct.pack(f"{format_char}H", r) for r in registers])

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


def apply_scale_factors(data: dict[str, Any]) -> dict[str, Any]:
    """
    Identifies scale factor registers (ending in "Scale Factor") and applies
    them to their respective base registers.
    """
    scaled_data = data.copy()

    # 1. Identify all scale factor keys in the current dataset
    sf_keys = [k for k in data.keys() if k.endswith("Scale Factor")]

    for sf_key in sf_keys:
        base_text = sf_key[:-13]
        for base_key in filter(lambda k: base_text in k, data.keys()):
            if data[sf_key] is not None and data[base_key] is not None:
                raw_value = data[base_key]
                sf_value = data[sf_key]

                # 2. Handle the "SunSpec" scale factor logic
                # SF is a signed 16-bit integer (e.g., -2 means 10^-2 or 0.01)
                try:
                    # We use 10 ** sf_value for the multiplier
                    multiplier = 10**sf_value
                    scaled_data[base_key] = raw_value * multiplier

                    # Optional: Round to avoid float precision artifacts (e.g., 0.000000001)
                    if sf_value < 0:
                        scaled_data[base_key] = round(
                            scaled_data[base_key], abs(sf_value)
                        )

                except TypeError, ValueError:
                    # Skip if the raw value isn't a number
                    continue
        del scaled_data[sf_key]

    return scaled_data
