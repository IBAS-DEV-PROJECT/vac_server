import json
from functools import lru_cache
from typing import Any


@lru_cache(maxsize=8)
def get_secret(secret_arn: str, region_name: str | None = None) -> dict[str, Any]:
    """Secrets Manager에서 시크릿을 조회한다.

    Lambda 실행 환경이 재사용되는 동안 결과를 캐시하여 콜드 스타트 이후의
    호출에서는 추가 API 요청이 발생하지 않도록 한다.
    """
    import boto3  # Lambda 실행 환경에서만 필요하므로 지연 임포트한다.

    client = boto3.client("secretsmanager", region_name=region_name)
    response = client.get_secret_value(SecretId=secret_arn)
    return json.loads(response["SecretString"])
