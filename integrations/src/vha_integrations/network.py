from __future__ import annotations

import re
import subprocess
from typing import Any

import psutil


class NetworkAnalyzer:
    def __init__(self):
        self._last_bytes_sent = None
        self._last_bytes_recv = None

    def snapshot(self) -> dict[str, Any]:
        counters = psutil.net_io_counters()
        interfaces = psutil.net_if_addrs()

        bytes_sent = counters.bytes_sent
        bytes_recv = counters.bytes_recv

        delta_sent = 0 if self._last_bytes_sent is None else bytes_sent - self._last_bytes_sent
        delta_recv = 0 if self._last_bytes_recv is None else bytes_recv - self._last_bytes_recv

        self._last_bytes_sent = bytes_sent
        self._last_bytes_recv = bytes_recv

        connected_devices = self._discover_connected_devices()
        anomaly_score = self._estimate_anomaly(delta_sent, delta_recv, len(connected_devices))

        summary = (
            f"Netwerk actief met {len(connected_devices)} zichtbare apparaten. "
            f"Verkeer laatste meting: {delta_recv / 1024:.1f} KB in, {delta_sent / 1024:.1f} KB uit."
        )
        if anomaly_score > 0.7:
            summary += " Er is een verhoogde afwijking gedetecteerd."

        return {
            "devices": connected_devices,
            "traffic": {
                "bytes_sent": bytes_sent,
                "bytes_recv": bytes_recv,
                "delta_sent": delta_sent,
                "delta_recv": delta_recv,
                "interfaces": list(interfaces.keys()),
            },
            "anomaly_score": anomaly_score,
            "summary": summary,
        }

    @staticmethod
    def _estimate_anomaly(delta_sent: int, delta_recv: int, device_count: int) -> float:
        baseline = max(device_count * 150_000, 150_000)
        traffic = delta_sent + delta_recv
        if traffic <= baseline:
            return 0.1
        if traffic <= baseline * 3:
            return 0.45
        return 0.82

    @staticmethod
    def _discover_connected_devices() -> list[dict[str, str]]:
        try:
            result = subprocess.run(
                ["arp", "-a"],
                capture_output=True,
                text=True,
                check=False,
                timeout=3,
            )
        except OSError:
            return []

        devices: list[dict[str, str]] = []
        ip_pattern = re.compile(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-f-]+)\s+(\w+)", re.IGNORECASE)
        for match in ip_pattern.finditer(result.stdout):
            devices.append(
                {
                    "ip": match.group(1),
                    "mac": match.group(2),
                    "type": match.group(3),
                }
            )
        return devices

