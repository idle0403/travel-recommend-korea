"""
SSL 헬퍼 - SSL 인증서 문제 해결
"""

import ssl
import aiohttp

def create_ssl_context():
    """SSL 인증서 검증을 비활성화한 컨텍스트 생성"""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context

def create_http_session():
    """SSL 문제를 해결한 HTTP 세션 생성"""
    ssl_context = create_ssl_context()
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    return aiohttp.ClientSession(connector=connector)