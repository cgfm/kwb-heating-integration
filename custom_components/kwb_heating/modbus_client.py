"""Modbus client for KWB heating systems."""
from __future__ import annotations

import asyncio
import logging
from typing import Any
import inspect

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    CONNECTION_TYPE_TCP,
    CONNECTION_TYPE_SERIAL,
    DEFAULT_BAUDRATE,
    DEFAULT_PARITY,
    DEFAULT_STOPBITS,
    DEFAULT_BYTESIZE,
)

_LOGGER = logging.getLogger(__name__)


class KWBModbusClient:
    """Modbus client for KWB heating systems."""

    def __init__(
        self,
        host: str | None = None,
        port: int = 502,
        slave_id: int = 1,
        connection_type: str = CONNECTION_TYPE_TCP,
        serial_port: str | None = None,
        baudrate: int = DEFAULT_BAUDRATE,
        parity: str = DEFAULT_PARITY,
        stopbits: int = DEFAULT_STOPBITS,
        bytesize: int = DEFAULT_BYTESIZE,
    ):
        """Initialize the Modbus client."""
        self.connection_type = connection_type
        self.host = host
        self.port = port
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.parity = parity
        self.stopbits = stopbits
        self.bytesize = bytesize
        self.slave_id = slave_id
        self._client: Any = None
        self._connected = False
        self._lock = asyncio.Lock()
        self._unit_kwarg: str = "unit"  # will be auto-detected on connect

    @property
    def is_connected(self) -> bool:
        """Return True if the client is connected to the Modbus device."""
        return self._connected

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

    async def _invoke_write(self, method_name: str, *, address: int, value: Any):
        """Call a pymodbus write method in a version-agnostic way.

        Always pass address and value(s) positionally, and unit/slave as keyword.
        Falls back between 'unit' and 'slave', and finally no unit (if not supported).
        """
        if not self._client:
            raise ConnectionError("Modbus client is not initialized")

        method = getattr(self._client, method_name)

        # Try with 'unit'
        try:
            res = await method(address, value, unit=self.slave_id)
            self._unit_kwarg = "unit"
            return res
        except TypeError as e_unit:
            # Try with 'slave'
            try:
                res2 = await method(address, value, slave=self.slave_id)
                self._unit_kwarg = "slave"
                return res2
            except TypeError:
                # Try without unit/slave
                try:
                    res3 = await method(address, value)
                    return res3
                except TypeError:
                    raise e_unit

    @property
    def _connection_label(self) -> str:
        """Return a human-readable label for the current connection."""
        if self.connection_type == CONNECTION_TYPE_SERIAL:
            return f"{self.serial_port} (RTU, {self.baudrate} baud)"
        return f"{self.host}:{self.port}"

    def _create_client(self) -> Any:
        """Create the appropriate pymodbus client based on connection type."""
        if self.connection_type == CONNECTION_TYPE_SERIAL:
            from pymodbus.client import AsyncModbusSerialClient

            return AsyncModbusSerialClient(
                port=self.serial_port,
                baudrate=self.baudrate,
                parity=self.parity,
                stopbits=self.stopbits,
                bytesize=self.bytesize,
                timeout=10,
            )
        return AsyncModbusTcpClient(
            host=self.host,
            port=self.port,
            timeout=10,
        )

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

                self._client = self._create_client()

                connection_result = await self._client.connect()
                if connection_result:
                    self._connected = True
                    _LOGGER.info("Connected to KWB heating system at %s", self._connection_label)
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
                    _LOGGER.error("Failed to establish connection to %s", self._connection_label)
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
                _LOGGER.error("Failed to connect to %s - %s", self._connection_label, exc)
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

    async def _teardown_connection(self) -> None:
        """Tear down the client connection after a transport-level error."""
        try:
            if self._client is not None:
                close_result = self._client.close()
                if asyncio.iscoroutine(close_result):
                    await close_result
        except Exception:
            pass
        self._client = None
        self._connected = False

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
                result = await self._invoke_write(
                    "write_register", address=address, value=value
                )

                if result.isError():
                    _LOGGER.error("Error writing register %d: %s", address, result)
                    return False

                return True

        except ModbusException as exc:
            _LOGGER.error("Modbus protocol error writing register %d: %s", address, exc)
            return False

        except (ConnectionError, asyncio.TimeoutError, OSError) as exc:
            _LOGGER.error("Connection error writing register %d: %s", address, exc)
            await self._teardown_connection()
            return False

        except Exception as exc:
            _LOGGER.error("Failed to write register %d: %s", address, exc)
            await self._teardown_connection()
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
                result = await self._invoke_write(
                    "write_registers", address=address, value=values
                )

                if result.isError():
                    _LOGGER.error("Error writing registers starting at %d: %s", address, result)
                    return False

                return True

        except ModbusException as exc:
            _LOGGER.error("Modbus protocol error writing registers starting at %d: %s", address, exc)
            return False

        except (ConnectionError, asyncio.TimeoutError, OSError) as exc:
            _LOGGER.error("Connection error writing registers starting at %d: %s", address, exc)
            await self._teardown_connection()
            return False

        except Exception as exc:
            _LOGGER.error("Failed to write registers starting at %d: %s", address, exc)
            await self._teardown_connection()
            return False

    async def _read_registers(self, register_type: str, address: int, count: int) -> list[int] | None:
        """Read registers with error handling (acquires lock).

        Public-facing method used by read_input_registers / read_holding_registers.
        Acquires the lock for a single read. For batch reads, use _read_registers_unlocked
        under an externally held lock instead.
        """
        if not self._connected or not self._client:
            await self.connect()

        if not self._connected or not self._client:
            _LOGGER.error("Cannot establish connection to Modbus device")
            return None

        async with self._lock:
            return await self._read_registers_unlocked(register_type, address, count)

    async def _read_registers_unlocked(self, register_type: str, address: int, count: int) -> list[int] | None:
        """Read registers without acquiring the lock (caller must hold it).

        Differentiates between protocol errors (ModbusException) and connection
        errors. Protocol errors do NOT tear down the connection, as the transport
        is still healthy.
        """
        try:
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

        except ModbusException as exc:
            _LOGGER.error(
                "Modbus protocol error reading %s registers at %d: %s",
                register_type, address, exc,
            )
            return None

        except (ConnectionError, asyncio.TimeoutError, OSError) as exc:
            _LOGGER.error(
                "Connection error reading %s registers at %d: %s",
                register_type, address, exc,
            )
            await self._teardown_connection()
            return None

        except Exception as exc:
            _LOGGER.error("Failed to read %s registers at %d: %s", register_type, address, exc)
            await self._teardown_connection()
            return None

    async def read_batch_registers(self, registers: list[dict]) -> dict[int, Any]:
        """Read multiple registers in batches for efficiency.

        Acquires the lock once for the entire batch so that all reads form an
        atomic snapshot of the device state (issue #24).
        """
        # Ensure connection before acquiring the lock
        if not self._connected or not self._client:
            await self.connect()

        if not self._connected or not self._client:
            _LOGGER.error("Cannot establish connection to Modbus device")
            return {}

        results = {}

        # Group registers by type
        input_registers = []
        holding_registers = []

        for reg in registers:
            data_type = reg.get("data_type", "")
            if "04" in data_type:
                input_registers.append(reg)
            elif "03" in data_type:
                holding_registers.append(reg)

        async with self._lock:
            if input_registers:
                results.update(await self._read_register_batch_unlocked(input_registers, "input"))
            if holding_registers:
                results.update(await self._read_register_batch_unlocked(holding_registers, "holding"))

        return results

    async def _read_register_batch_unlocked(self, registers: list[dict], register_type: str) -> dict[int, Any]:
        """Read a batch of registers using contiguous range reads (caller must hold lock).

        Groups registers into contiguous ranges (with a configurable gap tolerance)
        and reads each range with a single Modbus request.
        """
        results = {}

        # Build a list of (address, register_count, reg_dict) for each register
        address_info: list[tuple[int, int, dict]] = []
        for reg in registers:
            address = reg["starting_address"]
            data_type = reg.get("type", reg.get("unit", "u16"))
            count = 2 if data_type in ["u32", "s32"] else 1
            address_info.append((address, count, reg))

        address_info.sort(key=lambda x: x[0])
        if not address_info:
            return results

        # Group into contiguous ranges.
        MAX_GAP = 10   # max gap (in 16-bit registers) to bridge
        MAX_RANGE = 125  # Modbus protocol limit per request

        ranges: list[tuple[int, int, list[tuple[int, int, dict]]]] = []
        range_start = address_info[0][0]
        range_end = address_info[0][0] + address_info[0][1]
        range_regs: list[tuple[int, int, dict]] = [address_info[0]]

        for addr, count, reg in address_info[1:]:
            reg_end = addr + count
            if addr <= range_end + MAX_GAP and (reg_end - range_start) <= MAX_RANGE:
                range_end = max(range_end, reg_end)
                range_regs.append((addr, count, reg))
            else:
                ranges.append((range_start, range_end - range_start, range_regs))
                range_start = addr
                range_end = reg_end
                range_regs = [(addr, count, reg)]

        ranges.append((range_start, range_end - range_start, range_regs))

        _LOGGER.debug(
            "Reading %d %s registers in %d range(s) instead of %d individual reads",
            len(address_info), register_type, len(ranges), len(address_info),
        )

        for range_start, range_count, range_regs in ranges:
            try:
                values = await self._read_registers_unlocked(register_type, range_start, range_count)

                if not values or len(values) < range_count:
                    _LOGGER.warning(
                        "Incomplete data for %s range %d-%d (got %d of %d)",
                        register_type, range_start, range_start + range_count - 1,
                        len(values) if values else 0, range_count,
                    )
                    continue

                for addr, count, reg in range_regs:
                    offset = addr - range_start
                    if offset + count <= len(values):
                        if count == 2:
                            combined_value = (values[offset] << 16) | values[offset + 1]
                            results[addr] = combined_value
                            _LOGGER.debug("Read 32-bit register %d: %d", addr, combined_value)
                        else:
                            results[addr] = values[offset]
                            _LOGGER.debug("Read register %d: %d", addr, values[offset])
                    else:
                        _LOGGER.debug("No data for register %d in range response", addr)

            except Exception as exc:
                _LOGGER.warning(
                    "Failed to read %s range %d-%d (%d regs): %s. Falling back to individual reads.",
                    register_type, range_start, range_start + range_count - 1, range_count, exc,
                )
                for addr, count, reg in range_regs:
                    try:
                        ind_values = await self._read_registers_unlocked(register_type, addr, count)
                        if ind_values and len(ind_values) >= count:
                            if count == 2:
                                results[addr] = (ind_values[0] << 16) | ind_values[1]
                            else:
                                results[addr] = ind_values[0]
                    except Exception as inner_exc:
                        _LOGGER.warning("Failed to read register %d: %s", addr, inner_exc)

        return results
