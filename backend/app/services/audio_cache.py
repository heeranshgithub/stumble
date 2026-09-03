"""Synthesized audio per turn, kept in memory so a replay never pays for a second synthesis."""

from collections import OrderedDict


class AudioCache:
    def __init__(self, max_items: int = 200) -> None:
        self._items: OrderedDict[str, bytes] = OrderedDict()
        self._max = max_items

    def get(self, key: str) -> bytes | None:
        data = self._items.get(key)
        if data is not None:
            self._items.move_to_end(key)
        return data

    def put(self, key: str, data: bytes) -> None:
        self._items[key] = data
        self._items.move_to_end(key)
        while len(self._items) > self._max:
            self._items.popitem(last=False)
