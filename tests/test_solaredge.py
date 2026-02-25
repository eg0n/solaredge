import pytest
import struct
from unittest.mock import AsyncMock, MagicMock
from solaredge.device import SolaredgeDevice
from solaredge.register import HoldingRegister
from pymodbus.client.mixin import ModbusClientMixin as mcm

# --- Fixtures ---


class MockDevice(SolaredgeDevice):
    def __init__(self):
        super().__init__(id=1)
        self.registers = {
            "pwr": HoldingRegister(0x9C93, mcm.DATATYPE.INT16, self, label="Power", units="W"),
            "pwr_sf": HoldingRegister(0x9C94, mcm.DATATYPE.INT16, self, label="Power SF"),
            "model": HoldingRegister(0x9C54, mcm.DATATYPE.STRING, self, length=16, label="Model"),
        }
        self._init_registers()


@pytest.fixture
def device():
    return MockDevice()


@pytest.fixture
def mock_client():
    return AsyncMock()


# --- Decoding & Sentinel Tests ---


def test_register_decode_float(device):
    # 100.0 in Float32 (Big Endian) is 0x42C80000
    reg = HoldingRegister(0x0, mcm.DATATYPE.FLOAT32, device, length=2)
    assert reg.decode([0x42C8, 0x0000]) == 100.0


def test_register_decode_sentinel_int16(device):
    # 0x8000 is "Not Implemented" for INT16
    reg = HoldingRegister(0x0, mcm.DATATYPE.INT16, device)
    assert reg.decode([0x8000]) is None


def test_string_decoding_with_padding(device):
    """Verifies that strings are stripped of nulls and handled if uninitialized."""
    reg = device.registers["model"]

    # Case 1: Valid string with null padding
    # 'SolarEdge' padded with nulls to 32 bytes (16 registers)
    valid_data = list(struct.unpack(">16H", b"SolarEdge".ljust(32, b"\0")))
    assert reg.decode(valid_data) == "SolarEdge"

    # Case 2: Uninitialized string (filled with 0xFF)
    invalid_data = [0xFFFF] * 16
    assert reg.decode(invalid_data) is None


# --- Grouping Logic Tests ---


def test_grouping_logic(device):
    # pwr (0x9C93) and pwr_sf (0x9C94) are adjacent and same type
    groups = device.group_registers()
    # In MockDevice, model (0x9C54) is far from pwr (0x9C93)
    # Expected groups: [model] and [pwr, pwr_sf]
    assert len(groups) == 2
    assert any(len(g) == 2 for g in groups)  # The pwr group


# --- Data Proxy & Cache Tests ---


def test_cache_value_lookup(device):
    device.data_cache = {"pwr": 1500, "pwr_sf": -1}
    reg = device.registers["pwr"]
    # 1500 * 10^-1 = 150.0
    assert reg.value == 150.0
    assert str(reg) == "Power: 150.0 W"


# --- Async Integration Tests ---


@pytest.mark.asyncio
async def test_update_lifecycle(device, mock_client):
    # Prepare a mock response for the bulk read
    # Group 1: Model string (16 regs)
    # Group 2: Power and SF (2 regs)
    mock_response = MagicMock()
    mock_response.isError.return_value = False

    # We simulate two different calls for the two groups
    mock_client.read_holding_registers.side_effect = [
        MagicMock(
            registers=list(struct.unpack(">16H", b"SE10K".ljust(32, b"\0"))), isError=lambda: False
        ),
        MagicMock(registers=[3000, 0xFFFF], isError=lambda: False),
    ]

    await device.update(mock_client)

    assert device.data_cache["model"] == "SE10K"
    assert device.data_cache["pwr"] == 3000
    assert device.registers["pwr"].value == 300.0


def test_grouping_max_read_length_split(device):
    """
    Verifies that adjacent registers with matching metadata are split
    into multiple groups if the total length exceeds max_read_length.
    """
    # Create 5 adjacent registers, each of length 1
    # Addresses: 0x100, 0x101, 0x102, 0x103, 0x104
    test_regs = {}
    for i in range(5):
        key = f"reg_{i}"
        test_regs[key] = HoldingRegister(
            address=0x100 + i, data_type=mcm.DATATYPE.UINT16, device=device, length=1, key=key
        )

    device.registers = test_regs

    # Test 1: Max length of 2.
    # Expected: Group1 (2), Group2 (2), Group3 (1)
    groups_of_2 = device.group_registers(max_read_length=2)
    assert len(groups_of_2) == 3
    assert len(groups_of_2[0]) == 2
    assert len(groups_of_2[1]) == 2
    assert len(groups_of_2[2]) == 1

    # Test 2: Max length of 5.
    # Expected: Single group containing all 5
    groups_of_5 = device.group_registers(max_read_length=5)
    assert len(groups_of_5) == 1
    assert len(groups_of_5[0]) == 5


def test_grouping_mixed_lengths_limit(device):
    """
    Verifies that multi-register types (like FLOAT32) are not split
    across groups and correctly trigger a new group when the limit is hit.
    """
    # Reg 1: UINT16 (len 1) at 0x200
    # Reg 2: FLOAT32 (len 2) at 0x201
    device.registers = {
        "r1": HoldingRegister(0x200, mcm.DATATYPE.UINT16, device, length=1, key="r1"),
        "r2": HoldingRegister(0x201, mcm.DATATYPE.FLOAT32, device, length=2, key="r2"),
    }

    # If max_read_length is 2, the FLOAT32 cannot fit in Group 1 with UINT16
    groups = device.group_registers(max_read_length=2)
    assert len(groups) == 2
    assert groups[0][0].key == "r1"
    assert groups[1][0].key == "r2"
