"""
블로그 크롤링 서비스

네이버 블로그 내용을 실제로 크롤링하여 후기 정보 추출
"""

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import re
from urllib.parse import urljoin, urlparse
from app.services.ssl_helper import create_http_session

class BlogCrawlerService:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    
    async def get_blog_content(self, blog_url: str) -> Dict[str, Any]:
        """블로그 내용 크롤링 및 요약"""
        # URL 검증
        if not self._is_safe_url(blog_url):
            return {"error": "비허용된 URL입니다"}
        
        try:
            async with create_http_session() as session:
                async with session.get(
                    blog_url, 
                    timeout=10,
                    headers=self.headers,
                    allow_redirects=True,
                    max_redirects=3
                ) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._extract_blog_content(html, blog_url)
        except Exception as e:
            print(f"블로그 크롤링 오류: {str(e)}")
        
        return {"error": "블로그 내용을 가져올 수 없습니다"}
    
    def _extract_blog_content(self, html: str, url: str) -> Dict[str, Any]:
        """HTML에서 블로그 내용 추출"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # 네이버 블로그 특화 선택자
        content_selectors = [
            '.se-main-container',  # 스마트에디터
            '.post-view',          # 일반 블로그
            '#postViewArea',       # 구버전
            '.blog-content'        # 기타
        ]
        
        content = ""
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                content = element.get_text(strip=True)
                break
        
        if not content:
            content = soup.get_text(strip=True)
        
        # 내용 정리
        content = re.sub(r'\s+', ' ', content)
        content = content[:1000]  # 1000자로 제한
        
        # 키워드 추출
        keywords = self._extract_keywords(content)
        
        # 평점 추출 시도
        rating = self._extract_rating(content)
        
        return {
            "content": content,
            "keywords": keywords,
            "rating": rating,
            "url": url,
            "summary": content[:200] + "..." if len(content) > 200 else content,
            "crawled": True,
            "length": len(content)
        }
    
    def _extract_keywords(self, content: str) -> List[str]:
        """내용에서 키워드 추출"""
        positive_words = ['맛있', '좋', '추천', '만족', '훌륭', '최고', '깔끔', '친절']
        negative_words = ['별로', '아쉬', '실망', '불친절', '비싸']
        
        keywords = []
        for word in positive_words + negative_words:
            if word in content:
                keywords.append(word)
        
        return keywords[:5]  # 상위 5개만
    
    def _extract_rating(self, content: str) -> float:
        """내용에서 평점 추출 시도"""
        rating_patterns = [
            r'(\d+)점',
            r'★+',
            r'⭐+',
            r'(\d+)/5',
            r'(\d+)\/10'
        ]
        
        for pattern in rating_patterns:
            matches = re.findall(pattern, content)
            if matches:
                if pattern == r'★+' or pattern == r'⭐+':
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
    
    async def get_multiple_blog_contents(self, blog_urls: List[str]) -> List[Dict[str, Any]]:
        """여러 블로그 동시 크롤링"""
        tasks = [self.get_blog_content(url) for url in blog_urls[:5]]  # 최대 5개
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for result in results:
            if isinstance(result, dict) and "error" not in result:
                valid_results.append(result)
        
        return valid_results
    
    def _is_safe_url(self, url: str) -> bool:
        """안전한 URL인지 검증"""
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            # 허용된 도메인만 허용
            allowed_domains = [
                'blog.naver.com',
                'post.naver.com', 
                'cafe.naver.com',
                'brunch.co.kr',
                'tistory.com',
                'daum.net'
            ]
            
            domain = parsed.netloc.lower()
            return any(allowed_domain in domain for allowed_domain in allowed_domains)
        except:
            return False