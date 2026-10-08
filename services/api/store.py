"""Single-table store (pk/sk) sobre DynamoDB `connect-atv-data`, con backend en memoria para tests.

Cada item: pk, sk, doc (JSON string) + atributos opcionales para condiciones (rev, status, ttl).
"""
import copy
import json
import os
import threading
import time

TABLE = os.environ.get("FV_TABLE", "connect-atv-data")


class ConditionFailed(Exception):
    pass


def _cond_ok(cur, cond):
    if cond is None:
        return True
    if cond == "not_exists":
        return cur is None
    k, v = cond
    if cur is None:
        return v is None
    return cur.get("_attrs", {}).get(k) == v


class MemoryStore:
    def __init__(self):
        self.items, self.lock, self._slot = {}, threading.Lock(), 0

    def get(self, pk, sk):
        it = self.items.get((pk, sk))
        return copy.deepcopy(it["doc"]) if it else None

    def put(self, pk, sk, doc, cond=None, attrs=None):
        with self.lock:
            if not _cond_ok(self.items.get((pk, sk)), cond):
                raise ConditionFailed(f"{pk}/{sk}")
            self.items[(pk, sk)] = {"doc": copy.deepcopy(doc), "_attrs": dict(attrs or {})}

    def query(self, pk, prefix="", desc=False, limit=None):
        ks = sorted(k for k in self.items if k[0] == pk and k[1].startswith(prefix))
        if desc:
            ks.reverse()
        return [copy.deepcopy(self.items[k]["doc"]) for k in ks[:limit]]

    def scan_prefix(self, sk_prefix, limit=500):
        ks = sorted(k for k in self.items if k[1].startswith(sk_prefix))[:limit]
        return [dict(copy.deepcopy(self.items[k]["doc"]), _pk=k[0]) for k in ks]

    def delete_pk(self, pk):
        with self.lock:
            for k in [k for k in self.items if k[0] == pk]:
                del self.items[k]

    def transact(self, ops):
        """ops: [(pk, sk, doc, cond, attrs)] — todo o nada."""
        with self.lock:
            for pk, sk, doc, cond, attrs in ops:
                if not _cond_ok(self.items.get((pk, sk)), cond):
                    raise ConditionFailed(f"{pk}/{sk}")
            for pk, sk, doc, cond, attrs in ops:
                self.items[(pk, sk)] = {"doc": copy.deepcopy(doc), "_attrs": dict(attrs or {})}

    def reserve_slot(self, gap_ms):
        """Devuelve epoch-ms en que esta llamada puede empezar (global, ≥gap entre llamadas)."""
        with self.lock:
            now = int(time.time() * 1000)
            slot = max(now, self._slot)
            self._slot = slot + gap_ms
            return slot


class DynamoStore:
    def __init__(self, table=TABLE, region=None):
        import boto3
        from botocore.config import Config
        self.ddb = boto3.client("dynamodb", region_name=region or os.environ.get("AWS_REGION", "us-east-1"),
                                config=Config(retries={"max_attempts": 3, "mode": "standard"}, connect_timeout=3, read_timeout=5))
        self.table = table

    @staticmethod
    def _item(pk, sk, doc, attrs):
        it = {"pk": {"S": pk}, "sk": {"S": sk}, "doc": {"S": json.dumps(doc, ensure_ascii=False)}}
        for k, v in (attrs or {}).items():
            it[k] = {"N": str(v)} if isinstance(v, (int, float)) and not isinstance(v, bool) else {"S": str(v)}
        return it

    @staticmethod
    def _cond(cond):
        if cond is None:
            return {}
        if cond == "not_exists":
            return {"ConditionExpression": "attribute_not_exists(pk)"}
        k, v = cond
        if v is None:
            return {"ConditionExpression": "attribute_not_exists(pk)"}
        val = {"N": str(v)} if isinstance(v, (int, float)) and not isinstance(v, bool) else {"S": str(v)}
        return {"ConditionExpression": "#c = :c", "ExpressionAttributeNames": {"#c": k},
                "ExpressionAttributeValues": {":c": val}}

    def get(self, pk, sk):
        r = self.ddb.get_item(TableName=self.table, Key={"pk": {"S": pk}, "sk": {"S": sk}}, ConsistentRead=True)
        it = r.get("Item")
        return json.loads(it["doc"]["S"]) if it and "doc" in it else None

    def put(self, pk, sk, doc, cond=None, attrs=None):
        try:
            self.ddb.put_item(TableName=self.table, Item=self._item(pk, sk, doc, attrs), **self._cond(cond))
        except self.ddb.exceptions.ConditionalCheckFailedException as e:
            raise ConditionFailed(f"{pk}/{sk}") from e

    def query(self, pk, prefix="", desc=False, limit=None):
        kw = {"TableName": self.table, "KeyConditionExpression": "pk = :p AND begins_with(sk, :s)",
              "ExpressionAttributeValues": {":p": {"S": pk}, ":s": {"S": prefix}}, "ScanIndexForward": not desc}
        if limit:
            kw["Limit"] = limit
        out = []
        while True:
            r = self.ddb.query(**kw)
            out += [json.loads(i["doc"]["S"]) for i in r.get("Items", []) if "doc" in i]
            if limit and len(out) >= limit or "LastEvaluatedKey" not in r:
                return out[:limit] if limit else out
            kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]

    def scan_prefix(self, sk_prefix, limit=500):
        kw = {"TableName": self.table, "FilterExpression": "begins_with(sk, :s)",
              "ExpressionAttributeValues": {":s": {"S": sk_prefix}}}
        out = []
        while len(out) < limit:
            r = self.ddb.scan(**kw)
            out += [dict(json.loads(i["doc"]["S"]), _pk=i["pk"]["S"]) for i in r.get("Items", []) if "doc" in i]
            if "LastEvaluatedKey" not in r:
                break
            kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]
        return out[:limit]

    def delete_pk(self, pk):
        kw = {"TableName": self.table, "KeyConditionExpression": "pk = :p",
              "ExpressionAttributeValues": {":p": {"S": pk}}, "ProjectionExpression": "pk, sk"}
        keys = []
        while True:
            r = self.ddb.query(**kw)
            keys += r.get("Items", [])
            if "LastEvaluatedKey" not in r:
                break
            kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]
        for i in range(0, len(keys), 25):
            self.ddb.batch_write_item(RequestItems={self.table: [{"DeleteRequest": {"Key": k}} for k in keys[i:i + 25]]})

    def transact(self, ops):
        items = []
        for pk, sk, doc, cond, attrs in ops:
            items.append({"Put": dict({"TableName": self.table, "Item": self._item(pk, sk, doc, attrs)}, **self._cond(cond))})
        try:
            self.ddb.transact_write_items(TransactItems=items)
        except self.ddb.exceptions.TransactionCanceledException as e:
            raise ConditionFailed("transaction") from e

    def reserve_slot(self, gap_ms):
        """Lock global por escritura condicional: reserva el próximo hueco de Bedrock."""
        key = {"pk": {"S": "LOCK"}, "sk": {"S": "BEDROCK"}}
        for _ in range(20):
            r = self.ddb.get_item(TableName=self.table, Key=key, ConsistentRead=True)
            old = int(r["Item"]["next_at"]["N"]) if "Item" in r and "next_at" in r["Item"] else None
            now = int(time.time() * 1000)
            slot = max(now, old or 0)
            try:
                kw = {"TableName": self.table, "Key": key, "UpdateExpression": "SET next_at = :n",
                      "ExpressionAttributeValues": {":n": {"N": str(slot + gap_ms)}}}
                if old is None:
                    kw["ConditionExpression"] = "attribute_not_exists(next_at)"
                else:
                    kw["ConditionExpression"] = "next_at = :o"
                    kw["ExpressionAttributeValues"][":o"] = {"N": str(old)}
                self.ddb.update_item(**kw)
                return slot
            except self.ddb.exceptions.ConditionalCheckFailedException:
                time.sleep(0.05)
        return int(time.time() * 1000) + gap_ms


_STORE = None


def get_store():
    global _STORE
    if _STORE is None:
        _STORE = MemoryStore() if os.environ.get("FV_STORE") == "memory" else DynamoStore()
    return _STORE


def set_store(s):
    global _STORE
    _STORE = s
