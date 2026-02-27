import pytest
from solaredge.device import SolaredgeDevice
from solaredge.register import HoldingRegister
from pymodbus.client.mixin import ModbusClientMixin as mcm
from unittest.mock import AsyncMock


class TestSolaredgeDevice:
    """Test suite for SolaredgeDevice"""

    def test_device_initialization(self):
        """Test device initializes with correct attributes"""
        device = SolaredgeDevice(id=1, name="TestDevice", base=0x9C00)
        assert device.id == 1
        assert device.name == "TestDevice"
        assert device.base == 0x9C00
        assert device.registers == {}
        assert device.data_cache == {}

    def test_device_init_registers(self):
        """Test _init_registers sets key and auto-detects scale factors"""
        device = SolaredgeDevice(id=1)
        device.registers = {
            "power": HoldingRegister(
                0x100, mcm.DATATYPE.INT16, device, 1, "big", "Power", "W"
            ),
            "power_sf": HoldingRegister(
                0x101, mcm.DATATYPE.INT16, device, 1, "big", "Power SF"
            ),
        }
        device._init_registers()

        assert device.registers["power"].key == "power"
        assert device.registers["power"].sf_key == "power_sf"
        assert device.registers["power_sf"].key == "power_sf"

    def test_group_registers_empty(self):
        """Test group_registers with no registers"""
        device = SolaredgeDevice(id=1)
        groups = device.group_registers()
        assert groups == []

    def test_group_registers_single(self):
        """Test group_registers with single register"""
        device = SolaredgeDevice(id=1)
        reg = HoldingRegister(0x100, mcm.DATATYPE.INT16, device, 1, "big", "Test")
        device.registers = {"test": reg}
        groups = device.group_registers()
        assert len(groups) == 1
        assert len(groups[0]) == 1
        assert groups[0][0] == reg

    def test_group_registers_contiguous(self):
        """Test group_registers groups contiguous adjacent registers"""
        device = SolaredgeDevice(id=1)
        reg1 = HoldingRegister(0x100, mcm.DATATYPE.INT16, device, 1, "big", "Test1")
        reg2 = HoldingRegister(0x101, mcm.DATATYPE.INT16, device, 1, "big", "Test2")
        reg3 = HoldingRegister(0x102, mcm.DATATYPE.INT16, device, 1, "big", "Test3")
        device.registers = {"test1": reg1, "test2": reg2, "test3": reg3}
        groups = device.group_registers()
        assert len(groups) == 1
        assert len(groups[0]) == 3

    def test_group_registers_non_contiguous(self):
        """Test group_registers splits non-contiguous registers"""
        device = SolaredgeDevice(id=1)
        reg1 = HoldingRegister(0x100, mcm.DATATYPE.INT16, device, 1, "big", "Test1")
        reg2 = HoldingRegister(0x105, mcm.DATATYPE.INT16, device, 1, "big", "Test2")
        device.registers = {"test1": reg1, "test2": reg2}
        groups = device.group_registers()
        assert len(groups) == 2

    def test_group_registers_different_data_types(self):
        """Test group_registers splits registers with different data types"""
        device = SolaredgeDevice(id=1)
        reg1 = HoldingRegister(0x100, mcm.DATATYPE.INT16, device, 1, "big", "Test1")
        reg2 = HoldingRegister(0x101, mcm.DATATYPE.INT32, device, 2, "big", "Test2")
        device.registers = {"test1": reg1, "test2": reg2}
        groups = device.group_registers()
        assert len(groups) == 2

    def test_group_registers_different_word_order(self):
        """Test group_registers splits registers with different word order"""
        device = SolaredgeDevice(id=1)
        reg1 = HoldingRegister(0x100, mcm.DATATYPE.INT16, device, 1, "big", "Test1")
        reg2 = HoldingRegister(0x101, mcm.DATATYPE.INT16, device, 1, "little", "Test2")
        device.registers = {"test1": reg1, "test2": reg2}
        groups = device.group_registers()
        assert len(groups) == 2

    def test_group_registers_max_length(self):
        """Test group_registers respects max_read_length"""
        device = SolaredgeDevice(id=1)
        # Create 150 16-bit registers (would need 150 addresses)
        for i in range(150):
            device.registers[f"test{i}"] = HoldingRegister(
                0x100 + i, mcm.DATATYPE.INT16, device, 1, "big", f"Test{i}"
            )
        groups = device.group_registers(max_read_length=120)
        # Should split into multiple groups due to length limit
        assert len(groups) > 1

    @pytest.mark.asyncio
    async def test_update_calls_read_groups(self):
        """Test update method calls read_groups and updates cache"""
        device = SolaredgeDevice(id=1)
        device.registers = {
            "test": HoldingRegister(0x100, mcm.DATATYPE.INT16, device, 1, "big", "Test")
        }

        mock_client = AsyncMock()
        device.read_groups = AsyncMock(return_value={"test": 42})

        await device.update(mock_client)

        device.read_groups.assert_called_once_with(mock_client)
        assert device.data_cache == {"test": 42}

    def test_report_excludes_scale_factors(self):
        """Test report method excludes scale factor registers"""
        device = SolaredgeDevice(id=1)
        device.registers = {
            "power": HoldingRegister(
                0x100, mcm.DATATYPE.INT16, device, 1, "big", "Power", "W", key="power"
            ),
            "power_sf": HoldingRegister(
                0x101, mcm.DATATYPE.INT16, device, 1, "big", "Power SF", key="power_sf"
            ),
        }
        device.data_cache = {"power": 100, "power_sf": -1}

        report = device.report()
        assert "Power" in report
        assert "Power SF" not in report

    def test_report_includes_correct_values(self):
        """Test report method includes correct string values"""
        device = SolaredgeDevice(id=1)
        device.registers = {
            "power": HoldingRegister(
                0x100, mcm.DATATYPE.INT16, device, 1, "big", "Power", "W", key="power"
            ),
        }
        device.data_cache = {"power": 100}

        report = device.report()
        assert report["Power"] == "100 W"
