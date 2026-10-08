#!/usr/bin/env bash
# pin model rev in private S3. needs huggingface_hub (.venv-gliner) + aws creds.
set -euo pipefail
REPO=${REPO:-fastino/GLiNER2.5-multi-Decide}; REV=${REV:-a35a0cd3b7a0f00f2effc576f454cd48fa98aa5f}
B=${B:-connect-atv-gliner-build-325556500173}
D=$(python -c "from huggingface_hub import snapshot_download as d; print(d('$REPO', revision='$REV', allow_patterns=['*.json','*.safetensors']))")
aws s3 cp --recursive --follow-symlinks "$D/" "s3://$B/models/${REPO#*/}/$REV/" --region us-east-1
