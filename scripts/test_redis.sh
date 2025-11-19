#!/bin/bash
# Redis 테스트 스크립트 (로컬에서 Docker 이미지 테스트용)

echo "🔍 Redis 바이너리 확인 중..."

# Redis 서버 경로 확인
REDIS_PATHS=(
    "/usr/local/bin/redis-server"
    "/usr/bin/redis-server"
    "/bin/redis-server"
)

FOUND=false
for path in "${REDIS_PATHS[@]}"; do
    if [ -f "$path" ] && [ -x "$path" ]; then
        echo "✅ Redis 서버 발견: $path"
        $path --version
        FOUND=true
        break
    fi
done

if [ "$FOUND" = false ]; then
    echo "❌ Redis 서버를 찾을 수 없습니다."
    exit 1
fi

# Redis 시작 테스트
echo ""
echo "🚀 Redis 시작 테스트..."

REDIS_DIR=/tmp/redis-test
mkdir -p $REDIS_DIR

cat > $REDIS_DIR/redis.conf << EOF
port 6379
bind 127.0.0.1
dir $REDIS_DIR
daemonize no
save ""
appendonly no
maxmemory 256mb
maxmemory-policy allkeys-lru
EOF

$path $REDIS_DIR/redis.conf &
REDIS_PID=$!

sleep 2

# Redis 연결 테스트
if redis-cli -p 6379 ping 2>/dev/null | grep -q PONG; then
    echo "✅ Redis 시작 성공!"
    redis-cli -p 6379 set test "hello"
    redis-cli -p 6379 get test
    kill $REDIS_PID
    rm -rf $REDIS_DIR
    exit 0
else
    echo "❌ Redis 시작 실패"
    kill $REDIS_PID 2>/dev/null
    rm -rf $REDIS_DIR
    exit 1
fi

