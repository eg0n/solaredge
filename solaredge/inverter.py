from .device import SolaredgeDevice
from .register import HoldingRegister
from pymodbus.client.mixin import ModbusClientMixin as mcm

import logging

logger = logging.getLogger(__name__)


class SolaredgeInverter(SolaredgeDevice):
    def __init__(self, id: int, offset: int = 0):
        super().__init__(id, offset)
        self.registers = {
            "c_manufacturer": HoldingRegister(
                0x9C44, mcm.DATATYPE.STRING, self, 16, "big", "Manufacturer", None
            ),
            "c_model": HoldingRegister(
                0x9C54, mcm.DATATYPE.STRING, self, 16, "big", "Model", None
            ),
            "c_version": HoldingRegister(
                0x9C6C, mcm.DATATYPE.STRING, self, 8, "big", "Version", None
            ),
            "c_serialnumber": HoldingRegister(
                0x9C74, mcm.DATATYPE.STRING, self, 16, "big", "Serial Number", None
            ),
            "c_deviceaddress": HoldingRegister(
                0x9C84, mcm.DATATYPE.UINT16, self, 1, "big", "Device Address", None
            ),
            "c_sunspec_did": HoldingRegister(
                0x9C85, mcm.DATATYPE.UINT16, self, 1, "big", "SunSpec DID", None
            ),
            "c_sunspec_length": HoldingRegister(
                0x9C86, mcm.DATATYPE.UINT16, self, 1, "big", "SunSpec Length", None
            ),
            "i_ac_current": HoldingRegister(
                0x9C87, mcm.DATATYPE.UINT16, self, 1, "big", "AC Current", "A"
            ),
            "i_ac_currenta": HoldingRegister(
                0x9C88, mcm.DATATYPE.UINT16, self, 1, "big", "AC Current Phase A", "A"
            ),
            "i_ac_currentb": HoldingRegister(
                0x9C89, mcm.DATATYPE.UINT16, self, 1, "big", "AC Current Phase B", "A"
            ),
            "i_ac_currentc": HoldingRegister(
                0x9C8A, mcm.DATATYPE.UINT16, self, 1, "big", "AC Current Phase C", "A"
            ),
            "i_ac_current_sf": HoldingRegister(
                0x9C8B,
                mcm.DATATYPE.INT16,
                self,
                1,
                "big",
                "AC Current Scale Factor",
                None,
            ),
            "i_ac_voltageab": HoldingRegister(
                0x9C8C, mcm.DATATYPE.UINT16, self, 1, "big", "AC Voltage Phase AB", "V"
            ),
            "i_ac_voltagebc": HoldingRegister(
                0x9C8D, mcm.DATATYPE.UINT16, self, 1, "big", "AC Voltage Phase BC", "V"
            ),
            "i_ac_voltageca": HoldingRegister(
                0x9C8E, mcm.DATATYPE.UINT16, self, 1, "big", "AC Voltage Phase CA", "V"
            ),
            "i_ac_voltagean": HoldingRegister(
                0x9C8F, mcm.DATATYPE.UINT16, self, 1, "big", "AC Voltage Phase AN", "V"
            ),
            "i_ac_voltagebn": HoldingRegister(
                0x9C90, mcm.DATATYPE.UINT16, self, 1, "big", "AC Voltage Phase BN", "V"
            ),
            "i_ac_voltagecn": HoldingRegister(
                0x9C91, mcm.DATATYPE.UINT16, self, 1, "big", "AC Voltage Phase CN", "V"
            ),
            "i_ac_voltage_sf": HoldingRegister(
                0x9C92,
                mcm.DATATYPE.INT16,
                self,
                1,
                "big",
                "AC Voltage Scale Factor",
                None,
            ),
            "i_ac_power": HoldingRegister(
                0x9C93, mcm.DATATYPE.INT16, self, 1, "big", "AC Power", "W"
            ),
            "i_ac_power_sf": HoldingRegister(
                0x9C94,
                mcm.DATATYPE.INT16,
                self,
                1,
                "big",
                "AC Power Scale Factor",
                None,
            ),
            "i_ac_frequency": HoldingRegister(
                0x9C95, mcm.DATATYPE.UINT16, self, 1, "big", "AC Frequency", "Hz"
            ),
            "i_ac_frequency_sf": HoldingRegister(
                0x9C96,
                mcm.DATATYPE.INT16,
                self,
                1,
                "big",
                "AC Frequency Scale Factor",
                None,
            ),
            "i_ac_va": HoldingRegister(
                0x9C97, mcm.DATATYPE.INT16, self, 1, "big", "AC VA", "VA"
            ),
            "i_ac_va_sf": HoldingRegister(
                0x9C98, mcm.DATATYPE.INT16, self, 1, "big", "AC VA Scale Factor", None
            ),
            "i_ac_var": HoldingRegister(
                0x9C99, mcm.DATATYPE.INT16, self, 1, "big", "AC VAR", "VAR"
            ),
            "i_ac_var_sf": HoldingRegister(
                0x9C9A, mcm.DATATYPE.INT16, self, 1, "big", "AC VAR Scale Factor", None
            ),
            "i_ac_pf": HoldingRegister(
                0x9C9B, mcm.DATATYPE.INT16, self, 1, "big", "AC PF", "%"
            ),
            "i_ac_pf_sf": HoldingRegister(
                0x9C9C, mcm.DATATYPE.INT16, self, 1, "big", "AC PF Scale Factor", None
            ),
            "i_ac_energy_wh": HoldingRegister(
                0x9C9D, mcm.DATATYPE.INT32, self, 2, "big", "AC Energy Wh", "Wh"
            ),
            "i_ac_energy_wh_sf": HoldingRegister(
                0x9C9F,
                mcm.DATATYPE.INT16,
                self,
                1,
                "big",
                "AC Energy Wh Scale Factor",
                None,
            ),
            "i_dc_current": HoldingRegister(
                0x9CA0, mcm.DATATYPE.UINT16, self, 1, "big", "DC Current", "A"
            ),
            "i_dc_current_sf": HoldingRegister(
                0x9CA1,
                mcm.DATATYPE.INT16,
                self,
                1,
                "big",
                "DC Current Scale Factor",
                None,
            ),
            "i_dc_voltage": HoldingRegister(
                0x9CA2, mcm.DATATYPE.UINT16, self, 1, "big", "DC Voltage", "V"
            ),
            "i_dc_voltage_sf": HoldingRegister(
                0x9CA3,
                mcm.DATATYPE.INT16,
                self,
                1,
                "big",
                "DC Voltage Scale Factor",
                None,
            ),
            "i_dc_power": HoldingRegister(
                0x9CA4, mcm.DATATYPE.INT16, self, 1, "big", "DC Power", "W"
            ),
            "i_dc_power_sf": HoldingRegister(
                0x9CA5,
                mcm.DATATYPE.INT16,
                self,
                1,
                "big",
                "DC Power Scale Factor",
                None,
            ),
            "i_temp_sink": HoldingRegister(
                0x9CA7,
                mcm.DATATYPE.INT16,
                self,
                1,
                "big",
                "Heat Sink Temperature",
                "°C",
            ),
            "i_temp_sf": HoldingRegister(
                0x9CAA,
                mcm.DATATYPE.INT16,
                self,
                1,
                "big",
                "Heat Sink Temperature Scale Factor",
                None,
            ),
            "i_status": HoldingRegister(
                0x9CAB, mcm.DATATYPE.UINT16, self, 1, "big", "Status", None
            ),
            "i_status_vendor": HoldingRegister(
                0x9CAC, mcm.DATATYPE.UINT16, self, 1, "big", "Status Vendor", None
            ),
        }
