# code + deps only. Weights pinned in S3 (MODEL_S3), fetched to /tmp at cold start: see upload-weights.sh
FROM public.ecr.aws/lambda/python:3.12
RUN pip install --no-cache-dir torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir "gliner2[local]==2.0.0" "transformers==4.57.6" protobuf sentencepiece
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HOME=/tmp/hf MODEL_ID=fastino/GLiNER2.5-multi-Decide
COPY app.py ${LAMBDA_TASK_ROOT}/
CMD ["app.handler"]
