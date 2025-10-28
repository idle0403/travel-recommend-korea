"""
문자열 유사도 검사 유틸리티

장소 이름의 유사도를 계산하여 중복 여부를 판단합니다.
"""

from typing import Tuple
import re


def levenshtein_distance(s1: str, s2: str) -> int:
    """Levenshtein Distance 계산 (편집 거리)"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # 삽입, 삭제, 대체 비용 계산
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def normalize_place_name(name: str) -> str:
    """장소 이름 정규화"""
    if not name:
        return ""
    
    # 소문자 변환
    name = name.lower()
    
    # 공백 정규화
    name = re.sub(r'\s+', '', name)
    
    # 특수문자 제거
    name = re.sub(r'[^\w가-힣]', '', name)
    
    # 지점명 제거 (예: "스타벅스 강남점" -> "스타벅스강남")
    name = re.sub(r'(점|지점|매장|본점|분점)$', '', name)
    
    return name


def calculate_similarity(s1: str, s2: str) -> float:
    """
    두 문자열의 유사도 계산 (0.0 ~ 1.0)
    
    Returns:
        1.0: 완전히 동일
        0.0: 완전히 다름
    """
    # 정규화
    s1_norm = normalize_place_name(s1)
    s2_norm = normalize_place_name(s2)
    
    # 완전 일치
    if s1_norm == s2_norm:
        return 1.0
    
    # 한 문자열이 다른 문자열에 포함되는 경우
    if s1_norm in s2_norm or s2_norm in s1_norm:
        return 0.9
    
    # Levenshtein 거리 기반 유사도
    max_len = max(len(s1_norm), len(s2_norm))
    if max_len == 0:
        return 0.0
    
    distance = levenshtein_distance(s1_norm, s2_norm)
    similarity = 1.0 - (distance / max_len)
    
    return similarity


def are_similar_places(name1: str, name2: str, threshold: float = 0.85) -> bool:
    """
    두 장소가 유사한지 판단
    
    Args:
        name1: 첫 번째 장소 이름
        name2: 두 번째 장소 이름
        threshold: 유사도 임계값 (기본: 0.85)
    
    Returns:
        True: 유사함 (중복으로 간주)
        False: 다름
    """
    similarity = calculate_similarity(name1, name2)
    return similarity >= threshold


def calculate_coordinate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    두 좌표 간의 거리 계산 (미터 단위)
    
    Haversine formula 사용
    """
    import math
    
    # 지구 반지름 (미터)
    R = 6371000
    
    # 라디안 변환
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    # Haversine formula
    a = math.sin(delta_lat / 2) ** 2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * \
        math.sin(delta_lng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


def are_same_location(lat1: float, lng1: float, lat2: float, lng2: float, threshold: float = 50.0) -> bool:
    """
    두 좌표가 같은 위치인지 판단
    
    Args:
        lat1, lng1: 첫 번째 좌표
        lat2, lng2: 두 번째 좌표
        threshold: 거리 임계값 (미터, 기본: 50m)
    
    Returns:
        True: 같은 위치 (중복으로 간주)
        False: 다른 위치
    """
    distance = calculate_coordinate_distance(lat1, lng1, lat2, lng2)
    return distance <= threshold


# 테스트 함수
if __name__ == "__main__":
    # 테스트 케이스
    test_cases = [
        ("스타벅스 강남점", "스타벅스강남점", True),
        ("스타벅스 강남점", "스타벅스 서초점", False),
        ("경복궁", "경복궁 입구", True),
        ("남산타워", "N서울타워", False),
        ("명동 쇼핑거리", "명동쇼핑거리", True),
    ]
    
    print("=== 문자열 유사도 테스트 ===")
    for name1, name2, expected in test_cases:
        similarity = calculate_similarity(name1, name2)
        is_similar = are_similar_places(name1, name2)
        result = "✅" if is_similar == expected else "❌"
        print(f"{result} '{name1}' vs '{name2}': {similarity:.2f} -> {is_similar}")
    
    print("\n=== 좌표 거리 테스트 ===")
    # 경복궁과 가까운 위치
    distance = calculate_coordinate_distance(37.5796, 126.9770, 37.5800, 126.9775)
    print(f"거리: {distance:.1f}m")
    print(f"같은 위치: {are_same_location(37.5796, 126.9770, 37.5800, 126.9775)}")

