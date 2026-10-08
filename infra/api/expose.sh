#!/usr/bin/env bash
# Public exposure (decided by Eric 8 oct): Cognito Identity Pool with GUEST identities (no user pool, no login,
# classic flow OFF, no Pinpoint) + API Gateway HTTP API `connect-atv-api` with IAM (SigV4) auth on EVERY route.
# Re-runnable. Prints only ids/URLs, never credentials.
set -euo pipefail
export AWS_REGION=${AWS_REGION:-us-east-1} AWS_PAGER=""
R=$AWS_REGION
ACCT=$(aws sts get-caller-identity --query Account --output text)
FN=connect-atv-orchestrator
API_NAME=connect-atv-api
POOL_NAME=connect_atv_guest
GUEST_ROLE=connect-atv-guest-role
FN_ARN=arn:aws:lambda:$R:$ACCT:function:$FN
ORIGINS='["https://main.d2bloxc35rzfqy.amplifyapp.com","https://main.dfsvbpju4hwi2.amplifyapp.com","http://localhost:5173"]'

echo "== HTTP API $API_NAME"
API_ID=$(aws apigatewayv2 get-apis --query "Items[?Name=='$API_NAME'].ApiId | [0]" --output text)
CORS="{\"AllowOrigins\":$ORIGINS,\"AllowMethods\":[\"GET\",\"POST\",\"OPTIONS\"],\"AllowHeaders\":[\"authorization\",\"content-type\",\"x-amz-date\",\"x-amz-security-token\",\"x-amz-content-sha256\"],\"MaxAge\":600}"
if [ "$API_ID" = "None" ] || [ -z "$API_ID" ]; then
  API_ID=$(aws apigatewayv2 create-api --name $API_NAME --protocol-type HTTP --cors-configuration "$CORS" \
    --tags project=connect-atventures --query ApiId --output text)
else
  aws apigatewayv2 update-api --api-id "$API_ID" --cors-configuration "$CORS" >/dev/null
fi
INTEG=$(aws apigatewayv2 get-integrations --api-id "$API_ID" --query "Items[?IntegrationUri=='$FN_ARN'].IntegrationId | [0]" --output text)
if [ "$INTEG" = "None" ] || [ -z "$INTEG" ]; then
  INTEG=$(aws apigatewayv2 create-integration --api-id "$API_ID" --integration-type AWS_PROXY --integration-uri "$FN_ARN" \
    --payload-format-version 2.0 --timeout-in-millis 29000 --query IntegrationId --output text)
fi
EXISTING=$(aws apigatewayv2 get-routes --api-id "$API_ID" --query "Items[].RouteKey" --output text)
for RK in "POST /session" "POST /turn" "POST /action" "POST /demo/reset" "POST /voice/tts" "POST /voice/stt-url" "GET /admin/{service}"; do
  if ! grep -qF "$RK" <<<"$EXISTING"; then
    aws apigatewayv2 create-route --api-id "$API_ID" --route-key "$RK" --authorization-type AWS_IAM \
      --target "integrations/$INTEG" >/dev/null
  fi
done
# every route must be IAM
for RID in $(aws apigatewayv2 get-routes --api-id "$API_ID" --query "Items[?AuthorizationType!='AWS_IAM'].RouteId" --output text); do
  aws apigatewayv2 update-route --api-id "$API_ID" --route-id "$RID" --authorization-type AWS_IAM >/dev/null
done
if ! aws apigatewayv2 get-stage --api-id "$API_ID" --stage-name '$default' >/dev/null 2>&1; then
  aws apigatewayv2 create-stage --api-id "$API_ID" --stage-name '$default' --auto-deploy \
    --default-route-settings ThrottlingRateLimit=20,ThrottlingBurstLimit=40 --tags project=connect-atventures >/dev/null
else
  aws apigatewayv2 update-stage --api-id "$API_ID" --stage-name '$default' \
    --default-route-settings ThrottlingRateLimit=20,ThrottlingBurstLimit=40 >/dev/null
fi
aws lambda add-permission --function-name $FN --statement-id apigw-$API_ID --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:$R:$ACCT:$API_ID/*/*" >/dev/null 2>&1 || true
API_URL="https://$API_ID.execute-api.$R.amazonaws.com"

echo "== Identity pool $POOL_NAME (guest only, classic flow off)"
POOL_ID=$(aws cognito-identity list-identity-pools --max-results 60 --query "IdentityPools[?IdentityPoolName=='$POOL_NAME'].IdentityPoolId | [0]" --output text)
if [ "$POOL_ID" = "None" ] || [ -z "$POOL_ID" ]; then
  POOL_ID=$(aws cognito-identity create-identity-pool --identity-pool-name $POOL_NAME --allow-unauthenticated-identities \
    --no-allow-classic-flow --identity-pool-tags project=connect-atventures --query IdentityPoolId --output text)
fi

echo "== Guest role $GUEST_ROLE"
TRUST=$(cat <<JSON
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Federated":"cognito-identity.amazonaws.com"},
 "Action":"sts:AssumeRoleWithWebIdentity",
 "Condition":{"StringEquals":{"cognito-identity.amazonaws.com:aud":"$POOL_ID"},
              "ForAnyValue:StringLike":{"cognito-identity.amazonaws.com:amr":"unauthenticated"}}}]}
JSON
)
if ! aws iam get-role --role-name $GUEST_ROLE >/dev/null 2>&1; then
  aws iam create-role --role-name $GUEST_ROLE --assume-role-policy-document "$TRUST" \
    --tags Key=project,Value=connect-atventures --description "Cognito guest: invoke connect-atv-api only" >/dev/null
  sleep 8
else
  aws iam update-assume-role-policy --role-name $GUEST_ROLE --policy-document "$TRUST"
fi
aws iam put-role-policy --role-name $GUEST_ROLE --policy-name invoke-connect-atv-api --policy-document \
  "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":\"execute-api:Invoke\",\"Resource\":\"arn:aws:execute-api:$R:$ACCT:$API_ID/\$default/*\"}]}"
GUEST_ARN=$(aws iam get-role --role-name $GUEST_ROLE --query Role.Arn --output text)
aws cognito-identity set-identity-pool-roles --identity-pool-id "$POOL_ID" --roles unauthenticated="$GUEST_ARN"

echo "API_URL=$API_URL"
echo "IDENTITY_POOL_ID=$POOL_ID"
echo "REGION=$R"
