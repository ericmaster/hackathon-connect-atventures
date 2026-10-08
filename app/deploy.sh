#!/usr/bin/env bash
# Build + manual deploy to AWS Amplify Hosting (no Git). Usage: ./deploy.sh
set -euo pipefail
cd "$(dirname "$0")"
APP_ID="${AMPLIFY_APP_ID:-d2bloxc35rzfqy}"   # not a secret
BRANCH="${AMPLIFY_BRANCH:-main}"
export AWS_REGION="${AWS_REGION:-us-east-1}"
export PATH="$HOME/.nvm/versions/node/v24.21.0/bin:$PATH"

npm run build
ZIP="$(mktemp -d)/build.zip"
(cd build && python3 -c 'import os,sys,zipfile
z=zipfile.ZipFile(sys.argv[1],"w",zipfile.ZIP_DEFLATED)
[z.write(os.path.join(r,f),os.path.relpath(os.path.join(r,f))) for r,_,fs in os.walk(".") for f in fs]' "$ZIP")

aws amplify get-branch --app-id "$APP_ID" --branch-name "$BRANCH" >/dev/null 2>&1 ||
	aws amplify create-branch --app-id "$APP_ID" --branch-name "$BRANCH" >/dev/null

read -r JOB URL < <(aws amplify create-deployment --app-id "$APP_ID" --branch-name "$BRANCH" \
	--query '[jobId,zipUploadUrl]' --output text)
curl -fsS -X PUT -H 'Content-Type: application/zip' --upload-file "$ZIP" "$URL"
aws amplify start-deployment --app-id "$APP_ID" --branch-name "$BRANCH" --job-id "$JOB" >/dev/null

while :; do
	S=$(aws amplify get-job --app-id "$APP_ID" --branch-name "$BRANCH" --job-id "$JOB" --query job.summary.status --output text)
	echo "job $JOB: $S"
	case $S in SUCCEED) break ;; FAILED | CANCELLED) exit 1 ;; esac
	sleep 5
done
echo "https://$BRANCH.$APP_ID.amplifyapp.com"
