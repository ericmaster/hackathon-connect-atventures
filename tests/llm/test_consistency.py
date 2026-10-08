"""Suite de consistencia contra Bedrock (opt-in, gasta llamadas: 1 RPS).

  FV_LLM_MODEL=haiku-4.5 FV_LLM_RUNS=2 python3 -m unittest tests/llm/test_consistency.py -v

Prueba comportamiento (forma A2UI, componentes, guardrails), no el texto exacto.
"""
import json
import os
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import checks
import run

MODEL = os.environ.get("FV_LLM_MODEL")
RUNS = int(os.environ.get("FV_LLM_RUNS", "1"))
TEMP = float(os.environ.get("FV_LLM_TEMPERATURE", "0"))


@unittest.skipUnless(MODEL, "define FV_LLM_MODEL (clave de models.json) para correr contra Bedrock")
class TestConsistency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import bedrock
        cls.brt = bedrock.client()

    def _case(self, fx):
        for i in range(RUNS):
            res = run.call_model(self.brt, MODEL, fx, temperature=TEMP)
            self.assertTrue(res["ok"], res.get("error"))
            sc = checks.score(res["text"], fx)
            fails = {k: sc[k]["detail"] for k in checks.CHECKS if sc[k]["ok"] is False}
            self.assertFalse(fails, f"{fx['id']} corrida {i}: {json.dumps(fails, ensure_ascii=False)}")


for _fx in run.load_fixtures():
    setattr(TestConsistency, f"test_{_fx['id']}", lambda self, fx=_fx: self._case(fx))

if __name__ == "__main__":
    unittest.main()
