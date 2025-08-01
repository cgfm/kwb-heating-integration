"""Modbus client for KWB heating systems."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import MODBUS_FUNCTION_CODES, ERROR_CONNECTION, ERROR_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class KWBModbusClient:
    """Modbus client for KWB heating systems."""

    def __init__(self, host: str, port: int = 502, slave_id: int = 1):
        """Initialize the Modbus client."""
        self.host = host
        self.port = port
        self.slave_id = slave_id
        self._client: AsyncModbusTcpClient | None = None
        self._connected = False
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """Connect to the Modbus device."""
        async with self._lock:
            if self._connected:
                return

            try:
                self._client = AsyncModbusTcpClient(
                    host=self.host,
                    port=self.port,
                    timeout=10,
                )
                
                connection_result = await self._client.connect()
                if connection_result:
                    self._connected = True
                    _LOGGER.info("Connected to KWB heating system at %s:%d", self.host, self.port)
                else:
                    _LOGGER.error("Failed to establish connection to %s:%d", self.host, self.port)
                    raise ConnectionError("Could not establish Modbus connection")
                
            except Exception as exc:
                _LOGGER.error("Failed to connect to %s:%d - %s", self.host, self.port, exc)
                self._connected = False
                raise

    async def disconnect(self) -> None:
        """Disconnect from the Modbus device."""
        async with self._lock:
            if self._client and self._connected:
                self._client.close()
                self._connected = False
                _LOGGER.info("Disconnected from KWB heating system")

    async def test_connection(self) -> bool:
        """Test the connection by reading a basic register."""
        try:
            # Try to read register 8192 (Software version major) as test
            result = await self.read_input_registers(8192, 1)
            return result is not None
        except Exception as exc:
            _LOGGER.error("Connection test failed: %s", exc)
            return False

    async def read_input_registers(self, address: int, count: int = 1) -> list[int] | None:
        """Read input registers (function code 04)."""
        return await self._read_registers("input", address, count)

    async def read_holding_registers(self, address: int, count: int = 1) -> list[int] | None:
        """Read holding registers (function code 03)."""
        return await self._read_registers("holding", address, count)

    async def write_single_register(self, address: int, value: int) -> bool:
        """Write a single holding register (function code 06)."""
        if not self._connected or not self._client:
            await self.connect()

        if not self._connected or not self._client:
            _LOGGER.error("Cannot establish connection to Modbus device")
            return False

        try:
            async with self._lock:
                result = await self._client.write_register(
                    address=address,
                    value=value,
                    slave=self.slave_id
                )
                
                if result.isError():
                    _LOGGER.error("Error writing register %d: %s", address, result)
                    return False
                
                return True
                
        except Exception as exc:
            _LOGGER.error("Failed to write register %d: %s", address, exc)
            return False

    async def write_multiple_registers(self, address: int, values: list[int]) -> bool:
        """Write multiple holding registers (function code 16)."""
        if not self._connected or not self._client:
            await self.connect()

        if not self._connected or not self._client:
            _LOGGER.error("Cannot establish connection to Modbus device")
            return False

        try:
            async with self._lock:
                result = await self._client.write_registers(
                    address=address,
                    values=values,
                    slave=self.slave_id
                )
                
                if result.isError():
                    _LOGGER.error("Error writing registers starting at %d: %s", address, result)
                    return False
                
                return True
                
        except Exception as exc:
            _LOGGER.error("Failed to write registers starting at %d: %s", address, exc)
            return False

    async def _read_registers(self, register_type: str, address: int, count: int) -> list[int] | None:
        """Read registers with error handling."""
        if not self._connected or not self._client:
            await self.connect()

        if not self._connected or not self._client:
            _LOGGER.error("Cannot establish connection to Modbus device")
            return None

        try:
            async with self._lock:
                if register_type == "input":
                    result = await self._client.read_input_registers(
                        address=address,
                        count=count,
                        slave=self.slave_id
                    )
                elif register_type == "holding":
                    result = await self._client.read_holding_registers(
                        address=address,
                        count=count,
                        slave=self.slave_id
                    )
                else:
                    raise ValueError(f"Invalid register type: {register_type}")

                if result.isError():
                    _LOGGER.error("Error reading %s registers at %d: %s", register_type, address, result)
                    return None

                return result.registers

        except Exception as exc:
            _LOGGER.error("Failed to read %s registers at %d: %s", register_type, address, exc)
            # Try to reconnect on next call
            self._connected = False
            return None

    async def read_batch_registers(self, registers: list[dict]) -> dict[int, Any]:
        """Read multiple registers in batches for efficiency."""
        results = {}
        
        # Group registers by type and create continuous ranges
        input_registers = []
        holding_registers = []
        
        for reg in registers:
            data_type = reg.get("data_type", "")
            if "04" in data_type:  # Input registers (read-only)
                input_registers.append(reg)
            elif "03" in data_type:  # Holding registers (read-write)
                holding_registers.append(reg)
        
        # Process input registers
        if input_registers:
            results.update(await self._read_register_batch(input_registers, "input"))
        
        # Process holding registers
        if holding_registers:
            results.update(await self._read_register_batch(holding_registers, "holding"))
        
        return results

    async def _read_register_batch(self, registers: list[dict], register_type: str) -> dict[int, Any]:
        """Read a batch of registers of the same type."""
        results = {}
        
        # Sort registers by address
        sorted_registers = sorted(registers, key=lambda x: x["starting_address"])
        
        # Read registers individually or in small batches to avoid Modbus limits
        for reg in sorted_registers:
            address = reg["starting_address"]
            
            try:
                if register_type == "input":
                    values = await self.read_input_registers(address, 1)
                else:
                    values = await self.read_holding_registers(address, 1)
                
                if values and len(values) > 0:
                    results[address] = values[0]
                    _LOGGER.debug("Read register %d: %d", address, values[0])
                else:
                    _LOGGER.debug("No data for register %d", address)
                    
            except Exception as exc:
                _LOGGER.warning("Failed to read register %d: %s", address, exc)
                continue
        
        return results
