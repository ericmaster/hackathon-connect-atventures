"""Tests offline de services/api/admin.py con MemoryStore. python3 -m unittest tests/e2e/test_admin_unit.py"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "services", "api"))
os.environ["FV_STORE"] = "memory"

import store  # noqa: E402
import mock  # noqa: E402
import admin  # noqa: E402


class AdminTest(unittest.TestCase):
    def setUp(self):
        store.set_store(store.MemoryStore())
        mock._CACHE.clear()
        mock.seed()
        mock.get_profile("s1", "1729876548")
        mock.log({"route": "/turn", "state": "consulta", "ms": 12, "mode": "real", "status": 200})
        os.environ.pop("FV_ADMIN_SHOW_INTERNAL", None)
        os.environ.pop("FV_ADMIN_IDENTITIES", None)

    def test_all_services(self):
        for s in admin.SERVICES:
            st, body = admin.handle(s)
            self.assertEqual(st, 200, s)
            self.assertIsInstance(body["items"], list)
        self.assertEqual(len(admin.handle("catalogo")[1]["items"]), 36)  # catálogo ampliado (farmaenlace-mock)
        self.assertEqual(len(admin.handle("farmacias")[1]["items"]), 5)
        self.assertEqual(len(admin.handle("crm")[1]["items"]), 5)  # 4 seeds sintéticos + 1 sandbox

    def test_list_service_body(self):
        b = admin.list_service("pedidos")
        self.assertEqual(b["service"], "pedidos")
        self.assertIsInstance(b["items"], list)

    def test_logs(self):
        st, body = admin.handle("logs")
        self.assertEqual(st, 200)
        self.assertEqual(body["items"][0]["route"], "/turn")

    def test_unknown(self):
        self.assertEqual(admin.handle("borrar")[0], 404)

    def test_conditions_hidden_by_default(self):
        crm = admin.handle("crm")[1]["items"]
        for p in crm:
            self.assertNotIsInstance(p.get("condiciones_probables"), list)
            self.assertNotIn(admin.INTERNAL_KEY, p)

    def test_conditions_internal_flag(self):
        os.environ["FV_ADMIN_SHOW_INTERNAL"] = "1"
        crm = admin.handle("crm")[1]["items"]
        luis = next(p for p in crm if p["cedula"] == "1710034065")
        self.assertIn("hipertension", luis[admin.INTERNAL_KEY])
        self.assertNotIn("condiciones_probables", luis)

    def test_allowlist(self):
        os.environ["FV_ADMIN_IDENTITIES"] = "us-east-1:abc"
        ev = {"requestContext": {"authorizer": {"iam": {"cognitoIdentity": {"identityId": "us-east-1:zzz"}}}}}
        self.assertEqual(admin.handle("crm", ev)[0], 403)
        ev["requestContext"]["authorizer"]["iam"]["cognitoIdentity"]["identityId"] = "us-east-1:abc"
        self.assertEqual(admin.handle("crm", ev)[0], 200)


if __name__ == "__main__":
    unittest.main()
