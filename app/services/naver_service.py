"""
네이버 API 서비스

네이버 검색 API를 통한 블로그 검색 및 장소 정보 수집
"""

import os
import aiohttp
import asyncio
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from app.services.ssl_helper import create_http_session

class NaverService:
    def __init__(self):
        self.client_id = os.getenv("NAVER_CLIENT_ID")
        self.client_secret = os.getenv("NAVER_CLIENT_SECRET")
        self.base_url = "https://openapi.naver.com/v1"
    
    async def search_blogs(self, query: str, display: int = 5) -> List[Dict[str, Any]]:
        """네이버 블로그 검색"""
        if not self.client_id or not self.client_secret:
            return self._mock_blog_results(query)
        
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
        
        params = {
            "query": query,
            "display": display,
            "sort": "sim"  # 정확도순
        }
        
        try:
            async with create_http_session() as session:
                async with session.get(
                    f"{self.base_url}/search/blog.json",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._process_blog_results(data.get("items", []))
                    else:
                        return self._mock_blog_results(query)
        except Exception as e:
            print(f"네이버 블로그 검색 오류: {str(e)}")
            return self._mock_blog_results(query)
    
    async def search_places(self, query: str, display: int = 5) -> List[Dict[str, Any]]:
        """네이버 지역 검색"""
        if not self.client_id or not self.client_secret:
            return self._mock_place_results(query)
        
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
        
        params = {
            "query": query,
            "display": display
        }
        
        try:
            async with create_http_session() as session:
                async with session.get(
                    f"{self.base_url}/search/local.json",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_place_results(data.get("items", []))
                    else:
                        return self._mock_place_results(query)
        except Exception as e:
            print(f"네이버 지역 검색 오류: {str(e)}")
            return self._mock_place_results(query)
    
    async def _process_blog_results(self, items: List[Dict]) -> List[Dict[str, Any]]:
        """블로그 검색 결과 처리 및 상세 내용 분석"""
        processed_results = []
        
        for item in items:
            # 블로그 상세 내용 분석
            detailed_content = await self._get_blog_summary(item.get("link", ""))
            
            blog_info = {
                "title": self._clean_html(item.get("title", "")),
                "description": self._clean_html(item.get("description", "")),
                "link": item.get("link", ""),
                "url": item.get("link", ""),
                "blogger": item.get("bloggername", ""),
                "date": item.get("postdate", ""),
                "content_analysis": detailed_content if isinstance(detailed_content, dict) else {"summary": detailed_content},
                "summary": detailed_content.get("summary", detailed_content) if isinstance(detailed_content, dict) else detailed_content
            }
            processed_results.append(blog_info)
        
        return processed_results
    
    async def _get_blog_summary(self, url: str) -> str:
        """블로그 내용 요약 (실제 내용 크롤링)"""
        if not self._is_safe_url(url):
            return "안전하지 않은 URL입니다."
            
        try:
            async with create_http_session() as session:
                async with session.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; TravelBot/1.0)'
                }) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._extract_detailed_blog_content(html)
        except Exception as e:
            print(f"블로그 크롤링 오류: {str(e)}")
        
        return {"summary": "블로그 내용을 불러올 수 없습니다.", "keywords": [], "rating": 0, "sentiment": "중립적", "highlights": []}
    
    def _extract_detailed_blog_content(self, html: str) -> Dict[str, Any]:
        """네이버 블로그 상세 내용 추출 및 분석"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # 네이버 블로그 특화 선택자
        selectors = [
            '.se-main-container',  # 스마트에디터
            '.post-view',          # 일반 블로그
            '#postViewArea',       # 구버전
            '.blog-content'        # 기타
        ]
        
        content = ""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                content = element.get_text(strip=True)
                break
        
        if not content:
            content = soup.get_text(strip=True)
        
        # 내용 정리
        import re
        content = re.sub(r'\s+', ' ', content)
        
        # 상세 분석
        analysis = self._analyze_blog_content(content)
        
        return {
            "content": content[:500] + "..." if len(content) > 500 else content,
            "keywords": analysis["keywords"],
            "rating": analysis["rating"],
            "sentiment": analysis["sentiment"],
            "highlights": analysis["highlights"],
            "summary": analysis["summary"]
        }
    
    def _analyze_blog_content(self, content: str) -> Dict[str, Any]:
        """블로그 내용 상세 분석"""
        # 키워드 추출
        keywords = self._extract_keywords(content)
        
        # 평점 추출
        rating = self._extract_rating(content)
        
        # 감정 분석
        sentiment = self._analyze_sentiment(content)
        
        # 하이라이트 추출
        highlights = self._extract_highlights(content)
        
        # 요약 생성
        summary = content[:200] + "..." if len(content) > 200 else content
        
        return {
            "keywords": keywords,
            "rating": rating,
            "sentiment": sentiment,
            "highlights": highlights,
            "summary": summary
        }
    
    def _extract_rating(self, content: str) -> float:
        """내용에서 평점 추출"""
        import re
        
        # 평점 패턴 찾기
        rating_patterns = [
            r'(\d+)점',
            r'★+',
            r'⭐+',
            r'(\d+)/5',
            r'(\d+)/10'
        ]
        
        for pattern in rating_patterns:
            matches = re.findall(pattern, content)
            if matches:
                if pattern in ['★+', '⭐+']:
                    return len(matches[0])
                else:
                    try:
                        return float(matches[0])
                    except:
                        continue
        
        # 긍정/부정 키워드로 추정 평점
        positive_count = len([w for w in ['맛있', '좋', '추천', '만족'] if w in content])
        negative_count = len([w for w in ['별로', '아쉬', '실망'] if w in content])
        
        if positive_count > negative_count:
            return 4.0 + (positive_count * 0.2)
        elif negative_count > positive_count:
            return 3.0 - (negative_count * 0.3)
        else:
            return 3.5
    
    def _analyze_sentiment(self, content: str) -> str:
        """감정 분석"""
        positive_words = ['맛있', '좋', '추천', '만족', '훌륭', '최고']
        negative_words = ['별로', '아쉬', '실망', '불친절', '비싸']
        
        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)
        
        if positive_count > negative_count * 2:
            return "매우 긍정적"
        elif positive_count > negative_count:
            return "긍정적"
        elif negative_count > positive_count:
            return "부정적"
        else:
            return "중립적"
    
    def _extract_highlights(self, content: str) -> List[str]:
        """주요 내용 하이라이트 추출"""
        import re
        
        # 문장 단위로 분리
        sentences = re.split(r'[.!?]', content)
        
        highlights = []
        highlight_keywords = ['맛있', '추천', '좋', '최고', '특별', '인상적', '기억에 남']
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10 and any(keyword in sentence for keyword in highlight_keywords):
                highlights.append(sentence[:100] + "..." if len(sentence) > 100 else sentence)
                if len(highlights) >= 3:  # 최대 3개까지
                    break
        
        return highlights
    
    def _extract_keywords(self, content: str) -> list:
        """여행/맛집 관련 키워드 추출"""
        positive_words = ['맛있', '좋', '추천', '만족', '훌륭', '최고', '깔끔', '친절', '분위기', '가성비']
        negative_words = ['별로', '아쉬', '실망', '불친절', '비싸', '맛없']
        
        found_keywords = []
        for word in positive_words + negative_words:
            if word in content:
                found_keywords.append(word)
        
        return found_keywords[:5]
    
    def _is_safe_url(self, url: str) -> bool:
        """안전한 URL 검증"""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            allowed_domains = ['blog.naver.com', 'post.naver.com', 'cafe.naver.com']
            return any(domain in parsed.netloc.lower() for domain in allowed_domains)
        except:
            return False
    
    def _process_place_results(self, items: List[Dict]) -> List[Dict[str, Any]]:
        """장소 검색 결과 처리"""
        processed_results = []
        
        for item in items:
            place_info = {
                "name": self._clean_html(item.get("title", "")),
                "address": item.get("address", ""),
                "road_address": item.get("roadAddress", ""),
                "phone": item.get("telephone", ""),
                "category": item.get("category", ""),
                "description": self._clean_html(item.get("description", "")),
                "lat": float(item.get("mapy", 0)) / 10000000 if item.get("mapy") else 0,
                "lng": float(item.get("mapx", 0)) / 10000000 if item.get("mapx") else 0
            }
            processed_results.append(place_info)
        
        return processed_results
    
    def _clean_html(self, text: str) -> str:
        """HTML 태그 제거"""
        import re
        return re.sub(r'<[^>]+>', '', text)
    
    def _mock_blog_results(self, query: str) -> List[Dict[str, Any]]:
        """API 키가 없을 때 모의 블로그 결과"""
        import urllib.parse
        encoded_query = urllib.parse.quote(f"{query} 후기")
        
        return [
            {
                "title": f"{query} 후기 - 네이버 블로그",
                "description": f"{query}에 대한 상세한 후기와 팁을 공유합니다.",
                "link": f"https://search.naver.com/search.naver?where=blog&query={encoded_query}",
                "blogger": "여행러버",
                "date": "20241201",
                "summary": f"{query}는 정말 좋은 곳이었습니다. 특히 음식이 맛있고 분위기가 좋아서 추천합니다."
            },
            {
                "title": f"{query} 맛집 리뷰",
                "description": f"{query} 실제 방문 후기입니다.",
                "link": f"https://search.naver.com/search.naver?where=blog&query={encoded_query}",
                "blogger": "맛집탐험가",
                "date": "20241130",
                "summary": f"직접 가본 {query} 솔직한 후기. 사진과 함께 상세한 리뷰를 남깁니다."
            },
            {
                "title": f"{query} 방문 후기",
                "description": f"{query} 직접 방문한 솔직한 후기입니다.",
                "link": f"https://blog.naver.com/PostSearchList.naver?blogId=&from=postList&query={encoded_query}",
                "blogger": "맛집매니아",
                "date": "20241129",
                "summary": f"{query} 직접 가본 후기. 사진 많이 찍어왔어요. 정말 추천합니다!"
            }
        ]
    
    def _mock_place_results(self, query: str) -> List[Dict[str, Any]]:
        """API 키가 없을 때 모의 장소 결과"""
        return [
            {
                "name": query,
                "address": "서울시 강남구",
                "road_address": "서울시 강남구 테헤란로 123",
                "phone": "02-1234-5678",
                "category": "음식점",
                "description": f"{query}에 대한 정보입니다.",
                "lat": 37.5663,
                "lng": 126.8247
            }
        ]