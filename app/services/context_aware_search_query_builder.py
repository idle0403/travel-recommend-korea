"""
컨텍스트 인지 검색 쿼리 빌더 (Context-Aware Search Query Builder)

계층적 지역 정보와 키워드를 조합하여
최적의 검색 쿼리 리스트를 생성합니다.
"""

from typing import Dict, Any, List


class ContextAwareSearchQueryBuilder:
    """컨텍스트를 최대한 보존하는 검색 쿼리 생성"""
    
    def build_search_queries(
        self, 
        location_hierarchy: Dict[str, Any], 
        keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """
        다양한 검색 전략을 조합하여 우선순위별 검색 쿼리 생성
        
        Args:
            location_hierarchy: HierarchicalLocationExtractor 결과
            keywords: 추출된 키워드 리스트 (예: ['맛집', '카페'])
        
        Returns:
            [
                {
                    'query': 'LG사이언스파크 맛집',
                    'priority': 1,
                    'strategy': 'poi_level',
                    'expected_precision': 'very_high'
                },
                {
                    'query': '서울 강서구 마곡동 맛집',
                    'priority': 2,
                    'strategy': 'neighborhood_level',
                    'expected_precision': 'high'
                },
                ...
            ]
        """
        queries = []
        priority = 1
        
        city = location_hierarchy.get('city', '')
        district = location_hierarchy.get('district', '')
        neighborhood = location_hierarchy.get('neighborhood', '')
        poi_list = location_hierarchy.get('poi', [])
        context = location_hierarchy.get('context', {})
        
        # 전략 1: POI 레벨 (최고 우선순위)
        if poi_list:
            for poi in poi_list:
                for keyword in keywords:
                    queries.append({
                        'query': f"{poi} {keyword}",
                        'priority': priority,
                        'strategy': 'poi_level',
                        'expected_precision': 'very_high',
                        'location_level': 'poi'
                    })
            priority += 1
            
            # POI + 컨텍스트
            for poi in poi_list[:1]:  # 대표 POI 1개만
                for keyword in keywords:
                    context_text = self._build_context_text(context)
                    if context_text:
                        queries.append({
                            'query': f"{poi} {context_text} {keyword}",
                            'priority': priority,
                            'strategy': 'poi_context',
                            'expected_precision': 'very_high',
                            'location_level': 'poi'
                        })
            priority += 1
        
        # 전략 2: 동(Neighborhood) 레벨
        if neighborhood:
            for keyword in keywords:
                queries.append({
                    'query': f"{city} {district} {neighborhood} {keyword}",
                    'priority': priority,
                    'strategy': 'neighborhood_level',
                    'expected_precision': 'high',
                    'location_level': 'neighborhood'
                })
            priority += 1
            
            # 동 + 컨텍스트
            for keyword in keywords:
                context_text = self._build_context_text(context)
                if context_text:
                    queries.append({
                        'query': f"{neighborhood} {context_text} {keyword}",
                        'priority': priority,
                        'strategy': 'neighborhood_context',
                        'expected_precision': 'high',
                        'location_level': 'neighborhood'
                    })
            priority += 1
        
        # 전략 3: 구(District) 레벨
        if district:
            for keyword in keywords:
                queries.append({
                    'query': f"{city} {district} {keyword}",
                    'priority': priority,
                    'strategy': 'district_level',
                    'expected_precision': 'medium',
                    'location_level': 'district'
                })
            priority += 1
            
            # 구 + 컨텍스트
            for keyword in keywords:
                context_text = self._build_context_text(context)
                if context_text:
                    queries.append({
                        'query': f"{district} {context_text} {keyword}",
                        'priority': priority,
                        'strategy': 'district_context',
                        'expected_precision': 'medium',
                        'location_level': 'district'
                    })
            priority += 1
        
        # 전략 4: 도시 레벨 (낮은 우선순위 - 폴백용)
        if city:
            for keyword in keywords:
                queries.append({
                    'query': f"{city} {keyword}",
                    'priority': priority,
                    'strategy': 'city_level',
                    'expected_precision': 'low',
                    'location_level': 'city'
                })
            priority += 1
        
        # 중복 제거 (동일한 쿼리)
        seen = set()
        unique_queries = []
        for q in queries:
            if q['query'] not in seen:
                seen.add(q['query'])
                unique_queries.append(q)
        
        # 우선순위 순으로 정렬
        unique_queries.sort(key=lambda x: x['priority'])
        
        print(f"\n🔍 생성된 검색 쿼리 ({len(unique_queries)}개):")
        for i, q in enumerate(unique_queries[:5], 1):  # 상위 5개만 출력
            print(f"   {i}. [{q['strategy']}] {q['query']} (정밀도: {q['expected_precision']})")
        
        return unique_queries
    
    def _build_context_text(self, context: Dict[str, List[str]]) -> str:
        """컨텍스트를 텍스트로 변환"""
        parts = []
        
        # 시간대 우선
        if context.get('시간대'):
            parts.append(context['시간대'][0])
        
        # 타겟
        if context.get('타겟'):
            parts.append(context['타겟'][0])
        
        # 목적
        if context.get('목적'):
            parts.append(context['목적'][0])
        
        return ' '.join(parts)
    
    def get_primary_queries(
        self, 
        all_queries: List[Dict[str, Any]], 
        top_n: int = 5
    ) -> List[str]:
        """
        우선순위가 높은 상위 N개 쿼리 반환
        
        Args:
            all_queries: build_search_queries() 결과
            top_n: 반환할 쿼리 개수
        
        Returns:
            ['LG사이언스파크 맛집', '서울 강서구 마곡동 맛집', ...]
        """
        return [q['query'] for q in all_queries[:top_n]]
    
    def get_queries_by_strategy(
        self, 
        all_queries: List[Dict[str, Any]], 
        strategy: str
    ) -> List[str]:
        """
        특정 전략의 쿼리만 필터링
        
        Args:
            all_queries: build_search_queries() 결과
            strategy: 전략 이름 (예: 'poi_level', 'neighborhood_level')
        
        Returns:
            해당 전략의 쿼리 리스트
        """
        return [q['query'] for q in all_queries if q['strategy'] == strategy]

