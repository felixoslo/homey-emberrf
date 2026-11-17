"""EmberRF pairing uses receive-only capture or an explicitly supplied address."""
import asyncio
import re
from typing import Any
from homey.driver import Driver
from homey.pair_session import PairSession

PAIR_SIGNAL_ID = "g6r_h4t_rx"
LEARN_TIMEOUT_SECONDS = 30
REQUIRED_MATCHING_FRAMES = 3
HEX_ADDRESS = re.compile(r"^(?:0[xX])?([0-9a-fA-F]{1,5})$")


def parse_handset_address(value: Any) -> int:
    if not isinstance(value, str):
        raise ValueError("Handset address must be hexadecimal text")
    found = HEX_ADDRESS.fullmatch(value.strip())
    if not found:
        raise ValueError("Enter 1–5 hexadecimal digits, e.g. 0x12345")
    address = int(found.group(1), 16)
    if address > 0x3FFFF:
        raise ValueError("G6R address must fit in 18 bits")
    return address


def pairing_device(address: int) -> dict[str, Any]:
    if not 0 <= address <= 0x3FFFF:
        raise ValueError("Invalid G6R remote address")
    return {
        "name": "EmberRF fireplace",
        "data": {"id": f"emberrf-g6r-{address:05x}", "address": address},
    }


class EmberRFDriver(Driver):
    async def on_init(self) -> None:
        await super().on_init()
        for card_id, cmd in (
            ("send_on", "on"),
            ("send_off", "off"),
            ("send_broad", "broad"),
            ("send_narrow", "narrow"),
            ("send_flame_up", "flame_up"),
            ("send_flame_down", "flame_down"),
        ):
            card = self.homey.flow.get_action_card(card_id)

            async def on_flow(card_arguments: dict[str, Any], *, action: str = cmd, **kwargs: Any) -> None:
                device = card_arguments["device"]
                if action in ("flame_up", "flame_down"):
                    factor = card_arguments.get("factor", 1)
                    repeats = device.repetitions_for_factor(factor)
                    await device.send_command(
                        action, source=f"Flow:{action} factor={factor}",
                        repetitions=repeats,
                    )
                else:
                    await device.send_command(action, source=f"Flow:{action}")
                if action in ("on", "off"):
                    await device.set_capability_value("onoff", action == "on")

            card.register_run_listener(on_flow)
        self._sent_trigger = self.homey.flow.get_device_trigger_card("rf_accepted")
        self._error_trigger = self.homey.flow.get_device_trigger_card("rf_failed")
        self.log("EMBERRF FLOW: six explicit RF commands and two result triggers registered")

    async def trigger_rf_accepted(self, device: Any, tokens: dict[str, str]) -> None:
        await self._sent_trigger.trigger(device, tokens)

    async def trigger_rf_failed(self, device: Any, tokens: dict[str, str]) -> None:
        await self._error_trigger.trigger(device, tokens)

    async def on_pair(self, session: PairSession) -> None:
        # The handset address is unique to the user's equipment, never a value in source.
        signal = self.homey.rf.get_signal_433(PAIR_SIGNAL_ID)
        learn_lock = asyncio.Lock()
        active_task: asyncio.Task[Any] | None = None

        async def manual_address(data: Any) -> dict[str, Any]:
            if not isinstance(data, dict):
                raise ValueError("Supply a hex address in the address field")
            return pairing_device(parse_handset_address(data.get("address")))

        async def learn_remote(_data: Any = None) -> dict[str, Any]:
            nonlocal active_task
            async with learn_lock:
                active_task = asyncio.current_task()
                loop = asyncio.get_running_loop()
                matched: asyncio.Future[int] = loop.create_future()
                counts: dict[int, int] = {}
                enabled = False
                def on_payload(payload: Any, first: bool = False) -> None:
                    try:
                        if matched.done() or len(payload) != 22 or any(b not in (0,1) for b in payload):
                            return
                        address = int("".join(str(x) for x in payload[:18]), 2)
                        cmd = "".join(str(x) for x in payload[18:])
                        if cmd not in ("1001", "1011", "1010", "1101", "1110"):
                            return
                        counts[address] = counts.get(address, 0) + 1
                        if counts[address] >= REQUIRED_MATCHING_FRAMES:
                            matched.set_result(address)
                    except Exception as exc:
                        self.error(f"EMBERRF PAIR: invalid RF frame ignored: {exc}")
                signal.on_payload(on_payload)
                try:
                    await signal.enable_rx()
                    enabled = True
                    self.log("EMBERRF PAIR: receive-only scan started, up to 30 seconds")
                    address = await asyncio.wait_for(matched, timeout=LEARN_TIMEOUT_SECONDS)
                    self.log("EMBERRF PAIR: compatible handset found")
                    return pairing_device(address)
                except TimeoutError as exc:
                    raise RuntimeError("No compatible 433 MHz G6R frame detected. Try closer to the Homey antenna, or enter the address manually.") from exc
                finally:
                    if enabled:
                        try:
                            await signal.disable_rx()
                        except Exception as exc:
                            self.error(f"EMBERRF PAIR: disable receive failed: {exc}")
                    signal.remove_listener("payload", on_payload)
                    active_task = None

        async def disconnect(_data: Any = None) -> None:
            nonlocal active_task
            if active_task is not None and not active_task.done():
                active_task.cancel()

        session.set_handler("learn_remote", learn_remote)
        session.set_handler("manual_address", manual_address)
        session.set_handler("disconnect", disconnect)


homey_export = EmberRFDriver
