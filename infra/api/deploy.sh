#!/usr/bin/env bash
# Re-runnable deploy of the Farmacéutico Virtual orchestrator (workstream A).
#   infra/api/deploy.sh            -> table + role + Lambda zip + seed (+ API/auth if EXPOSE=1)
# Never prints credentials. us-east-1, tag project=connect-atventures.
set -euo pipefail
cd "$(dirname "$0")/../.."
export AWS_REGION=${AWS_REGION:-us-east-1} AWS_PAGER=""
R=$AWS_REGION
ACCT=$(aws sts get-caller-identity --query Account --output text)
TABLE=connect-atv-data
FN=connect-atv-orchestrator
ROLE=connect-atv-orchestrator-role
GLINER=connect-atv-gliner
MODEL_PROFILE=us.anthropic.claude-haiku-4-5-20251001-v1:0
TAG_KV="Key=project,Value=connect-atventures"

echo "== DynamoDB $TABLE"
if ! aws dynamodb describe-table --table-name $TABLE >/dev/null 2>&1; then
  aws dynamodb create-table --table-name $TABLE \
    --attribute-definitions AttributeName=pk,AttributeType=S AttributeName=sk,AttributeType=S \
    --key-schema AttributeName=pk,KeyType=HASH AttributeName=sk,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST --tags $TAG_KV >/dev/null
fi
aws dynamodb wait table-exists --table-name $TABLE
aws dynamodb update-time-to-live --table-name $TABLE --time-to-live-specification Enabled=true,AttributeName=ttl >/dev/null 2>&1 || true

echo "== IAM role $ROLE"
TRUST='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
if ! aws iam get-role --role-name $ROLE >/dev/null 2>&1; then
  aws iam create-role --role-name $ROLE --assume-role-policy-document "$TRUST" \
    --tags $TAG_KV --description "connect-atv orchestrator Lambda (minimal)" >/dev/null
  NEW_ROLE=1
fi
POLICY=$(cat <<JSON
{"Version":"2012-10-17","Statement":[
 {"Sid":"Table","Effect":"Allow","Action":["dynamodb:GetItem","dynamodb:PutItem","dynamodb:UpdateItem","dynamodb:DeleteItem","dynamodb:Query","dynamodb:Scan","dynamodb:BatchWriteItem","dynamodb:ConditionCheckItem"],
  "Resource":"arn:aws:dynamodb:$R:$ACCT:table/$TABLE"},
 {"Sid":"Gliner","Effect":"Allow","Action":"lambda:InvokeFunction","Resource":"arn:aws:lambda:$R:$ACCT:function:$GLINER"},
 {"Sid":"Bedrock","Effect":"Allow","Action":["bedrock:InvokeModel","bedrock:InvokeModelWithResponseStream"],
  "Resource":["arn:aws:bedrock:$R:$ACCT:inference-profile/$MODEL_PROFILE",
              "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
              "arn:aws:bedrock:us-east-2::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
              "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0"]},
 {"Sid":"Polly","Effect":"Allow","Action":"polly:SynthesizeSpeech","Resource":"*"},
 {"Sid":"Transcribe","Effect":"Allow","Action":"transcribe:StartStreamTranscriptionWebSocket","Resource":"*"},
 {"Sid":"Logs","Effect":"Allow","Action":["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],
  "Resource":["arn:aws:logs:$R:$ACCT:log-group:/aws/lambda/$FN","arn:aws:logs:$R:$ACCT:log-group:/aws/lambda/$FN:*"]}
]}
JSON
)
aws iam put-role-policy --role-name $ROLE --policy-name orchestrator-minimal --policy-document "$POLICY"
ROLE_ARN=$(aws iam get-role --role-name $ROLE --query Role.Arn --output text)
[ "${NEW_ROLE:-0}" = 1 ] && { echo "   waiting for IAM propagation"; sleep 12; }

echo "== Build zip"
B=$(mktemp -d)
cp services/api/*.py "$B"/
cp tests/llm/checks.py tests/llm/catalog.json tests/llm/system_prompt.md "$B"/
rm -f "$B"/test_*.py
rm -f /tmp/$FN.zip; python3 -c "import shutil,sys; shutil.make_archive(sys.argv[1], 'zip', sys.argv[2])" /tmp/$FN "$B"
echo "   $(ls -la /tmp/$FN.zip | awk '{print $5}') bytes: $(ls "$B" | tr '\n' ' ')"

ENV="Variables={FV_TABLE=$TABLE,FV_LLM_MODEL=$MODEL_PROFILE,FV_LLM_TEMPERATURE=0.1,FV_GLINER_FUNCTION=$GLINER,FV_GLINER_TIMEOUT_S=4,FV_TRANSCRIBE_VOCABULARY=connect-atv-meds}"
echo "== Lambda $FN"
if aws lambda get-function --function-name $FN >/dev/null 2>&1; then
  aws lambda update-function-code --function-name $FN --zip-file fileb:///tmp/$FN.zip >/dev/null
  aws lambda wait function-updated-v2 --function-name $FN
  aws lambda update-function-configuration --function-name $FN --timeout 29 --memory-size 512 \
    --environment "$ENV" --role "$ROLE_ARN" >/dev/null
else
  for i in 1 2 3 4 5; do
    if aws lambda create-function --function-name $FN --runtime python3.12 --architectures arm64 \
        --handler handler.handler --role "$ROLE_ARN" --zip-file fileb:///tmp/$FN.zip \
        --timeout 29 --memory-size 512 --environment "$ENV" \
        --tags project=connect-atventures >/dev/null 2>/tmp/fn-create.err; then break; fi
    grep -q "cannot be assumed" /tmp/fn-create.err && { echo "   role not ready, retry $i"; sleep 8; continue; }
    cat /tmp/fn-create.err; exit 1
  done
fi
aws lambda wait function-updated-v2 --function-name $FN
# NOTE: no reserved concurrency (do NOT set to 1), no Function URL.

echo "== Seed"
aws lambda invoke --function-name $FN --cli-binary-format raw-in-base64-out \
  --payload '{"route":"POST /internal/seed","body":{}}' /tmp/seed.json >/dev/null && cat /tmp/seed.json; echo

# ---------------------------------------------------------------------------
# AUTH/API HOOK (was TODO; DONE 8 oct): Eric chose Cognito Identity Pool guest identities +
# API Gateway HTTP API with IAM (SigV4) auth on every route. Implemented in infra/api/expose.sh
# (re-runnable): EXPOSE=1 infra/api/deploy.sh. Verify: python3 infra/api/test_guest.py
# ---------------------------------------------------------------------------
if [ "${EXPOSE:-0}" = 1 ]; then
  bash infra/api/expose.sh
fi
echo "done"
