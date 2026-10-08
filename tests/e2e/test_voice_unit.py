"""Tests offline de services/api/voice.py y del framing EventStream.

python3 -m unittest tests/e2e/test_voice_unit.py -v
"""
import base64
import datetime as dt
import io
import os
import sys
import unittest
import urllib.parse
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "services", "api"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import voice  # noqa: E402
import eventstream  # noqa: E402

CREDS = SimpleNamespace(access_key="AKIDEXAMPLE", secret_key="wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY",
                        token="tok/en+==")
NOW = dt.datetime(2026, 10, 8, 17, 30, 0, tzinfo=dt.timezone.utc)


class PresignTest(unittest.TestCase):
    def test_shape(self):
        r = voice.presign_transcribe_url(credentials=CREDS, now=NOW, region="us-east-1")
        u = urllib.parse.urlparse(r["url"])
        self.assertEqual(u.scheme, "wss")
        self.assertEqual(u.netloc, "transcribestreaming.us-east-1.amazonaws.com:8443")
        self.assertEqual(u.path, "/stream-transcription-websocket")
        q = dict(urllib.parse.parse_qsl(u.query))
        self.assertEqual(q["language-code"], "es-US")
        self.assertEqual(q["sample-rate"], "16000")
        self.assertEqual(q["media-encoding"], "pcm")
        self.assertEqual(q["X-Amz-Expires"], "300")
        self.assertEqual(q["X-Amz-Security-Token"], "tok/en+==")
        self.assertEqual(q["X-Amz-Credential"], "AKIDEXAMPLE/20261008/us-east-1/transcribe/aws4_request")
        self.assertRegex(q["X-Amz-Signature"], r"^[0-9a-f]{64}$")
        self.assertEqual(r["expiresAt"], int(NOW.timestamp()) + 300)
        self.assertNotIn("vocabulary-name", q)

    def test_deterministic_and_vocab(self):
        a = voice.presign_transcribe_url(credentials=CREDS, now=NOW, region="us-east-1")["url"]
        b = voice.presign_transcribe_url(credentials=CREDS, now=NOW, region="us-east-1")["url"]
        self.assertEqual(a, b)
        c = voice.presign_transcribe_url(vocabulary_name="fv-marcas", credentials=CREDS, now=NOW,
                                         region="us-east-1")["url"]
        self.assertIn("vocabulary-name=fv-marcas", c)
        self.assertNotEqual(a.split("X-Amz-Signature=")[1], c.split("X-Amz-Signature=")[1])

    def test_rejects(self):
        with self.assertRaises(ValueError):
            voice.presign_transcribe_url(language="xx-XX", credentials=CREDS, now=NOW)
        with self.assertRaises(ValueError):
            voice.presign_transcribe_url(sample_rate=44100, credentials=CREDS, now=NOW)
        r = voice.presign_transcribe_url(expires=9999, credentials=CREDS, now=NOW)
        self.assertIn("X-Amz-Expires=300", r["url"])


class FakePolly:
    def __init__(self, fail_generative=False):
        self.calls = []
        self.fail_generative = fail_generative

    def synthesize_speech(self, **kw):
        self.calls.append(kw)
        if self.fail_generative and kw["Engine"] == "generative":
            raise RuntimeError("boom")
        return {"AudioStream": io.BytesIO(b"ID3fake")}


class SynthTest(unittest.TestCase):
    def test_generative(self):
        p = FakePolly()
        r = voice.synthesize("Hola, ¿en qué te ayudo?", client=p)
        self.assertEqual(base64.b64decode(r["audio"]), b"ID3fake")
        self.assertEqual(r["engine"], "generative")
        self.assertEqual(p.calls[0]["VoiceId"], "Lupe")
        self.assertEqual(p.calls[0]["LanguageCode"], "es-US")
        self.assertEqual(p.calls[0]["OutputFormat"], "mp3")

    def test_fallback_neural(self):
        p = FakePolly(fail_generative=True)
        r = voice.synthesize("Hola", client=p)
        self.assertEqual(r["engine"], "neural")
        self.assertEqual([c["Engine"] for c in p.calls], ["generative", "neural"])

    def test_cap_and_empty(self):
        p = FakePolly()
        r = voice.synthesize("palabra " * 500, client=p)
        self.assertLessEqual(len(p.calls[0]["Text"]), voice.MAX_TTS_CHARS)
        self.assertLessEqual(r["chars"], voice.MAX_TTS_CHARS)
        with self.assertRaises(ValueError):
            voice.synthesize("   ", client=p)

    def test_all_fail(self):
        class Bad:
            def synthesize_speech(self, **kw):
                raise RuntimeError("x")
        with self.assertRaises(RuntimeError):
            voice.synthesize("hola", client=Bad())


class EventStreamTest(unittest.TestCase):
    def test_roundtrip(self):
        msg = eventstream.audio_event(b"\x01\x02" * 100)
        h, p = eventstream.decode(msg)
        self.assertEqual(h[":event-type"], "AudioEvent")
        self.assertEqual(p, b"\x01\x02" * 100)

    def test_empty_end_frame(self):
        h, p = eventstream.decode(eventstream.audio_event(b""))
        self.assertEqual(p, b"")

    def test_crc_detects_corruption(self):
        m = bytearray(eventstream.audio_event(b"abc"))
        m[-6] ^= 0xFF
        with self.assertRaises(ValueError):
            eventstream.decode(bytes(m))


if __name__ == "__main__":
    unittest.main()
