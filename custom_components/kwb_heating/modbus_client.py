"""Modbus client for KWB heating systems."""
from __future__ import annotations

import asyncio
import logging
from typing import Any
import inspect

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
        self._unit_kwarg: str = "unit"  # will be auto-detected on connect

    async def _invoke_with_unit_kwarg(self, method_name: str, *args):
        """Call a pymodbus client method with unit/slave in a version-agnostic way.

        1) Try positional unit/slave as last arg (most compatible)
        2) Try keyword 'unit'
        3) Try keyword 'slave'
        Caches the working keyword for later debug logging.
        """
        if not self._client:
            raise ConnectionError("Modbus client is not initialized")

        method = getattr(self._client, method_name)

        # 1) Positional attempt
        try:
            res_pos = await method(*args, self.slave_id)
            _LOGGER.debug("pymodbus call %s used positional unit arg", method_name)
            return res_pos
        except TypeError as e_pos:
            # 2) Keyword 'unit'
            try:
                res = await method(*args, unit=self.slave_id)
                self._unit_kwarg = "unit"
                _LOGGER.info("pymodbus call %s works with kwarg 'unit'", method_name)
                return res
            except TypeError as e_unit:
                # 3) Keyword 'slave'
                try:
                    res2 = await method(*args, slave=self.slave_id)
                    self._unit_kwarg = "slave"
                    _LOGGER.info("pymodbus call %s works with kwarg 'slave'", method_name)
                    return res2
                except TypeError:
                    # Re-raise the first error for clearer context
                    raise e_pos

    async def _invoke_read(self, method_name: str, *, address: int, count: int):
        """Call a pymodbus read method in a version-agnostic way.

        Prefer keyword parameters for count and unit/slave to support
        versions that enforce keyword-only arguments.
        """
        if not self._client:
            raise ConnectionError("Modbus client is not initialized")

        method = getattr(self._client, method_name)

        # Try unit kwarg
        try:
            res = await method(address, count=count, unit=self.slave_id)
            self._unit_kwarg = "unit"
            return res
        except TypeError as e_unit:
            # Try slave kwarg
            try:
                res2 = await method(address, count=count, slave=self.slave_id)
                self._unit_kwarg = "slave"
                return res2
            except TypeError as e_slave:
                # Try without unit/slave
                try:
                    res3 = await method(address, count=count)
                    return res3
                except TypeError:
                    # As last resort, try positional count only
                    try:
                        res4 = await method(address, count)
                        return res4
                    except TypeError:
                        # Propagate the earliest informative error
                        raise e_unit

    async def connect(self) -> None:
        """Connect to the Modbus device."""
        async with self._lock:
            if self._connected:
                return

            try:
                # Close any previous client to avoid leaking sockets
                if self._client is not None:
                    try:
                        close_result = self._client.close()
                        if asyncio.iscoroutine(close_result):
                            await close_result
                    except Exception:
                        pass
                    self._client = None

                self._client = AsyncModbusTcpClient(
                    host=self.host,
                    port=self.port,
                    timeout=10,
                )

                connection_result = await self._client.connect()
                if connection_result:
                    self._connected = True
                    _LOGGER.info("Connected to KWB heating system at %s:%d", self.host, self.port)
                    # Detect correct kwarg name for unit/slave depending on pymodbus version
                    try:
                        sig = inspect.signature(self._client.read_holding_registers)
                        if "unit" in sig.parameters:
                            self._unit_kwarg = "unit"
                        elif "slave" in sig.parameters:
                            self._unit_kwarg = "slave"
                        else:
                            # Fallback to unit
                            self._unit_kwarg = "unit"
                        _LOGGER.debug("Using pymodbus kwarg '%s' for unit id", self._unit_kwarg)
                    except Exception:
                        self._unit_kwarg = "unit"
                else:
                    _LOGGER.error("Failed to establish connection to %s:%d", self.host, self.port)
                    # Ensure client is closed on failure
                    try:
                        close_result = self._client.close()
                        if asyncio.iscoroutine(close_result):
                            await close_result
                    except Exception:
                        pass
                    self._client = None
                    self._connected = False
                    raise ConnectionError("Could not establish Modbus connection")

            except Exception as exc:
                _LOGGER.error("Failed to connect to %s:%d - %s", self.host, self.port, exc)
                # Ensure we don't keep a half-open client
                if self._client is not None:
                    try:
                        close_result = self._client.close()
                        if asyncio.iscoroutine(close_result):
                            await close_result
                    except Exception:
                        pass
                    self._client = None
                self._connected = False
                raise

    async def disconnect(self) -> None:
        """Disconnect from the Modbus device."""
        async with self._lock:
            if self._client and self._connected:
                try:
                    close_result = self._client.close()
                    if asyncio.iscoroutine(close_result):
                        await close_result
                finally:
                    self._connected = False
                    self._client = None
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
                result = await self._invoke_with_unit_kwarg(
                    "write_register", address, value
                )
                
                if result.isError():
                    _LOGGER.error("Error writing register %d: %s", address, result)
                    return False
                
                return True
                
        except Exception as exc:
            _LOGGER.error("Failed to write register %d: %s", address, exc)
            # Close client on failure to avoid leaks and reconnect next time
            try:
                if self._client is not None:
                    close_result = self._client.close()
                    if asyncio.iscoroutine(close_result):
                        await close_result
            except Exception:
                pass
            self._client = None
            self._connected = False
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
                result = await self._invoke_with_unit_kwarg(
                    "write_registers", address, values
                )
                
                if result.isError():
                    _LOGGER.error("Error writing registers starting at %d: %s", address, result)
                    return False
                
                return True
                
        except Exception as exc:
            _LOGGER.error("Failed to write registers starting at %d: %s", address, exc)
            # Close client on failure to avoid leaks and reconnect next time
            try:
                if self._client is not None:
                    close_result = self._client.close()
                    if asyncio.iscoroutine(close_result):
                        await close_result
            except Exception:
                pass
            self._client = None
            self._connected = False
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
                    result = await self._invoke_read(
                        "read_input_registers", address=address, count=count
                    )
                elif register_type == "holding":
                    result = await self._invoke_read(
                        "read_holding_registers", address=address, count=count
                    )
                else:
                    raise ValueError(f"Invalid register type: {register_type}")

                if result.isError():
                    _LOGGER.error("Error reading %s registers at %d: %s", register_type, address, result)
                    return None

                return result.registers

        except Exception as exc:
            _LOGGER.error("Failed to read %s registers at %d: %s", register_type, address, exc)
            # Close client to avoid leaks and reconnect on next call
            try:
                if self._client is not None:
                    close_result = self._client.close()
                    if asyncio.iscoroutine(close_result):
                        await close_result
            except Exception:
                pass
            self._client = None
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
            
            # Determine count based on data type (u32/s32 need 2 registers)
            data_type = reg.get("unit", "u16")
            count = 2 if data_type in ["u32", "s32"] else 1
            
            try:
                if register_type == "input":
                    values = await self.read_input_registers(address, count)
                else:
                    values = await self.read_holding_registers(address, count)
                
                if values and len(values) > 0:
                    if count == 2 and len(values) >= 2:
                        # Combine two 16-bit registers into one 32-bit value
                        combined_value = (values[0] << 16) | values[1]
                        results[address] = combined_value
                        _LOGGER.debug("Read 32-bit register %d: %d", address, combined_value)
                    else:
                        results[address] = values[0]
                        _LOGGER.debug("Read register %d: %d", address, values[0])
                else:
                    _LOGGER.debug("No data for register %d", address)
                    
            except Exception as exc:
                _LOGGER.warning("Failed to read register %d: %s", address, exc)
                continue
        
        return results
