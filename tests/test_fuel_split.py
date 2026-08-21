"""Focused tests for shared pellet/log-wood energy accounting."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import sys
import types
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_ROOT = PROJECT_ROOT / "custom_components" / "kwb_heating"


def _load_fuel_split_module():
    package_name = "kwb_fuel_split_test_package"
    package = types.ModuleType(package_name)
    package.__path__ = [str(INTEGRATION_ROOT)]
    sys.modules[package_name] = package
    for module_name in ("register_utils", "fuel_split"):
        qualified_name = f"{package_name}.{module_name}"
        spec = importlib.util.spec_from_file_location(
            qualified_name, INTEGRATION_ROOT / f"{module_name}.py"
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Could not load {module_name}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified_name] = module
        spec.loader.exec_module(module)
    return sys.modules[f"{package_name}.fuel_split"]


fuel_split = _load_fuel_split_module()


class MutableClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def advance(self, seconds: float) -> None:
        self.value += timedelta(seconds=seconds)

    def __call__(self) -> datetime:
        return self.value


class FakeStore:
    def __init__(self, data=None) -> None:
        self.data = data
        self.delay_calls = 0
        self.save_calls = 0
        self.pending = None

    async def async_load(self):
        return self.data

    def async_delay_save(self, data_func, _delay=0) -> None:
        self.delay_calls += 1
        self.pending = data_func

    async def async_save(self, data) -> None:
        self.save_calls += 1
        self.data = data


class FailingLoadStore(FakeStore):
    async def async_load(self):
        raise ValueError("corrupt storage")


class FakeCoordinator:
    def __init__(self) -> None:
        self.data = {}
        self.listeners = []
        self.last_update_success = True

    def async_add_listener(self, listener):
        self.listeners.append(listener)

        def remove_listener():
            if listener in self.listeners:
                self.listeners.remove(listener)

        return remove_listener

    def update(self, total, mode=...):
        if total is ...:
            self.data.pop(100, None)
        else:
            self.data[100] = {"value": total}
        if mode is ...:
            self.data.pop(200, None)
        else:
            self.data[200] = {"raw_value": mode}
        for listener in tuple(self.listeners):
            listener()


class FuelSplitTrackerTests(unittest.TestCase):
    def make_tracker(self, total, mode, *, store=None, clock=None):
        coordinator = FakeCoordinator()
        coordinator.update(total, mode)
        store = store or FakeStore()
        clock = clock or MutableClock()
        tracker = fuel_split.FuelSplitTracker(
            coordinator,
            store,
            total_address=100,
            mode_address=200,
            expected_interval_seconds=30,
            now=clock,
        )
        asyncio.run(tracker.async_initialize())
        return tracker, coordinator, store, clock

    @staticmethod
    def advance(coordinator, clock, total, mode=..., seconds=30):
        clock.advance(seconds)
        coordinator.update(total, mode)

    def test_first_observation_only_establishes_baseline(self) -> None:
        tracker, _coordinator, _store, _clock = self.make_tracker(10000.0, 2)
        self.assertEqual((0, 0, 0), (
            tracker.pellet_kwh,
            tracker.log_wood_kwh,
            tracker.unattributed_kwh,
        ))
        self.assertEqual(10000.0, tracker.state.last_source_total_kwh)
        self.assertEqual(10000.0, tracker.state.source_total_at_start)
        self.assertIsNotNone(tracker.state.tracking_started_at)

    def test_normal_pellet_accumulation(self) -> None:
        tracker, coordinator, _store, clock = self.make_tracker(100.0, 2)
        self.advance(coordinator, clock, 100.2, 2)
        self.advance(coordinator, clock, 100.5, 2)
        self.assertAlmostEqual(0.5, tracker.pellet_kwh)
        self.assertEqual(0, tracker.log_wood_kwh)
        self.assertEqual(0, tracker.unattributed_kwh)

    def test_log_wood_raw_modes_share_one_fuel_group(self) -> None:
        tracker, coordinator, _store, clock = self.make_tracker(100.0, 1)
        self.advance(coordinator, clock, 100.2, 1)
        self.advance(coordinator, clock, 100.5, 3)
        self.advance(coordinator, clock, 100.8, 3)
        self.assertAlmostEqual(0.8, tracker.log_wood_kwh)
        self.assertEqual(0, tracker.unattributed_kwh)

    def test_fuel_switch_interval_is_unattributed_once(self) -> None:
        tracker, coordinator, _store, clock = self.make_tracker(100.0, 2)
        self.advance(coordinator, clock, 100.2, 2)
        self.advance(coordinator, clock, 100.4, 1)
        self.advance(coordinator, clock, 100.7, 1)
        self.assertAlmostEqual(0.2, tracker.pellet_kwh)
        self.assertAlmostEqual(0.3, tracker.log_wood_kwh)
        self.assertAlmostEqual(0.2, tracker.unattributed_kwh)
        self.assertAlmostEqual(100.7, tracker.state.last_source_total_kwh)

    def test_nonfuel_unknown_and_missing_modes_are_unattributed(self) -> None:
        tracker, coordinator, _store, clock = self.make_tracker(100.0, 0)
        for total, mode in ((100.1, 0), (100.2, 4), (100.3, 99), (100.4, ...)):
            self.advance(coordinator, clock, total, mode)
        self.assertAlmostEqual(0.4, tracker.unattributed_kwh)
        self.assertEqual(0, tracker.pellet_kwh)
        self.assertEqual(0, tracker.log_wood_kwh)

    def test_zero_delta_advances_mode_baseline(self) -> None:
        tracker, coordinator, _store, clock = self.make_tracker(100.0, 2)
        self.advance(coordinator, clock, 100.0, 1)
        self.advance(coordinator, clock, 100.3, 1)
        self.assertAlmostEqual(0.3, tracker.log_wood_kwh)
        self.assertEqual(0, tracker.unattributed_kwh)

    def test_source_reset_never_decreases_derived_totals(self) -> None:
        tracker, coordinator, _store, clock = self.make_tracker(1000.0, 2)
        observations = []
        for total in (1000.4, 0.0, 0.3):
            self.advance(coordinator, clock, total, 2)
            observations.append(tracker.pellet_kwh)
        self.assertAlmostEqual(0.7, tracker.pellet_kwh)
        self.assertEqual(1, tracker.state.source_reset_count)
        self.assertEqual(sorted(observations), observations)

    def test_invalid_source_total_does_not_corrupt_baseline(self) -> None:
        tracker, coordinator, _store, clock = self.make_tracker(100.0, 2)
        for invalid in (None, "bad", float("nan"), float("inf")):
            self.advance(coordinator, clock, invalid, 1)
        self.assertEqual(100.0, tracker.state.last_source_total_kwh)
        self.advance(coordinator, clock, 100.5, 1)
        self.assertAlmostEqual(0.5, tracker.unattributed_kwh)

    def test_restart_restores_totals_and_baseline_metadata(self) -> None:
        tracker, coordinator, store, clock = self.make_tracker(100.0, 2)
        self.advance(coordinator, clock, 100.2, 2)
        self.advance(coordinator, clock, 100.4, 1)
        asyncio.run(tracker.async_shutdown())
        self.assertEqual([], coordinator.listeners)
        self.assertEqual(1, store.save_calls)

        restored_coordinator = FakeCoordinator()
        restored_coordinator.update(100.4, 1)
        restored = fuel_split.FuelSplitTracker(
            restored_coordinator, store, 100, 200, 30, now=clock
        )
        asyncio.run(restored.async_initialize())
        self.assertAlmostEqual(0.2, restored.pellet_kwh)
        self.assertAlmostEqual(0.2, restored.unattributed_kwh)
        self.assertEqual(100.4, restored.state.last_source_total_kwh)
        self.assertEqual(1, len(restored_coordinator.listeners))

    def test_long_restart_gap_is_unattributed(self) -> None:
        tracker, _coordinator, store, clock = self.make_tracker(100.0, 2)
        asyncio.run(tracker.async_shutdown())
        clock.advance(91)
        coordinator = FakeCoordinator()
        coordinator.update(105.0, 2)
        restored = fuel_split.FuelSplitTracker(
            coordinator, store, 100, 200, 30, now=clock
        )
        asyncio.run(restored.async_initialize())
        self.assertEqual(0, restored.pellet_kwh)
        self.assertAlmostEqual(5.0, restored.unattributed_kwh)

    def test_failed_polls_do_not_hide_a_long_observation_gap(self) -> None:
        tracker, coordinator, _store, clock = self.make_tracker(100.0, 2)
        coordinator.last_update_success = False
        for _ in range(4):
            self.advance(coordinator, clock, 100.0, 2)
        coordinator.last_update_success = True
        self.advance(coordinator, clock, 105.0, 2)
        self.assertEqual(0, tracker.pellet_kwh)
        self.assertAlmostEqual(5.0, tracker.unattributed_kwh)

    def test_short_reload_gap_allows_same_fuel_attribution(self) -> None:
        tracker, _coordinator, store, clock = self.make_tracker(100.0, 2)
        asyncio.run(tracker.async_shutdown())
        clock.advance(10)
        coordinator = FakeCoordinator()
        coordinator.update(101.0, 2)
        restored = fuel_split.FuelSplitTracker(
            coordinator, store, 100, 200, 30, now=clock
        )
        asyncio.run(restored.async_initialize())
        self.assertAlmostEqual(1.0, restored.pellet_kwh)
        self.assertEqual(0, restored.unattributed_kwh)

    def test_three_entity_listeners_do_not_multiply_delta(self) -> None:
        tracker, coordinator, _store, clock = self.make_tracker(100.0, 2)
        notifications = [0, 0, 0]
        for index in range(3):
            tracker.async_add_listener(
                lambda index=index: notifications.__setitem__(
                    index, notifications[index] + 1
                )
            )
        self.advance(coordinator, clock, 101.0, 2)
        self.assertAlmostEqual(1.0, tracker.pellet_kwh)
        self.assertEqual([1, 1, 1], notifications)

    def test_accounting_continues_without_entity_listeners(self) -> None:
        tracker, coordinator, _store, clock = self.make_tracker(100.0, 2)
        self.advance(coordinator, clock, 101.0, 2)
        self.assertAlmostEqual(1.0, tracker.pellet_kwh)

    def test_duplicate_observation_does_not_change_totals(self) -> None:
        tracker, coordinator, _store, clock = self.make_tracker(100.0, 2)
        self.advance(coordinator, clock, 101.0, 2)
        self.advance(coordinator, clock, 101.0, 2, seconds=0)
        self.assertAlmostEqual(1.0, tracker.pellet_kwh)

    def test_malformed_persisted_state_is_conservative(self) -> None:
        tracker, _coordinator, _store, _clock = self.make_tracker(
            100.0, 2, store=FakeStore({"pellet_kwh": "bad", "source_reset_count": {}})
        )
        self.assertEqual(0, tracker.pellet_kwh)
        self.assertEqual(100.0, tracker.state.last_source_total_kwh)

    def test_storage_load_failure_does_not_break_initialization(self) -> None:
        with self.assertLogs(fuel_split.__name__, "WARNING"):
            tracker, _coordinator, _store, _clock = self.make_tracker(
                100.0, 2, store=FailingLoadStore()
            )
        self.assertEqual(100.0, tracker.state.last_source_total_kwh)
        self.assertEqual(0, tracker.pellet_kwh)

    def test_poll_updates_use_delayed_storage_and_unload_flushes(self) -> None:
        tracker, coordinator, store, clock = self.make_tracker(100.0, 2)
        for step in range(1, 10):
            self.advance(coordinator, clock, 100.0 + step / 10, 2)
        self.assertEqual(1, store.delay_calls)
        self.advance(coordinator, clock, 101.0, 2)
        self.assertEqual(2, store.delay_calls)
        self.assertEqual(0, store.save_calls)
        asyncio.run(tracker.async_shutdown())
        self.assertEqual(1, store.save_calls)


class FuelSplitCapabilityTests(unittest.TestCase):
    @staticmethod
    def register(parameter, address):
        return {"parameter": parameter, "starting_address": address}

    def test_both_parameters_enable_capability_with_actual_addresses(self) -> None:
        registers = [
            self.register(fuel_split.TOTAL_HEAT_PARAMETER, "9000"),
            self.register(fuel_split.FUEL_MODE_PARAMETER, 9100),
        ]
        self.assertEqual(
            (9000, 9100), fuel_split.get_fuel_split_register_addresses(registers)
        )

    def test_either_missing_parameter_disables_capability(self) -> None:
        total = self.register(fuel_split.TOTAL_HEAT_PARAMETER, 100)
        mode = self.register(fuel_split.FUEL_MODE_PARAMETER, 200)
        self.assertIsNone(fuel_split.get_fuel_split_register_addresses([total]))
        self.assertIsNone(fuel_split.get_fuel_split_register_addresses([mode]))

    def test_device_name_is_not_part_of_capability_detection(self) -> None:
        registers = [
            self.register(fuel_split.TOTAL_HEAT_PARAMETER, 100),
            self.register(fuel_split.FUEL_MODE_PARAMETER, 200),
        ]
        self.assertEqual(
            (100, 200), fuel_split.get_fuel_split_register_addresses(registers)
        )

    def test_storage_identity_is_language_independent(self) -> None:
        self.assertEqual(
            fuel_split.fuel_split_storage_key("entry-1"),
            fuel_split.fuel_split_storage_key("entry-1"),
        )
        self.assertNotEqual(
            fuel_split.fuel_split_storage_key("entry-1"),
            fuel_split.fuel_split_storage_key("entry-2"),
        )

    def test_central_raw_mode_mapping(self) -> None:
        expected = {
            0: "none",
            1: "log_wood",
            2: "pellets",
            3: "log_wood",
            4: "none",
            99: "unknown",
            None: "unknown",
        }
        self.assertEqual(
            expected,
            {
                raw: fuel_split.fuel_group_for_raw_mode(raw)[1]
                for raw in expected
            },
        )


if __name__ == "__main__":
    unittest.main()
