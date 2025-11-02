"""
FastAPI 메인 애플리케이션

한국 여행 플래너 API 서버의 진입점입니다.
CORS 설정, 라우터 등록, 미들웨어 설정을 담당합니다.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os

# 환경변수 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.api.endpoints import router as api_router
from app.api.streaming_endpoints import router as streaming_router  # 🆕 SSE
# from app.api.user_endpoints import router as user_router  # 로그인 제거로 비활성화

# FastAPI 앱 생성
app = FastAPI(
    title="🇰🇷 스마트 한국 여행 플래너 API",
    description="AI 기반 맞춤형 한국 여행 계획 생성 서비스",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용 - 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(api_router, prefix="/api/travel", tags=["travel"])
# app.include_router(user_router, prefix="/api/users", tags=["users"])  # 로그인 제거
app.include_router(streaming_router, prefix="/api/travel", tags=["streaming"])  # 🆕 SSE

def get_frontend_path():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

# 정적 파일 서빙 (프론트엔드)
frontend_path = get_frontend_path()
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    
@app.get("/script.js")
async def serve_script():
    script_file = os.path.join(get_frontend_path(), "script.js")
    if os.path.exists(script_file):
        return FileResponse(script_file, media_type="application/javascript")
    return {"error": "Script not found"}

@app.get("/test.html")
async def serve_test():
    test_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test.html")
    if os.path.exists(test_file):
        return FileResponse(test_file)
    return {"error": "Test file not found"}

@app.get("/debug.html")
async def serve_debug():
    debug_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "debug.html")
    if os.path.exists(debug_file):
        return FileResponse(debug_file)
    return {"error": "Debug file not found"}

@app.get("/simple.html")
async def serve_simple():
    simple_file = os.path.join(get_frontend_path(), "simple.html")
    if os.path.exists(simple_file):
        return FileResponse(simple_file)
    return {"error": "Simple file not found"}

@app.get("/simple.js")
async def serve_simple_js():
    simple_js = os.path.join(get_frontend_path(), "simple.js")
    if os.path.exists(simple_js):
        return FileResponse(simple_js, media_type="application/javascript")
    return {"error": "Simple JS not found"}

@app.get("/results.html")
async def serve_results():
    results_file = os.path.join(get_frontend_path(), "results.html")
    if os.path.exists(results_file):
        return FileResponse(results_file)
    return {"error": "Results page not found"}

@app.get("/")
async def serve_frontend():
    """프론트엔드 메인 페이지 서빙"""
    frontend_file = os.path.join(get_frontend_path(), "index.html")
    if os.path.exists(frontend_file):
        return FileResponse(frontend_file)
    return {"message": "🇰🇷 스마트 한국 여행 플래너 API", "docs": "/docs"}

# 🆕 404 페이지 핸들러 (login.html, register.html 등 삭제된 페이지)
@app.get("/login.html")
@app.get("/register.html")
@app.get("/history.html")
async def serve_404_pages():
    """삭제된 페이지 접근 시 안내 페이지 표시"""
    notfound_file = os.path.join(get_frontend_path(), "404.html")
    if os.path.exists(notfound_file):
        return FileResponse(notfound_file)
    return {"message": "이 페이지는 제거되었습니다. 메인 페이지(/)로 이동하세요. 로그인 없이 바로 사용 가능합니다."}

# Chrome DevTools 404 에러 방지
@app.get("/.well-known/appspecific/com.chrome.devtools.json")
async def chrome_devtools():
    return JSONResponse({"version": "1.0", "name": "Travel Planner"})

@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "Korean Travel Planner API",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)