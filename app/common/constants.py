from enum import StrEnum


class Topic(StrEnum):
    """고민 주제 (docs/api-spec.md - 카테고리)."""

    WORK = "일"
    RELATIONSHIP = "관계"
    MONEY = "돈"
    HEALTH = "건강"
    SELF = "나"
    ETC = "기타"


class Value(StrEnum):
    """기록의 대표 가치 (docs/api-spec.md - 카테고리)."""

    GROWTH = "성장"
    STABILITY = "안정"
    AUTONOMY = "자율"
    CONNECTION = "연결"
    RECOGNITION = "인정"
    FUN = "재미"
    EFFICIENCY = "효율"
    MEANING = "의미"
    RESPONSIBILITY = "책임"
    ETC = "기타"


class ConcernStatus(StrEnum):
    """고민 진행 상태."""

    PENDING = "PENDING"
    RESOLVED = "RESOLVED"
