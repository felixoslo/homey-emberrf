"""Device-scoped, bounded flame hold API for the EmberRF dashboard widget."""
from typing import Any
from homey.homey import Homey


def _device(homey: Homey, body: dict[str, Any]):
    device_id = body.get("device_id")
    if not isinstance(device_id, str) or not device_id:
        raise ValueError("Select an EmberRF fireplace device in widget settings")
    # Only devices belonging to this app's fireplace driver are accepted.
    return homey.drivers.get_driver("fireplace").get_device_by_id(device_id)


async def start_hold(*, homey: Homey, query: dict[str, str],
                     params: dict[str, str], body: dict[str, Any]) -> dict:
    return await _device(homey, body).start_hold(body.get("direction"), body.get("session"))


async def heartbeat_hold(*, homey: Homey, query: dict[str, str],
                         params: dict[str, str], body: dict[str, Any]) -> dict:
    return await _device(homey, body).heartbeat_hold(body.get("session"))


async def stop_hold(*, homey: Homey, query: dict[str, str],
                    params: dict[str, str], body: dict[str, Any]) -> dict:
    return await _device(homey, body).stop_hold(body.get("session"))


__all__ = ["start_hold", "heartbeat_hold", "stop_hold"]
