from .register import HoldingRegister

import logging

logger = logging.getLogger(__name__)


class SolaredgeDevice:
    """
    Class containing logic common to all supported solaredge devices
    """

    id: int
    offset: int
    registers: list[HoldingRegister]

    def __init__(self, id: int, offset: int = 0):
        self.id = id
        self.offset = offset
        self.registers = {}

    def group_registers(
        self, max_read_length: int = 120
    ) -> list[list[HoldingRegister]]:
        """
        Groups registers into contiguous blocks based on:
        1. Adjacency (address + length == next_address)
        2. Identical Data Type
        3. Identical Word Order
        4. Maximum aggregate length (max_read_length)
        """
        if not self.registers:
            return []

        # 1. Ensure registers are sorted by their hexadecimal address
        sorted_regs = sorted(self.registers.values(), key=lambda r: r.address)

        groups = []
        current_group = [sorted_regs[0]]
        current_group_length = sorted_regs[0].length

        for next_reg in sorted_regs[1:]:
            last_reg = current_group[-1]

            # Logic Checks
            is_adjacent = (last_reg.address + last_reg.length) == next_reg.address
            is_same_type = last_reg.data_type == next_reg.data_type
            is_same_order = last_reg.word_order == next_reg.word_order

            # Length Check: Will adding this register exceed our Modbus limit?
            fits_in_limit = (current_group_length + next_reg.length) <= max_read_length

            if is_adjacent and is_same_type and is_same_order and fits_in_limit:
                current_group.append(next_reg)
                current_group_length += next_reg.length
            else:
                # Start a new block
                groups.append(current_group)
                current_group = [next_reg]
                current_group_length = next_reg.length

        # Close the final group
        groups.append(current_group)

        return groups

    async def read_groups(self, client):
        """
        Executes bulk Modbus reads based on grouped registers and
        stores/returns the decoded values.
        """
        groups = self.group_registers()
        decoded_data = {}

        for group in groups:
            start_addr = group[0].address
            # Total registers to read is the sum of lengths in this contiguous block
            total_count = sum(reg.length for reg in group)

            try:
                # Execute the bulk read
                response = await client.read_holding_registers(
                    address=start_addr, count=total_count, device_id=self.id
                )

            except Exception as e:
                logging.error(f"Failed to read group at {hex(start_addr)}: {e}")
                continue

            if response.isError():
                logger.error(
                    f"Modbus Error reading group starting at {hex(start_addr)}: {response}"
                )
                continue

            # response.registers is a list of 16-bit integers
            raw_buffer = response.registers
            # Now, slice the buffer and assign it back to each register object
            cursor = 0
            for reg in group:
                # Extract the specific registers belonging to this 'HoldingRegister'
                register_slice = raw_buffer[cursor : cursor + reg.length]
                value = reg.decode(register_slice)
                # Store by label or key
                key = reg.label if reg.label else f"reg_{hex(reg.address)}"
                decoded_data[key] = value
                cursor += reg.length
        return decoded_data
