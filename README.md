# 암호화폐 가격 분석 POC

이 프로젝트는 Upbit API를 사용하여 암호화폐의 과거 가격 정보를 수집하고 분석하는 예제 코드입니다.

## 기능

- 지정된 암호화폐의 과거 가격 데이터 수집
- 기본 통계 정보 계산 (최고가, 최저가, 거래량 등)
- 가격 차트 생성 (종가 및 20일 이동평균선)
- 차트 이미지 저장

## 환경 설정 및 실행 방법

### 환경 설정

환경 설정 스크립트 실행:
```
chmod +x setup.sh
./setup.sh
```

이 스크립트는 다음 작업을 수행합니다:
- 가상환경(venv) 생성
- 필요한 패키지 설치

또는 수동으로 환경 설정:
```
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
deactivate
```

### 프로그램 실행

실행 스크립트 사용:
```
chmod +x run.sh
./run.sh
```

이 스크립트는 다음 작업을 수행합니다:
- 가상환경이 없는 경우 자동으로 setup.sh 실행
- 가상환경 활성화
- main.py 실행
- 실행 완료 후 가상환경 비활성화

또는 수동 실행:
```
source venv/bin/activate  # Windows: venv\Scripts\activate
python main.py
deactivate
```

## 환경 변수 설정

프로그램 실행에 필요한 환경 변수는 `.env` 파일에 설정합니다.

### 환경 변수 파일 설정 방법

1. `.env.example` 파일을 `.env`로 복사합니다:
   ```
   cp .env.example .env
   ```

2. `.env` 파일을 열어 필요한 설정 값을 입력합니다:
   ```
   # Upbit API 키 설정 (필수)
   UPBIT_ACCESS_KEY=your_access_key_here
   UPBIT_SECRET_KEY=your_secret_key_here

   # 텔레그램 설정 (선택사항)
   ENABLE_TELEGRAM=false  # 텔레그램 알림을 사용하려면 true로 변경
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   TELEGRAM_CHAT_ID=your_telegram_chat_id_here
   ```

3. 환경 변수 설명:

   | 환경 변수 | 설명 | 기본값 |
   |-----------|------|--------|
   | CHART_SAVE_PATH | 차트 이미지 저장 경로 | charts |
   | DEFAULT_INTERVAL | 기본 시간 간격 (day, minute1, minute3, minute5 등) | day |
   | DEFAULT_COUNT | 조회할 데이터 개수 | 100 |
   | LOG_LEVEL | 로그 레벨 (INFO, DEBUG, WARNING, ERROR) | INFO |
   | UPBIT_ACCESS_KEY | Upbit API 액세스 키 | - |
   | UPBIT_SECRET_KEY | Upbit API 시크릿 키 | - |
   | ENABLE_TELEGRAM | 텔레그램 알림 활성화 여부 (true/false) | false |
   | TELEGRAM_BOT_TOKEN | 텔레그램 봇 토큰 | - |
   | TELEGRAM_CHAT_ID | 텔레그램 채팅 ID | - |

**참고**: `setup.sh` 스크립트 실행 시 `.env` 파일이 없는 경우 자동으로 `.env.example` 파일을 복사하여 `.env` 파일을 생성합니다.

## 사용 방법

1. 환경 설정:
```
./setup.sh
```

2. 실행:
```
./run.sh  # 기본 실행 (텔레그램 알림 비활성화)
./run.sh --telegram  # 텔레그램 알림 활성화
./run.sh -t  # 텔레그램 알림 활성화 (단축 옵션)
./run.sh --help  # 도움말 표시
```

3. 결과 확인:
   - 콘솔에 각 종목의 기본 통계 정보가 출력됩니다.
   - `charts` 폴더에 각 종목의 차트 이미지가 저장됩니다.
   - 텔레그램 알림을 활성화한 경우, 봇을 통해 알림과 차트가 전송됩니다.

## 프로젝트 구조

```
├── .env                 # 환경 변수 설정 파일
├── .env.example         # 환경 변수 예제 파일
├── .gitignore           # Git 무시 파일 목록
├── main.py              # 메인 프로그램
├── requirements.txt     # 필요 패키지 목록
├── run.sh               # 실행 스크립트
├── setup.sh             # 환경 설정 스크립트
├── charts/              # 차트 이미지 저장 폴더
└── venv/                # 가상환경 (Git에서 무시됨)
```

## 참고사항

- 기본적으로 BTC(비트코인), ETH(이더리움), XRP(리플)의 데이터를 분석합니다.
- 다른 종목을 분석하려면 `main.py` 파일의 `tickers` 리스트를 수정하세요.
- 업비트에서 제공하는 모든 암호화폐 종목에 대해 분석이 가능합니다.
- API 키는 선택사항이며, 설정하지 않아도 기본적인 시세 조회는 가능합니다.
- 가상환경은 `.gitignore`에 포함되어 있어 Git에 커밋되지 않습니다.