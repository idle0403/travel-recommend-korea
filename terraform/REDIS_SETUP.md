# 🔴 Lambda 내부 Redis 설정

이 프로젝트는 Lambda 함수 내에서 Redis 서버를 자동으로 시작하도록 구성되어 있습니다.

## 📋 작동 방식

1. **Dockerfile.lambda**: Redis 서버를 소스에서 빌드하여 이미지에 포함
2. **lambda_handler.py**: Lambda 핸들러 초기화 시 Redis 서버를 백그라운드로 시작
3. **start_redis.sh**: Redis 서버 시작 스크립트

## ⚠️ 제한사항

### Lambda 내부 Redis의 한계:

1. **상태 공유 불가**: 각 Lambda 인보케이션은 독립적인 Redis 인스턴스를 가집니다
   - 인보케이션 간 캐시 공유 불가
   - 콜드 스타트마다 새로운 Redis 인스턴스 시작

2. **콜드 스타트 시간 증가**: Redis 시작에 약 1-3초 추가
   - 첫 요청 시 Redis 빌드/시작 시간 필요

3. **메모리 제한**: Lambda 메모리 제한 내에서 Redis도 실행
   - Redis 메모리 사용량이 Lambda 메모리에 포함됨

4. **데이터 지속성 없음**: Lambda 인보케이션이 종료되면 Redis 데이터도 사라짐
   - `/tmp` 디렉토리는 인보케이션 간 유지되지 않음

## ✅ 권장 사용 사례

Lambda 내부 Redis는 다음 경우에 적합합니다:

- ✅ 단일 요청 내에서만 캐시가 필요한 경우
- ✅ 빠른 프로토타이핑
- ✅ 개발/테스트 환경
- ✅ 트래픽이 적고 콜드 스타트가 자주 발생하지 않는 경우

## 🔄 대안: 외부 Redis 사용

프로덕션 환경에서는 다음 옵션을 고려하세요:

### 옵션 1: AWS ElastiCache (권장)
```hcl
# terraform.tfvars
REDIS_URL = "redis://your-elasticache-endpoint:6379/0"
```

**장점:**
- 인보케이션 간 상태 공유
- 높은 가용성 및 확장성
- 데이터 지속성

**단점:**
- VPC 설정 필요
- 추가 비용 발생

### 옵션 2: Upstash Redis (서버리스)
```hcl
# terraform.tfvars
REDIS_URL = "redis://your-upstash-endpoint:6379/0"
```

**장점:**
- VPC 불필요
- 서버리스 (사용한 만큼만 비용)
- Lambda와 잘 통합됨

### 옵션 3: Redis Cloud
```hcl
# terraform.tfvars
REDIS_URL = "redis://your-redis-cloud-endpoint:6379/0"
```

## 🔧 설정 변경

Lambda 내부 Redis를 비활성화하고 외부 Redis를 사용하려면:

1. `terraform.tfvars`에서 `REDIS_URL` 수정
2. Dockerfile.lambda에서 Redis 설치 부분 제거 (선택사항)
3. `lambda_handler.py`에서 Redis 시작 코드 제거 (선택사항)

## 📊 성능 비교

| 방식 | 콜드 스타트 | 상태 공유 | 데이터 지속성 | 비용 |
|------|------------|----------|--------------|------|
| Lambda 내부 Redis | 느림 (+1-3초) | ❌ | ❌ | 무료 |
| ElastiCache | 빠름 | ✅ | ✅ | $$ |
| Upstash | 빠름 | ✅ | ✅ | $ |

## 🐛 문제 해결

### Redis가 시작되지 않는 경우

1. CloudWatch Logs 확인:
   ```bash
   aws logs tail /aws/lambda/travel-recommend-korea-dev --follow
   ```

2. Redis 시작 스크립트 확인:
   - `/usr/local/bin/start_redis.sh` 파일 존재 확인
   - 실행 권한 확인

3. Redis 바이너리 확인:
   ```bash
   # Lambda 함수 내에서 확인
   which redis-server
   redis-server --version
   ```

### 메모리 부족 에러

Lambda 메모리를 증가시키세요:
```hcl
# terraform.tfvars
lambda_memory_size = 2048  # 1024에서 증가
```

## 📚 참고 자료

- [AWS Lambda 환경 변수](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)
- [AWS ElastiCache](https://docs.aws.amazon.com/elasticache/)
- [Upstash Redis](https://docs.upstash.com/redis)

