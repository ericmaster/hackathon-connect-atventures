FROM public.ecr.aws/lambda/python:3.12
RUN pip install --no-cache-dir torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir "gliner2[local]==2.0.0" "transformers==4.57.6"
ARG MODEL_ID=fastino/GLiNER2.5-Decide
ARG MODEL_REV=5a7adf72a23b4d311abae6ce050d7f0012bb3416
RUN python -c "from huggingface_hub import snapshot_download as d; d('${MODEL_ID}', revision='${MODEL_REV}', local_dir='/opt/model')"
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 MODEL_ID=${MODEL_ID} MODEL_DIR=/opt/model HF_HOME=/tmp/hf
COPY app.py ${LAMBDA_TASK_ROOT}/
CMD ["app.handler"]
