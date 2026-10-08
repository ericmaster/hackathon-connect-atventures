#!/usr/bin/env bash
# Re-runnable deploy of the SEPARATE Farmaenlace mock API (additive; does not touch the orchestrator Lambda).
#   infra/farmaenlace-mock/deploy.sh             -> table + role + Lambda + HTTP API (AWS_IAM) + seed + invoke policy
#   OPERATOR=1 infra/farmaenlace-mock/deploy.sh  -> also lets WSParticipantRole call it (manual verification only)
# Never prints credentials. us-east-1, tag project=connect-atventures.
set -euo pipefail
cd "$(dirname "$0")/../.."
export AWS_REGION=${AWS_REGION:-us-east-1} AWS_PAGER=""
R=$AWS_REGION
ACCT=$(aws sts get-caller-identity --query Account --output text)
TABLE=connect-atv-farmaenlace
FN=connect-atv-farmaenlace-mock
ROLE=connect-atv-farmaenlace-mock-role
API_NAME=connect-atv-farmaenlace-api
ORCH_ROLE=connect-atv-orchestrator-role
TAG_KV="Key=project,Value=connect-atventures"
ALLOWED=$ORCH_ROLE
[ "${OPERATOR:-0}" = 1 ] && ALLOWED="$ORCH_ROLE,WSParticipantRole"

echo "== DynamoDB $TABLE"
if ! aws dynamodb describe-table --table-name $TABLE >/dev/null 2>&1; then
  aws dynamodb create-table --table-name $TABLE \
    --attribute-definitions AttributeName=pk,AttributeType=S AttributeName=sk,AttributeType=S \
    --key-schema AttributeName=pk,KeyType=HASH AttributeName=sk,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST --tags $TAG_KV >/dev/null
fi
aws dynamodb wait table-exists --table-name $TABLE

echo "== IAM role $ROLE"
TRUST='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
if ! aws iam get-role --role-name $ROLE >/dev/null 2>&1; then
  aws iam create-role --role-name $ROLE --assume-role-policy-document "$TRUST" \
    --tags $TAG_KV --description "connect-atv Farmaenlace mock API Lambda (minimal)" >/dev/null
  NEW_ROLE=1
fi
aws iam put-role-policy --role-name $ROLE --policy-name farmaenlace-mock-minimal --policy-document "$(cat <<JSON
{"Version":"2012-10-17","Statement":[
 {"Sid":"Table","Effect":"Allow","Action":["dynamodb:GetItem","dynamodb:PutItem","dynamodb:DeleteItem","dynamodb:Query","dynamodb:Scan","dynamodb:BatchWriteItem","dynamodb:ConditionCheckItem"],
  "Resource":"arn:aws:dynamodb:$R:$ACCT:table/$TABLE"},
 {"Sid":"Logs","Effect":"Allow","Action":["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],
  "Resource":["arn:aws:logs:$R:$ACCT:log-group:/aws/lambda/$FN","arn:aws:logs:$R:$ACCT:log-group:/aws/lambda/$FN:*"]}
]}
JSON
)"
ROLE_ARN=$(aws iam get-role --role-name $ROLE --query Role.Arn --output text)
[ "${NEW_ROLE:-0}" = 1 ] && { echo "   waiting for IAM propagation"; sleep 12; }

echo "== Build zip"
B=$(mktemp -d)
cp services/farmaenlace-mock/app.py services/farmaenlace-mock/data.py services/api/store.py "$B"/
rm -f /tmp/$FN.zip; python3 -c "import shutil,sys; shutil.make_archive(sys.argv[1], 'zip', sys.argv[2])" /tmp/$FN "$B"

ENV="Variables={FV_TABLE=$TABLE,FM_ALLOWED_ROLES=\"$ALLOWED\"}"
echo "== Lambda $FN (allowed roles: $ALLOWED)"
if aws lambda get-function --function-name $FN >/dev/null 2>&1; then
  aws lambda update-function-code --function-name $FN --zip-file fileb:///tmp/$FN.zip >/dev/null
  aws lambda wait function-updated-v2 --function-name $FN
  aws lambda update-function-configuration --function-name $FN --timeout 10 --memory-size 512 \
    --environment "$ENV" --role "$ROLE_ARN" >/dev/null
else
  for i in 1 2 3 4 5; do
    if aws lambda create-function --function-name $FN --runtime python3.12 --architectures arm64 \
        --handler app.handler --role "$ROLE_ARN" --zip-file fileb:///tmp/$FN.zip \
        --timeout 10 --memory-size 512 --environment "$ENV" \
        --tags project=connect-atventures >/dev/null 2>/tmp/fm-create.err; then break; fi
    grep -q "cannot be assumed" /tmp/fm-create.err && { echo "   role not ready, retry $i"; sleep 8; continue; }
    cat /tmp/fm-create.err; exit 1
  done
fi
aws lambda wait function-updated-v2 --function-name $FN
FN_ARN=$(aws lambda get-function --function-name $FN --query Configuration.FunctionArn --output text)

echo "== Seed"
aws lambda invoke --function-name $FN --cli-binary-format raw-in-base64-out \
  --payload '{"route":"POST /internal/seed"}' /tmp/fm-seed.json >/dev/null && cat /tmp/fm-seed.json; echo

echo "== HTTP API $API_NAME (AWS_IAM on every route, no CORS: server-to-server only)"
API_ID=$(aws apigatewayv2 get-apis --query "Items[?Name=='$API_NAME'].ApiId | [0]" --output text)
if [ -z "$API_ID" ] || [ "$API_ID" = "None" ]; then
  API_ID=$(aws apigatewayv2 create-api --name $API_NAME --protocol-type HTTP --tags project=connect-atventures \
    --description "Mock of Farmaenlace backend (synthetic data) for connect-atv orchestrator" --query ApiId --output text)
fi
INTEG=$(aws apigatewayv2 get-integrations --api-id "$API_ID" --query "Items[?IntegrationUri=='$FN_ARN'].IntegrationId | [0]" --output text)
if [ -z "$INTEG" ] || [ "$INTEG" = "None" ]; then
  INTEG=$(aws apigatewayv2 create-integration --api-id "$API_ID" --integration-type AWS_PROXY --integration-uri "$FN_ARN" \
    --payload-format-version 2.0 --timeout-in-millis 8000 --query IntegrationId --output text)
fi
for RK in 'ANY /{proxy+}'; do
  if ! aws apigatewayv2 get-routes --api-id "$API_ID" --query "Items[].RouteKey" --output text | tr '\t' '\n' | grep -qxF "$RK"; then
    aws apigatewayv2 create-route --api-id "$API_ID" --route-key "$RK" --authorization-type AWS_IAM \
      --target "integrations/$INTEG" >/dev/null
  fi
done
for RID in $(aws apigatewayv2 get-routes --api-id "$API_ID" --query "Items[?AuthorizationType!='AWS_IAM'].RouteId" --output text); do
  aws apigatewayv2 update-route --api-id "$API_ID" --route-id "$RID" --authorization-type AWS_IAM >/dev/null
done
if ! aws apigatewayv2 get-stage --api-id "$API_ID" --stage-name '$default' >/dev/null 2>&1; then
  aws apigatewayv2 create-stage --api-id "$API_ID" --stage-name '$default' --auto-deploy \
    --default-route-settings ThrottlingRateLimit=50,ThrottlingBurstLimit=100 --tags project=connect-atventures >/dev/null
else
  aws apigatewayv2 update-stage --api-id "$API_ID" --stage-name '$default' \
    --default-route-settings ThrottlingRateLimit=50,ThrottlingBurstLimit=100 >/dev/null
fi
aws lambda add-permission --function-name $FN --statement-id apigw-$API_ID --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:$R:$ACCT:$API_ID/*/*" >/dev/null 2>&1 || true

echo "== Orchestrator may invoke (inline policy farmaenlace-mock-invoke on $ORCH_ROLE)"
aws iam put-role-policy --role-name $ORCH_ROLE --policy-name farmaenlace-mock-invoke --policy-document \
  "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":\"execute-api:Invoke\",\"Resource\":\"arn:aws:execute-api:$R:$ACCT:$API_ID/\$default/*\"}]}"

echo "FV_FARMAENLACE_URL=https://$API_ID.execute-api.$R.amazonaws.com"
echo "done"
