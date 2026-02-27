import struct
from pymodbus.client.mixin import ModbusClientMixin as mcm
from solaredge.register import HoldingRegister


class MockDevice:
    """Mock device for testing HoldingRegister"""

    def __init__(self):
        self.data_cache = {}


class TestHoldingRegister:
    """Test suite for HoldingRegister decode and value methods"""

    def test_register_initialization(self):
        """Test register initializes with correct attributes"""
        device = MockDevice()
        reg = HoldingRegister(
            address=0x100,
            data_type=mcm.DATATYPE.INT16,
            device=device,
            length=1,
            word_order="big",
            label="Test Register",
            units="V",
            key="test_key",
            sf_key="test_sf",
        )
        assert reg.address == 0x100
        assert reg.data_type == mcm.DATATYPE.INT16
        assert reg.length == 1
        assert reg.label == "Test Register"
        assert reg.units == "V"
        assert reg.key == "test_key"
        assert reg.sf_key == "test_sf"

    def test_decode_int16_big_endian(self):
        """Test decoding INT16 with big endian byte order"""
        device = MockDevice()
        reg = HoldingRegister(0x100, mcm.DATATYPE.INT16, device, 1, "big", "Test")

        # Test positive value
        result = reg.decode([100])
        assert result == 100

        # Test negative value
        result = reg.decode([0xFFFF])
        assert result == -1

    def test_decode_int16_little_endian(self):
        """Test decoding INT16 with little endian byte order"""
        device = MockDevice()
        reg = HoldingRegister(0x100, mcm.DATATYPE.INT16, device, 1, "little", "Test")
        result = reg.decode([100])
        assert result == 100

    def test_decode_uint16(self):
        """Test decoding UINT16"""
        device = MockDevice()
        reg = HoldingRegister(0x100, mcm.DATATYPE.UINT16, device, 1, "big", "Test")
        result = reg.decode([65534])
        assert result == 65534
        result = reg.decode([65535])
        assert result is None

    def test_decode_int32(self):
        """Test decoding INT32 (2 registers)"""
        device = MockDevice()
        reg = HoldingRegister(0x100, mcm.DATATYPE.INT32, device, 2, "big", "Test")
        result = reg.decode([0, 100])
        assert result == 100

    def test_decode_uint32(self):
        """Test decoding UINT32"""
        device = MockDevice()
        reg = HoldingRegister(0x100, mcm.DATATYPE.UINT32, device, 2, "big", "Test")
        result = reg.decode([0xFFFF, 0xFFFE])
        assert result == 0xFFFFFFFE
        result = reg.decode([0xFFFF, 0xFFFF])
        assert result is None

    def test_decode_float32(self):
        """Test decoding FLOAT32"""
        device = MockDevice()
        reg = HoldingRegister(0x100, mcm.DATATYPE.FLOAT32, device, 2, "big", "Test")

        # Pack a float value
        packed = struct.pack(">f", 3.14)
        regs = struct.unpack(">HH", packed)
        result = reg.decode(list(regs))
        assert abs(result - 3.14) < 0.01

    def test_decode_string(self):
        """Test decoding STRING"""
        device = MockDevice()
        reg = HoldingRegister(0x100, mcm.DATATYPE.STRING, device, 4, "big", "Test")

        # "TEST" as bytes
        test_str = "TEST"
        byte_val = test_str.encode("utf-8")
        regs = [
            int.from_bytes(byte_val[0:2], byteorder="big"),
            int.from_bytes(byte_val[2:4], byteorder="big"),
        ]
        result = reg.decode(regs)
        assert result == "TEST"

    def test_decode_invalid_int16_sentinel(self):
        """Test that SunSpec 'not implemented' sentinel for INT16 returns None"""
        device = MockDevice()
        reg = HoldingRegister(0x100, mcm.DATATYPE.INT16, device, 1, "big", "Test")
        result = reg.decode([0x8000])  # INT16 sentinel
        assert result is None

    def test_decode_invalid_uint16_sentinel(self):
        """Test that SunSpec 'not implemented' sentinel for UINT16 returns None"""
        device = MockDevice()
        reg = HoldingRegister(0x100, mcm.DATATYPE.UINT16, device, 1, "big", "Test")
        result = reg.decode([0xFFFF])  # UINT16 sentinel
        assert result is None

    def test_decode_invalid_float32_sentinel(self):
        """Test that SunSpec NaN sentinel for FLOAT32 returns None"""
        device = MockDevice()
        reg = HoldingRegister(0x100, mcm.DATATYPE.FLOAT32, device, 2, "big", "Test")
        result = reg.decode([0x7FC0, 0x0000])  # Float NaN
        assert result is None

    def test_decode_empty_registers(self):
        """Test decoding with empty register list"""
        device = MockDevice()
        reg = HoldingRegister(0x100, mcm.DATATYPE.INT16, device, 1, "big", "Test")
        result = reg.decode([])
        assert result is None

    def test_raw_value_property(self):
        """Test raw_value property retrieves from cache"""
        device = MockDevice()
        device.data_cache = {"test_key": 42}
        reg = HoldingRegister(
            0x100, mcm.DATATYPE.INT16, device, 1, "big", "Test", key="test_key"
        )
        assert reg.raw_value == 42

    def test_raw_value_missing(self):
        """Test raw_value returns None when not in cache"""
        device = MockDevice()
        device.data_cache = {}
        reg = HoldingRegister(
            0x100, mcm.DATATYPE.INT16, device, 1, "big", "Test", key="missing"
        )
        assert reg.raw_value is None

    def test_value_with_scale_factor(self):
        """Test value property applies scale factor"""
        device = MockDevice()
        device.data_cache = {"test_key": 100, "test_key_sf": -1}
        reg = HoldingRegister(
            0x100,
            mcm.DATATYPE.INT16,
            device,
            1,
            "big",
            "Test",
            key="test_key",
            sf_key="test_key_sf",
        )
        # 100 * 10^-1 = 10
        assert reg.value == 10.0

    def test_value_with_scale_factor_precision(self):
        """Test value property applies correct rounding"""
        device = MockDevice()
        device.data_cache = {"test_key": 123, "test_key_sf": -2}
        reg = HoldingRegister(
            0x100,
            mcm.DATATYPE.INT16,
            device,
            1,
            "big",
            "Test",
            key="test_key",
            sf_key="test_key_sf",
        )
        # 123 * 10^-2 = 1.23
        assert reg.value == 1.23

    def test_value_without_scale_factor(self):
        """Test value property without scale factor"""
        device = MockDevice()
        device.data_cache = {"test_key": 42}
        reg = HoldingRegister(
            0x100, mcm.DATATYPE.INT16, device, 1, "big", "Test", key="test_key"
        )
        assert reg.value == 42

    def test_text_value_mapped(self):
        """Test text_value property for mapped values"""
        device = MockDevice()
        device.data_cache = {"i_status": 4}
        reg = HoldingRegister(
            0x100, mcm.DATATYPE.UINT16, device, 1, "big", "Status", key="i_status"
        )
        assert reg.text_value == "Producing"

    def test_text_value_not_mapped(self):
        """Test text_value returns None for unmapped registers"""
        device = MockDevice()
        device.data_cache = {"other_key": 123}
        reg = HoldingRegister(
            0x100, mcm.DATATYPE.UINT16, device, 1, "big", "Other", key="other_key"
        )
        assert reg.text_value is None

    def test_str_with_text_value(self):
        """Test __str__ returns text value"""
        device = MockDevice()
        device.data_cache = {"i_status": 4}
        reg = HoldingRegister(
            0x100, mcm.DATATYPE.UINT16, device, 1, "big", "Status", key="i_status"
        )
        assert str(reg) == "Producing"

    def test_str_with_units(self):
        """Test __str__ includes units"""
        device = MockDevice()
        device.data_cache = {"test_key": 42}
        reg = HoldingRegister(
            0x100,
            mcm.DATATYPE.INT16,
            device,
            1,
            "big",
            "Test",
            units="V",
            key="test_key",
        )
        assert str(reg) == "42 V"

    def test_str_na_when_none(self):
        """Test __str__ returns N/A when value is None"""
        device = MockDevice()
        device.data_cache = {}
        reg = HoldingRegister(
            0x100, mcm.DATATYPE.INT16, device, 1, "big", "Test", key="missing"
        )
        assert str(reg) == "N/A"

    def test_repr_with_text_value(self):
        """Test __repr__ includes text value"""
        device = MockDevice()
        device.data_cache = {"i_status": 4}
        reg = HoldingRegister(
            0x100, mcm.DATATYPE.UINT16, device, 1, "big", "Status", key="i_status"
        )
        assert "Producing" in repr(reg)

    def test_repr_without_text_value(self):
        """Test __repr__ without text value"""
        device = MockDevice()
        device.data_cache = {"test_key": 42}
        reg = HoldingRegister(
            0x100, mcm.DATATYPE.INT16, device, 1, "big", "Test", key="test_key"
        )
        assert "Test" in repr(reg) and "42" in repr(reg)
