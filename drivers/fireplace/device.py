import asyncio
import math
import time
from typing import Any
from homey.device import Device

# A flow factor controls the duration of a *repeated RF command*, not
# a known percentage of physical flame height.
BASE_REPETITIONS = 10
MAX_FLOW_FACTOR = 10
HOLD_BURST_REPETITIONS = 10
HOLD_MAX_SECONDS = 8.0
HOLD_HEARTBEAT_SECONDS = 1.2

def repetitions_for_factor(factor: int | float) -> int:
    if isinstance(factor, bool) or not isinstance(factor, (int, float)):
        raise ValueError("Factor must be a number from 1 to 10")
    if not math.isfinite(factor) or factor != int(factor) or not 1 <= factor <= MAX_FLOW_FACTOR:
        raise ValueError("Factor must be an integer from 1 to 10")
    return int(factor) * BASE_REPETITIONS


ADDRESS_BITS = 18
STANDARD_SIGNAL_ID = "g6r_h4t_standard"
AUX_SIGNAL_ID = "g6r_h4t_aux"
# Initially derived from a working Broadlink capture and a G6R handset.
# Keep these transmission parameters unchanged in this UI/Flow update.
COMMANDS: dict[str, tuple[str, int, str, int]] = {
    "on": ("På / tenn", 0b1001, STANDARD_SIGNAL_ID, 10),
    "off": ("Av", 0b1011, STANDARD_SIGNAL_ID, 10),
    "broad": ("Bred flamme", 0b1001, AUX_SIGNAL_ID, 30),
    "narrow": ("Smal flamme", 0b1010, AUX_SIGNAL_ID, 30),
    "flame_up": ("Flamme opp", 0b1101, STANDARD_SIGNAL_ID, 10),
    "flame_down": ("Flamme ned", 0b1110, STANDARD_SIGNAL_ID, 10),
}


def frame_for(address: int, command: int) -> list[int]:
    if not 0 <= address < 2**ADDRESS_BITS:
        raise ValueError("Invalid 18-bit G6R handset address")
    if not 0 <= command < 16:
        raise ValueError("Invalid 4-bit G6R command")
    word = (address << 4) | command
    return [(word >> n) & 1 for n in range(21, -1, -1)]


class PeisTestDevice(Device):
    async def on_init(self) -> None:
        await super().on_init()
        self._address = int(self.get_data()["address"])
        self._tx_lock = asyncio.Lock()
        self._hold_lock = asyncio.Lock()
        self._hold_task: asyncio.Task | None = None
        self._hold_session: str | None = None
        self._hold_last_heartbeat: float = 0.0
        self._hold_stop = asyncio.Event()

        self._standard = self.homey.rf.get_signal_433(STANDARD_SIGNAL_ID)
        self._aux = self.homey.rf.get_signal_433(AUX_SIGNAL_ID)
        # Homey does not automatically add new capabilities to already paired devices.
        # Perform migration only when needed, without sending any RF command.
        if not self.has_capability("onoff"):
            await self.add_capability("onoff")
            await self.set_capability_value("onoff", False)
            self.log("EMBERRF MIGRATE: added onoff, initialized to OFF as an assumed command state; no RF sent")
        for obsolete in ("button.peis_pa", "button.peis_av"):
            if self.has_capability(obsolete):
                await self.remove_capability(obsolete)
                self.log(f"EMBERRF MIGRATE: removed obsolete {obsolete}; no RF sent")

        self.register_capability_listener("onoff", self.on_onoff)
        self.register_capability_listener("button.bred_flamme", self._on_broad)
        self.register_capability_listener("button.smal_flamme", self._on_narrow)
        self.register_capability_listener("button.flame_up", self._on_flame_up)
        self.register_capability_listener("button.flame_down", self._on_flame_down)
        self.log(
            f"EMBERRF READY: device=EmberRF address=0x{self._address:05X} "
            f"antenna={self._antenna_name()} capabilities=onoff,broad,narrow,flame_up,flame_down "
            "RF=433.92MHz status=commanded-only (no physical feedback)"
        )

    async def on_onoff(self, value: bool, **kwargs: Any) -> None:
        await self.send_command("on" if value else "off", source="På/Av-bryter (UI eller standard Flow)")

    async def _on_broad(self, value: bool, **kwargs: Any) -> None:
        await self.send_command("broad", source="Bred-knapp (Homey UI)")

    async def _on_narrow(self, value: bool, **kwargs: Any) -> None:
        await self.send_command("narrow", source="Smal-knapp (Homey UI)")

    async def _on_flame_up(self, value: bool, **kwargs: Any) -> None:
        await self.send_command("flame_up", source="Flamme opp (Homey UI)")

    async def _on_flame_down(self, value: bool, **kwargs: Any) -> None:
        await self.send_command("flame_down", source="Flamme ned (Homey UI)")

    def _antenna_name(self) -> str:
        try:
            value = self.get_setting("satellite_mode_antenna")
        except Exception:
            return "ukjent"
        if value == "self":
            return "Homey Pro"
        return "Homey Bridge" if value else "not selected"

    async def on_settings(self, old_settings: dict, new_settings: dict, changed_keys: tuple[str, ...]) -> str | None:
        if "satellite_mode_antenna" in changed_keys:
            self.log(
                f"EMBERRF ANTENNE: byttet fra {old_settings.get('satellite_mode_antenna')} "
                f"til {new_settings.get('satellite_mode_antenna')}; ingen RF sendt"
            )
        return None

    async def _trigger_result(self, action: str, tokens: dict[str, str]) -> None:
        # A Flow-card error must never cause us to retransmit an already-sent RF frame.
        try:
            if action == "rf_accepted":
                await self.driver.trigger_rf_accepted(self, tokens)
            else:
                await self.driver.trigger_rf_failed(self, tokens)
        except Exception as exc:
            self.error(f"EMBERRF LOG: could not trigger {action} Flow: {exc}")

    repetitions_for_factor = staticmethod(repetitions_for_factor)

    async def on_uninit(self) -> None:
        # A dashboard disappearing, an app restart or an unload stops any
        # future RF bursts. The current short burst cannot be recalled.
        self._hold_stop.set()
        task = self._hold_task
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        await super().on_uninit()

    async def start_hold(self, direction: str, session: str) -> dict:
        if direction not in ("flame_up", "flame_down"):
            raise ValueError("Only flame_up or flame_down may be held")
        if not isinstance(session, str) or len(session) < 8 or len(session) > 100:
            raise ValueError("Invalid hold session")
        async with self._hold_lock:
            if self._hold_task and not self._hold_task.done():
                if session == self._hold_session:
                    return {"active": True}
                raise RuntimeError("Flame hold already active on this device")
            self._hold_stop = asyncio.Event()
            self._hold_session = session
            self._hold_last_heartbeat = time.monotonic()
            self._hold_task = asyncio.create_task(self._hold_loop(direction, session))
            self.log(f"EMBERRF HOLD START: direction={direction}; max={HOLD_MAX_SECONDS}s; antenna={self._antenna_name()}")
            return {"active": True, "max_seconds": HOLD_MAX_SECONDS}

    async def heartbeat_hold(self, session: str) -> dict:
        async with self._hold_lock:
            active = (self._hold_session == session
                      and self._hold_task is not None
                      and not self._hold_task.done())
            if active:
                self._hold_last_heartbeat = time.monotonic()
            return {"active": bool(active)}

    async def stop_hold(self, session: str) -> dict:
        async with self._hold_lock:
            if self._hold_session != session:
                return {"stopped": False}
            self._hold_stop.set()
            task = self._hold_task
        if task and not task.done():
            # Wait for at most the RF burst in progress. Do not restart TX.
            await task
        return {"stopped": True}

    async def _hold_loop(self, direction: str, session: str) -> None:
        started = time.monotonic()
        bursts = 0
        try:
            while (not self._hold_stop.is_set()
                   and time.monotonic() - started < HOLD_MAX_SECONDS
                   and time.monotonic() - self._hold_last_heartbeat < HOLD_HEARTBEAT_SECONDS):
                await self.send_command(
                    direction, source="Dashboard hold",
                    repetitions=HOLD_BURST_REPETITIONS, emit_result=(bursts == 0),
                )
                bursts += 1
                # Give other tasks and the STOP/heartbeat API a chance to run.
                await asyncio.sleep(0)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.error(f"EMBERRF HOLD ERROR: direction={direction}; {exc}")
        finally:
            self.log(f"EMBERRF HOLD STOP: direction={direction}; bursts={bursts}; elapsed={time.monotonic() - started:.2f}s")
            self._hold_stop.set()

    async def send_command(
        self, action: str, *, source: str = "ukjent",
        repetitions: int | None = None, emit_result: bool = True,
    ) -> None:
        title, command, profile, repeats = COMMANDS[action]
        if repetitions is not None:
            if isinstance(repetitions, bool) or not isinstance(repetitions, int) or not 1 <= repetitions <= 255:
                raise ValueError("Repetitions must be an integer from 1 to 255")
            repeats = repetitions
        signal = self._aux if profile == AUX_SIGNAL_ID else self._standard
        bits = frame_for(self._address, command)
        antenna = self._antenna_name()
        # Any manual or Flow command preempts an existing dashboard hold
        # before its next radio burst. Never keep holding after OFF.
        if source != "Dashboard hold":
            if self._hold_task is not None and not self._hold_task.done():
                self._hold_stop.set()
                self.log("EMBERRF HOLD INTERRUPTED: another command was requested")
        async with self._tx_lock:
            self.log(
                f"EMBERRF TX START: kommando={title}; kilde={source}; antenne={antenna}; "
                f"adresse=0x{self._address:05X}; databits={''.join(map(str,bits))}; "
                f"profil={profile}; repetisjoner={repeats}"
            )
            try:
                await signal.tx(bits, repetitions=repeats, device=self)
            except Exception as exc:
                self.error(
                    f"EMBERRF TX FEIL: kommando={title}; antenne={antenna}; "
                    f"kilde={source}; feil={type(exc).__name__}: {exc}"
                )
                if emit_result:
                    await self._trigger_result("rf_failed", {"kommando": title, "antenne": antenna, "feil": str(exc)[:240]})
                raise
            self.log(
                f"EMBERRF TX OK: kommando={title}; antenne={antenna}; "
                f"kilde={source}; RF akseptert av Homey; fysisk resultat ikke bekreftet"
            )
        if emit_result:
            await self._trigger_result("rf_accepted", {"kommando": title, "antenne": antenna, "kilde": source})


homey_export = PeisTestDevice
