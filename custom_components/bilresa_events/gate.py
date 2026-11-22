"""Pure bounded identity deduplication; no gesture or time inference."""
from collections import deque
import re

UID = re.compile(r"^[0-9A-Fa-f]+-([0-9A-Fa-f]{16})-MatterNodeDevice-(\d+)-GenericSwitch-59-\d+$")
LIMIT = 512


def address(unique_id):
    match = UID.fullmatch(unique_id or "")
    if match is None:
        raise ValueError("Expected a native Matter Generic Switch event entity")
    return int(match[1], 16), int(match[2])


class ReleaseGate:
    """Remember 512 releases per endpoint, including across integration reloads.

    Event numbers identify Matter events, unlike HA receipt timestamps. Out-of-order
    distinct events remain valid. No initial node snapshot is converted to an event.
    """

    def __init__(self, saved=None):
        self.recent = {}
        for key, values in (saved or {}).items():
            self.recent[key] = deque(
                (n for n in values if type(n) is int and n >= 0), maxlen=LIMIT
            )

    def accept(self, event, node_id, endpoint_id):
        if (event.node_id != node_id or event.endpoint_id != endpoint_id
                or event.cluster_id != 59 or event.event_id != 3):
            return False
        number = event.event_number
        if type(number) is not int or number < 0:
            return False
        if (event.data or {}).get("previousPosition") != 1:
            return False
        key = f"{node_id}:{endpoint_id}"
        seen = self.recent.setdefault(key, deque(maxlen=LIMIT))
        if number in seen:
            return False
        seen.append(number)
        return True

    def snapshot(self):
        return {key: list(values) for key, values in self.recent.items()}
