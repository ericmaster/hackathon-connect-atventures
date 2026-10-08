"""Checks the public path: unsigned → 403, Cognito guest SigV4 → 200, CORS preflight, guest cannot invoke Lambdas directly. Never prints credentials."""
import json, time, urllib.request, boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials
from botocore import UNSIGNED
from botocore.config import Config
URL="https://znpzz1wg21.execute-api.us-east-1.amazonaws.com"; POOL="us-east-1:8434d4ed-e17e-4082-ad26-42b59e004e3e"
ci=boto3.client("cognito-identity",region_name="us-east-1",config=Config(signature_version=UNSIGNED))
iid=ci.get_id(IdentityPoolId=POOL)["IdentityId"]
c=ci.get_credentials_for_identity(IdentityId=iid)["Credentials"]
creds=Credentials(c["AccessKeyId"],c["SecretKey"],c["SessionToken"])
def req(method,path,body=None,sign=True,origin=None):
    data=json.dumps(body).encode() if body is not None else None
    r=AWSRequest(method=method,url=URL+path,data=data,headers={"Content-Type":"application/json"} if data else {})
    if sign: SigV4Auth(creds,"execute-api","us-east-1").add_auth(r)
    h=dict(r.headers)
    if origin: h["Origin"]=origin
    t=time.time()
    try:
        resp=urllib.request.urlopen(urllib.request.Request(URL+path,data=data,method=method,headers=h),timeout=35)
        return resp.status,json.loads(resp.read()),int((time.time()-t)*1000),dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code,e.read()[:200],int((time.time()-t)*1000),dict(e.headers)
print("identity ok:", iid.split(":")[0])
print("unsigned /session ->", req("POST","/session",{},sign=False)[:2])
s,b,ms,h=req("POST","/session",{},origin="https://main.d2bloxc35rzfqy.amplifyapp.com")
print("signed /session ->", s, b.get("state"), ms,"ms", "ACAO:",h.get("access-control-allow-origin") or h.get("Access-Control-Allow-Origin"))
s2,b2,ms2,_=req("POST","/turn",{"sessionId":b["sessionId"],"text":"1710034065"})
print("signed /turn ->", s2, b2.get("state"), ms2,"ms")
s3,b3,_,_=req("GET","/admin/catalogo"); print("admin ->",s3, b3.get("count") if isinstance(b3,dict) else b3)
# preflight
r=urllib.request.Request(URL+"/turn",method="OPTIONS",headers={"Origin":"https://main.dfsvbpju4hwi2.amplifyapp.com","Access-Control-Request-Method":"POST","Access-Control-Request-Headers":"authorization,content-type,x-amz-date,x-amz-security-token"})
try:
    resp=urllib.request.urlopen(r,timeout=10); print("preflight", resp.status, resp.headers.get("access-control-allow-origin"))
except urllib.error.HTTPError as e: print("preflight", e.code)
# guest creds cannot invoke the lambda directly
try:
    boto3.client("lambda",region_name="us-east-1",aws_access_key_id=c["AccessKeyId"],aws_secret_access_key=c["SecretKey"],aws_session_token=c["SessionToken"]).invoke(FunctionName="connect-atv-gliner",Payload=b"{}")
    print("guest lambda invoke: ALLOWED (bad)")
except Exception as e: print("guest direct lambda invoke denied:", type(e).__name__)
