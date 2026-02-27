from solaredge.meter import SolaredgeMeter


class TestSolaredgeMeter:
    """Test suite for SolaredgeMeter"""

    def test_meter_initialization(self):
        """Test meter initializes with base address"""
        meter = SolaredgeMeter(id=1)
        assert meter.id == 1
        assert meter.name == "meter_1_0x0"
        assert len(meter.registers) > 0

    def test_meter_has_current_registers(self):
        """Test meter has AC current registers"""
        meter = SolaredgeMeter(id=1)
        assert "m_ac_current" in meter.registers or "current" in meter.registers

    def test_meter_has_voltage_registers(self):
        """Test meter has AC voltage registers"""
        meter = SolaredgeMeter(id=1)
        voltage_keys = [k for k in meter.registers.keys() if "voltage" in k]
        assert len(voltage_keys) > 0

    def test_meter_has_power_registers(self):
        """Test meter has power registers"""
        meter = SolaredgeMeter(id=1)
        power_keys = [k for k in meter.registers.keys() if "power" in k]
        assert len(power_keys) > 0

    def test_meter_has_energy_registers(self):
        """Test meter has energy registers"""
        meter = SolaredgeMeter(id=1)
        energy_keys = [k for k in meter.registers.keys() if "wh" in k or "energy" in k]
        assert len(energy_keys) > 0

    def test_meter_offset_1(self):
        """Test meter with offset 1"""
        meter1 = SolaredgeMeter(id=1)
        meter2 = SolaredgeMeter(id=2, base=1)
        # Offset should change the base addresses
        assert meter1.base != meter2.base

    def test_meter_registers_sorted(self):
        """Test meter registers are properly sorted by address"""
        meter = SolaredgeMeter(id=1)
        addresses = [reg.address for reg in meter.registers.values()]
        assert addresses == sorted(addresses)
