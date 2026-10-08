"""AWS EventStream (vnd.amazon.eventstream) mínimo para Transcribe streaming."""
import binascii
import json
import struct


def _headers(h: dict) -> bytes:
    out = b""
    for k, v in h.items():
        kb, vb = k.encode(), v.encode()
        out += struct.pack(">B", len(kb)) + kb + b"\x07" + struct.pack(">H", len(vb)) + vb
    return out


def encode(headers: dict, payload: bytes) -> bytes:
    hb = _headers(headers)
    total = 12 + len(hb) + len(payload) + 4
    prelude = struct.pack(">II", total, len(hb))
    prelude += struct.pack(">I", binascii.crc32(prelude) & 0xFFFFFFFF)
    msg = prelude + hb + payload
    return msg + struct.pack(">I", binascii.crc32(msg) & 0xFFFFFFFF)


def audio_event(pcm: bytes) -> bytes:
    return encode({":content-type": "application/octet-stream", ":event-type": "AudioEvent",
                   ":message-type": "event"}, pcm)


def decode(buf: bytes):
    total, hlen = struct.unpack(">II", buf[:8])
    if binascii.crc32(buf[:8]) & 0xFFFFFFFF != struct.unpack(">I", buf[8:12])[0]:
        raise ValueError("prelude crc")
    if binascii.crc32(buf[: total - 4]) & 0xFFFFFFFF != struct.unpack(">I", buf[total - 4 : total])[0]:
        raise ValueError("message crc")
    h, i, end = {}, 12, 12 + hlen
    while i < end:
        n = buf[i]; i += 1
        name = buf[i : i + n].decode(); i += n
        t = buf[i]; i += 1
        if t != 7:
            raise ValueError(f"header type {t} no soportado")
        ln = struct.unpack(">H", buf[i : i + 2])[0]; i += 2
        h[name] = buf[i : i + ln].decode(); i += ln
    return h, buf[end : total - 4]


def parse_json(buf: bytes):
    h, p = decode(buf)
    return h, (json.loads(p) if p else None)
