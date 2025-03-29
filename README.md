# 암호화폐 가격 분석 POC

이 프로젝트는 Upbit API를 사용하여 암호화폐의 과거 가격 정보를 수집하고 분석하는 예제 코드입니다.

## 기능

- 지정된 암호화폐의 과거 가격 데이터 수집
- 기본 통계 정보 계산 (최고가, 최저가, 거래량 등)
- 가격 차트 생성 (종가 및 20일 이동평균선)
- 차트 이미지 저장

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 환경 변수 설정:
   - `.env.example` 파일을 `.env`로 복사
   ```bash
   cp .env.example .env
   ```
   - `.env` 파일을 열어 필요한 설정 값 입력
   ```
   UPBIT_ACCESS_KEY="your-access-key-here"  # Upbit API 액세스 키
   UPBIT_SECRET_KEY="your-secret-key-here"  # Upbit API 시크릿 키
   ```

## 환경 변수 설정

| 변수명 | 설명 | 기본값 |
|--------|------|---------|
| UPBIT_ACCESS_KEY | Upbit API 액세스 키 | - |
| UPBIT_SECRET_KEY | Upbit API 시크릿 키 | - |
| CHART_SAVE_PATH | 차트 이미지 저장 경로 | charts |
| DEFAULT_INTERVAL | 기본 데이터 조회 간격 | day |
| DEFAULT_COUNT | 기본 데이터 조회 개수 | 100 |
| LOG_LEVEL | 로깅 레벨 | INFO |

## 사용 방법

1. 스크립트 실행:
```bash
python historical_price.py
```

2. 결과 확인:
- 콘솔에 각 종목의 기본 통계 정보가 출력됩니다.
- `poc/charts` 폴더에 각 종목의 차트 이미지가 저장됩니다.

## 참고사항

- 기본적으로 BTC(비트코인), ETH(이더리움), XRP(리플)의 데이터를 분석합니다.
- 다른 종목을 분석하려면 `historical_price.py` 파일의 `tickers` 리스트를 수정하세요.
- 업비트에서 제공하는 모든 암호화폐 종목에 대해 분석이 가능합니다.
- API 키는 선택사항이며, 설정하지 않아도 기본적인 시세 조회는 가능합니다.