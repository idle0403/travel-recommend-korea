"""
AWS Lambda 핸들러
FastAPI 애플리케이션을 Lambda에서 실행하기 위한 래퍼
Redis 서버를 Lambda 내에서 시작합니다.
"""

import os
import subprocess
import time
import threading
import shutil
import redis

# Redis 시작 (모듈 레벨에서 한 번만 실행)
_redis_started = False
_redis_lock = threading.Lock()
_redis_process = None

def find_redis_server():
    """Redis 서버 바이너리 경로 찾기"""
    possible_paths = [
        "/var/task/redis-server",
        "/usr/local/bin/redis-server",
        "/usr/bin/redis-server",
        "/bin/redis-server",
        "/opt/redis-server",
        shutil.which("redis-server")
    ]
    
    # 디버깅: 모든 경로 확인
    print("   🔍 Redis 바이너리 검색 중...")
    for path in possible_paths:
        if path:
            exists = os.path.exists(path)
            accessible = os.access(path, os.X_OK) if exists else False
            print(f"   - {path}: {'✅ 존재' if exists else '❌ 없음'} {'(실행 가능)' if accessible else '(실행 불가)' if exists else ''}")
            if exists and accessible:
                return path
    
    # 추가 검색: /usr/local/bin과 /usr/bin 디렉토리 전체 확인
    print("   🔍 추가 경로 검색 중...")
    for search_dir in ["/usr/local/bin", "/usr/bin", "/bin"]:
        if os.path.isdir(search_dir):
            try:
                files = os.listdir(search_dir)
                redis_files = [f for f in files if 'redis' in f.lower()]
                if redis_files:
                    print(f"   - {search_dir}에서 Redis 관련 파일 발견: {redis_files}")
                    for f in redis_files:
                        full_path = os.path.join(search_dir, f)
                        if 'server' in f.lower() and os.access(full_path, os.X_OK):
                            print(f"   ✅ 발견: {full_path}")
                            return full_path
            except:
                pass
    
    return None

def start_redis_if_needed():
    """Redis 서버를 백그라운드로 시작 (이미 시작되었으면 스킵)"""
    global _redis_started, _redis_process
    
    with _redis_lock:
        if _redis_started:
            return
        
        # Redis가 이미 실행 중인지 확인
        try:
            r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=1)
            r.ping()
            print("✅ Redis가 이미 실행 중입니다.")
            _redis_started = True
            return
        except Exception as e:
            print(f"🔍 Redis 연결 확인: {e}")
        
        # Redis 서버 바이너리 찾기
        redis_server = find_redis_server()
        if not redis_server:
            print("⚠️  Redis 서버 바이너리를 찾을 수 없습니다.")
            print("   가능한 경로 확인:")
            for path in ["/usr/local/bin/redis-server", "/usr/bin/redis-server", "/bin/redis-server"]:
                exists = os.path.exists(path)
                accessible = os.access(path, os.X_OK) if exists else False
                print(f"   - {path}: {'✅ 존재' if exists else '❌ 없음'} {'(실행 가능)' if accessible else '(실행 불가)' if exists else ''}")
            
            # Redis 버전 확인 시도
            if redis_server:
                try:
                    result = subprocess.run([redis_server, "--version"], 
                                          capture_output=True, text=True, timeout=2)
                    print(f"   Redis 버전 확인: {result.stdout.strip() if result.stdout else 'N/A'}")
                except:
                    pass
            
            print("   Redis 없이 계속 진행합니다.")
            return
        
        print(f"📍 Redis 서버 경로: {redis_server}")
        
        # Redis 서버 실행 가능 여부 확인
        if not os.access(redis_server, os.X_OK):
            print(f"⚠️  Redis 서버에 실행 권한이 없습니다: {redis_server}")
            # 실행 권한 부여 시도
            try:
                os.chmod(redis_server, 0o755)
                print(f"   실행 권한 부여 시도 완료")
            except Exception as e:
                print(f"   실행 권한 부여 실패: {e}")
                print("   Redis 없이 계속 진행합니다.")
                return
        
        # Redis 데이터 디렉토리 생성
        redis_dir = "/tmp/redis"
        os.makedirs(redis_dir, exist_ok=True)
        
        # Redis 설정 파일 생성
        redis_conf = os.path.join(redis_dir, "redis.conf")
        with open(redis_conf, 'w') as f:
            f.write(f"""# Redis 설정 (Lambda 환경)
port 6379
bind 127.0.0.1
dir {redis_dir}
daemonize yes
pidfile {redis_dir}/redis.pid
save ""
appendonly no
maxmemory 128mb
maxmemory-policy allkeys-lru
loglevel notice
logfile {redis_dir}/redis.log
""")
        
        try:
            print("🚀 Redis 서버 시작 중...")
            print(f"   Redis 서버: {redis_server}")
            print(f"   설정 파일: {redis_conf}")
            
            # Redis 로그 파일 경로
            redis_log = os.path.join(redis_dir, "redis.log")
            redis_err = os.path.join(redis_dir, "redis.err")
            
            # Redis 서버를 백그라운드로 시작 (daemonize yes로 설정했으므로 자동으로 백그라운드 실행)
            # Lambda 환경에서는 stdout/stderr를 파일로 리다이렉트
            with open(redis_log, 'w') as log_file, open(redis_err, 'w') as err_file:
                _redis_process = subprocess.Popen(
                    [redis_server, redis_conf],
                    stdout=log_file,
                    stderr=err_file,
                    cwd=redis_dir,
                    close_fds=True
                )
            
            print(f"   Redis 프로세스 PID: {_redis_process.pid}")
            
            # 프로세스가 즉시 종료되었는지 확인 (daemonize yes이므로 부모 프로세스는 즉시 종료됨)
            time.sleep(1)
            
            # PID 파일 확인 (daemonize yes일 때)
            pid_file = os.path.join(redis_dir, "redis.pid")
            if os.path.exists(pid_file):
                try:
                    with open(pid_file, 'r') as f:
                        redis_pid = int(f.read().strip())
                    print(f"   Redis 데몬 PID (PID 파일): {redis_pid}")
                except:
                    pass
            
            # 프로세스가 즉시 종료되었는지 확인 (daemonize yes이면 정상)
            if _redis_process.poll() is not None and _redis_process.returncode != 0:
                # 프로세스가 종료됨 - 에러 로그 확인
                with open(redis_err, 'r') as f:
                    error_output = f.read()
                with open(redis_log, 'r') as f:
                    log_output = f.read()
                print(f"❌ Redis 프로세스가 즉시 종료됨 (returncode: {_redis_process.returncode})")
                print(f"   stderr: {error_output[:500] if error_output else 'None'}")
                print(f"   stdout: {log_output[:500] if log_output else 'None'}")
                return
            
            # Redis 시작 대기 (최대 10초)
            for i in range(20):
                time.sleep(0.5)
                try:
                    r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=1)
                    r.ping()
                    print(f"✅ Redis 서버 시작 완료 (시도 {i+1}/20)")
                    _redis_started = True
                    return
                except Exception as e:
                    if i == 0:
                        print(f"⏳ Redis 시작 대기 중... ({e})")
                    continue
            
            # 프로세스가 종료되었는지 확인
            if _redis_process.poll() is not None:
                # 에러 로그 파일 읽기
                redis_err = os.path.join(redis_dir, "redis.err")
                redis_log = os.path.join(redis_dir, "redis.log")
                try:
                    with open(redis_err, 'r') as f:
                        error_output = f.read()
                    with open(redis_log, 'r') as f:
                        log_output = f.read()
                    print(f"❌ Redis 프로세스 종료됨 (returncode: {_redis_process.returncode})")
                    print(f"   stderr: {error_output[:1000] if error_output else 'None'}")
                    print(f"   stdout: {log_output[:1000] if log_output else 'None'}")
                except Exception as e:
                    print(f"❌ Redis 프로세스 종료됨 (로그 읽기 실패: {e})")
            else:
                print("⚠️  Redis 시작 시간 초과, Redis 없이 계속 진행합니다.")
                print(f"   Redis 프로세스는 여전히 실행 중입니다 (PID: {_redis_process.pid})")
                
        except Exception as e:
            print(f"❌ Redis 시작 실패: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")

# Lambda 핸들러 초기화 시 Redis 시작
# Redis가 완전히 준비될 때까지 기다린 후 app.main을 import
start_redis_if_needed()

# Redis가 시작되었는지 확인하고, 시작되지 않았어도 계속 진행
# (서비스들이 Redis 연결 실패 시 메모리 캐시로 폴백함)
if not _redis_started:
    # Redis 시작을 기다림 (최대 5초)
    print("⏳ Redis 시작 대기 중...")
    for i in range(10):
        time.sleep(0.5)
        try:
            r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=1)
            r.ping()
            print("✅ Redis가 준비되었습니다.")
            _redis_started = True
            break
        except Exception as e:
            if i == 9:  # 마지막 시도
                print(f"⚠️  Redis가 아직 준비되지 않았습니다 (최종 시도 실패: {e})")
                print("   app.main을 로드합니다. 서비스들이 Redis 연결 실패 시 메모리 캐시로 폴백합니다.")
            continue

# app.main을 import (이 시점에 서비스들이 초기화되며 Redis 연결 시도)
from mangum import Mangum  # type: ignore
from app.main import app

# Mangum을 사용하여 FastAPI 앱을 Lambda 핸들러로 변환
handler = Mangum(app, lifespan="off")

