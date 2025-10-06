"""
Notion 서비스

Notion API 연동으로 여행 계획 자동 문서화
"""

import os
import requests
from typing import Dict, Any, List
from datetime import datetime

class NotionService:
    def __init__(self):
        self.token = os.getenv("NOTION_TOKEN")
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        self.base_url = "https://api.notion.com/v1"
    
    def create_travel_plan_page(self, plan_data: Dict[str, Any]) -> str:
        """여행 계획 Notion 페이지 생성"""
        if not self.token or not self.database_id:
            print("Notion 토큰 또는 데이터베이스 ID가 설정되지 않았습니다")
            return "https://notion.so/mock-page"
        
        headers = {
            "Authorization": "Bearer " + str(self.token),
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # 안전한 제목 생성
        title = plan_data.get('title', 'AI 여행 계획')
        if isinstance(title, dict):
            title = 'AI 여행 계획'
        
        page_title = "🇰🇷 " + str(title) + " - " + datetime.now().strftime('%Y-%m-%d')
        
        # 페이지 데이터 구성
        page_data = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "이름": {
                    "title": [{
                        "text": {
                            "content": page_title
                        }
                    }]
                }
            },
            "children": self._build_page_content(plan_data)
        }
        
        try:
            response = requests.post(
                self.base_url + "/pages",
                headers=headers,
                json=page_data
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("url", "https://notion.so/created-page")
            else:
                print("Notion API 오류: " + str(response.status_code) + " - " + str(response.text))
                return "https://notion.so/error-page"
        except Exception as e:
            print("Notion 페이지 생성 오류: " + str(e))
            return "https://notion.so/error-page"
    
    def _build_page_content(self, plan_data: Dict[str, Any]) -> List[Dict]:
        """Notion 페이지 콘텐츠 구성"""
        content = []
        
        # 헤더
        content.append({
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{
                    "text": {"content": "🗺️ 여행 일정"}
                }]
            }
        })
        
        # 요약 정보
        summary = plan_data.get("summary", "")
        if summary:
            content.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{
                        "text": {"content": str(summary)}
                    }],
                    "icon": {"emoji": "ℹ️"}
                }
            })
        
        # 일정 목록
        itinerary = plan_data.get("itinerary", [])
        if itinerary:
            content.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{
                        "text": {"content": "📅 상세 일정"}
                    }]
                }
            })
            
            for i, item in enumerate(itinerary):
                # 시간 및 장소
                time_str = str(item.get('time', str(9+i) + ':00'))
                name_str = str(item.get('place_name', item.get('name', item.get('activity', '활동'))))
                
                content.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{
                            "text": {
                                "content": time_str + " - " + name_str
                            }
                        }]
                    }
                })
                
                # 상세 정보
                details = []
                if item.get("description"):
                    details.append("📝 " + str(item['description']))
                if item.get("address") or item.get("location"):
                    location = item.get("address") or item.get("location")
                    details.append("📍 " + str(location))
                if item.get("transportation"):
                    details.append("🚇 " + str(item['transportation']))
                if item.get("duration"):
                    details.append("⏱️ 소요시간: " + str(item['duration']))
                if item.get("price"):
                    details.append("💰 비용: " + str(item['price']))
                if item.get("rating"):
                    details.append("⭐ 평점: " + str(item['rating']) + "/5")
                
                if details:
                    content.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{
                                "text": {"content": "\n".join(details)}
                            }]
                        }
                    })
        
        # 총 비용
        total_cost = plan_data.get("total_cost")
        if total_cost:
            content.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{
                        "text": {"content": "💰 예상 총 비용"}
                    }]
                }
            })
            
            # total_cost가 dict인 경우 amount 추출
            if isinstance(total_cost, dict):
                cost_amount = total_cost.get('amount', 0)
            else:
                cost_amount = total_cost
            
            content.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{
                        "text": {"content": str(cost_amount) + "원"}
                    }],
                    "icon": {"emoji": "💳"}
                }
            })
        
        # 생성 정보
        content.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "text": {
                        "content": "\n🤖 AI 생성 시간: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                }]
            }
        })
        
        return content