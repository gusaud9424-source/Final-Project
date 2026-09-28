from dataclasses import dataclass
from typing import Optional


@dataclass
class PracticeResult:
    output: str
    success: bool


class PracticeBuilder:
    """실습 모듈 공통 인터페이스. 6개 취약점 모듈이 각자 구현해 PRACTICE_BUILDERS에 등록한다."""

    difficulties = ()

    def validate_input(self, difficulty: str, user_input) -> Optional[str]:
        """입력이 유효하지 않으면 에러 메시지, 유효하면 None"""
        raise NotImplementedError

    def run(self, difficulty: str, user_input: str) -> PracticeResult:
        """실습 실행 결과. 성공 판정(flag 비교 등)은 구현체 책임"""
        raise NotImplementedError

    def hints(self, difficulty: str) -> list:
        """단계별 힌트. 정답 자체가 아니라 접근 방법을 단계적으로 제시"""
        return []
