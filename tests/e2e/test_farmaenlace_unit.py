"""Cliente HTTP del orquestador contra la API mock de Farmaenlace (local_server.py real, HTTP sin firma) + fail-closed."""
import os
import socket
import subprocess
import sys
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "services", "api"))
os.environ["FV_STORE"] = "memory"
import mock  # noqa: E402


def _port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class FarmaenlaceHttpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = _port()
        cls.proc = subprocess.Popen([sys.executable, os.path.join(ROOT, "services", "farmaenlace-mock", "local_server.py"),
                                     str(cls.port)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        cls.proc.stdout.readline()
        time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(5)

    def setUp(self):
        os.environ["FV_FARMAENLACE_URL"] = f"http://127.0.0.1:{self.port}"
        mock._CACHE.clear()

    def tearDown(self):
        os.environ.pop("FV_FARMAENLACE_URL", None)

    def test_reads_and_order_over_http(self):
        self.assertEqual(mock.pharmacies()[0]["pharmacyId"], "MED-UIO-014")
        self.assertEqual([p["sku"] for p in mock.search_products(["gripe"], include_rx=True)][:2], ["FV-1001", "FV-1004"])
        p, created = mock.get_profile("u1", "1712456787")
        self.assertFalse(created)
        self.assertEqual(p["archetype"], "Práctico")
        mock.ensure_coupon("u1", "1712456787")
        s = {"cart": [{"sku": "FV-1002", "qty": 1}], "pharmacyId": "MED-UIO-014", "revision": 3}
        b = {"tipo": "consumidor_final", "email": "a@b.co"}
        put = lambda res: ({"x": 1}, None, {"rev": 4})  # noqa: E731
        r1, c1 = mock.reserve("u1", s, p, b, 3, put)
        r2, c2 = mock.reserve("u1", s, p, b, 3, put)
        self.assertTrue(c1)
        self.assertFalse(c2)
        self.assertEqual(r1["order"]["orderNumber"], r2["order"]["orderNumber"])
        self.assertEqual(r1["invoice"]["sri"]["estado"], "SIMULADA_NO_TRANSMITIDA")
        self.assertEqual(len(r1["invoice"]["sri"]["infoTributaria"]["claveAcceso"]), 49)
        self.assertEqual(mock.get_coupon("u1", "1712456787")["status"], "usado")
        crm = str(mock.admin_list("crm"))
        self.assertNotIn("hipertension", crm)
        self.assertNotIn("rinitis", crm)

    def test_fail_closed(self):
        os.environ["FV_FARMAENLACE_URL"] = "http://127.0.0.1:9"
        with self.assertRaises(mock.BackendUnavailable):
            mock.get_profile("u2", "1710034065")
        with self.assertRaises(mock.BackendUnavailable):
            mock.pharmacies()


if __name__ == "__main__":
    unittest.main()
