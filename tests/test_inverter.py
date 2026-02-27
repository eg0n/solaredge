from solaredge.inverter import SolaredgeInverter


class TestSolaredgeInverter:
    """Test suite for SolaredgeInverter"""

    def test_inverter_initialization(self):
        """Test inverter initializes correctly"""
        inverter = SolaredgeInverter(id=1)
        assert inverter.id == 1
        assert inverter.name == "inverter_1"
        assert len(inverter.registers) > 0

    def test_inverter_custom_name(self):
        """Test inverter with custom name"""
        inverter = SolaredgeInverter(id=1, name="MyInverter")
        assert inverter.name == "MyInverter"

    def test_inverter_has_ac_current_registers(self):
        """Test inverter has AC current registers"""
        inverter = SolaredgeInverter(id=1)
        assert "i_ac_current" in inverter.registers
        assert "i_ac_currenta" in inverter.registers
        assert "i_ac_currentb" in inverter.registers
        assert "i_ac_currentc" in inverter.registers

    def test_inverter_has_ac_voltage_registers(self):
        """Test inverter has AC voltage registers"""
        inverter = SolaredgeInverter(id=1)
        voltage_keys = [k for k in inverter.registers.keys() if "voltage" in k]
        assert len(voltage_keys) > 0

    def test_inverter_has_dc_registers(self):
        """Test inverter has DC registers"""
        inverter = SolaredgeInverter(id=1)
        assert "i_dc_current" in inverter.registers
        assert "i_dc_voltage" in inverter.registers
        assert "i_dc_power" in inverter.registers

    def test_inverter_has_temperature_register(self):
        """Test inverter has temperature register"""
        inverter = SolaredgeInverter(id=1)
        assert "i_temp_sink" in inverter.registers

    def test_inverter_has_status_registers(self):
        """Test inverter has status registers"""
        inverter = SolaredgeInverter(id=1)
        assert "i_status" in inverter.registers
        assert "i_status_vendor" in inverter.registers

    def test_inverter_ac_current_has_scale_factor(self):
        """Test AC current registers have scale factor"""
        inverter = SolaredgeInverter(id=1)
        assert inverter.registers["i_ac_currenta"].sf_key == "i_ac_current_sf"
        assert "i_ac_current_sf" in inverter.registers

    def test_inverter_registers_sorted(self):
        """Test inverter registers are properly sorted by address"""
        inverter = SolaredgeInverter(id=1)
        addresses = [reg.address for reg in inverter.registers.values()]
        assert addresses == sorted(addresses)

    def test_inverter_group_registers(self):
        """Test inverter can group registers efficiently"""
        inverter = SolaredgeInverter(id=1)
        groups = inverter.group_registers()
        assert len(groups) > 0
        # All groups should be non-empty
        assert all(len(group) > 0 for group in groups)
