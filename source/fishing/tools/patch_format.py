"""Strict IPS/IPS32 reader and IPS32 writer for this project's tools."""
from __future__ import annotations

def parse_ips(data: bytes) -> list[tuple[int, bytes]]:
    if data[:5] == b"IPS32":
        width, tail = 4, b"EEOF"
    elif data[:5] == b"PATCH":
        width, tail = 3, b"EOF"
    else:
        raise ValueError("Not an IPS/IPS32 patch")
    pos, records = 5, []
    while True:
        if data[pos:pos + width] == tail:
            if pos + width != len(data):
                raise ValueError("Unexpected data after IPS footer")
            return records
        if pos + width + 2 > len(data):
            raise ValueError("Truncated IPS record")
        offset = int.from_bytes(data[pos:pos + width], "big")
        size = int.from_bytes(data[pos + width:pos + width + 2], "big")
        pos += width + 2
        if size:
            if pos + size > len(data):
                raise ValueError("Truncated IPS payload")
            payload = data[pos:pos + size]
            pos += size
        else:
            if pos + 3 > len(data):
                raise ValueError("Truncated IPS RLE record")
            count = int.from_bytes(data[pos:pos + 2], "big")
            if not count:
                raise ValueError("Empty IPS RLE record")
            payload = bytes([data[pos + 2]]) * count
            pos += 3
        if offset < 0x100 or offset + len(payload) > 0x100000000:
            raise ValueError("IPS record outside supported NSO image")
        if any(offset < old + len(blob) and old < offset + len(payload)
               for old, blob in records):
            raise ValueError("Overlapping IPS records")
        records.append((offset, payload))

def write_ips32(records: list[tuple[int, bytes]]) -> bytes:
    result = bytearray(b"IPS32")
    for offset, payload in records:
        if not payload or len(payload) > 65535:
            raise ValueError("Invalid IPS32 payload size")
        result += offset.to_bytes(4, "big")
        result += len(payload).to_bytes(2, "big") + payload
    result += b"EEOF"
    parse_ips(bytes(result))
    return bytes(result)
