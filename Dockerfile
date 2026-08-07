FROM public.ecr.aws/lambda/python:3.13

COPY requirements.txt requirements-lambda.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r requirements-lambda.txt --target "${LAMBDA_TASK_ROOT}"

COPY app/ ${LAMBDA_TASK_ROOT}/app/
COPY migrations/ ${LAMBDA_TASK_ROOT}/migrations/
COPY alembic.ini ${LAMBDA_TASK_ROOT}/

# 마이그레이션 함수는 template.yaml 의 ImageConfig.Command 로 핸들러를 덮어쓴다.
CMD ["app.lambda_handler.handler"]
