# AlphaVibe

암호화폐 거래 전략 백테스팅 및 분석을 위한 강력한 도구

## 소개

AlphaVibe는 암호화폐 시장에서 거래 전략을 개발하고 평가하기 위한 종합적인 프레임워크입니다. 이 도구는 다양한
기술적 지표를 활용한 전략 백테스팅, 시장 분석, 결과 시각화를 제공합니다.

### 주요 기능

- Backtesting.py 기반의 강력한 백테스팅 엔진
- 다양한 기술적 지표 기반 거래 전략 구현
- 실시간 시장 데이터 분석
- 자세한 성능 메트릭 및 결과 시각화
- 사용자 정의 전략 개발 용이성

## Backtesting.py 기반 엔진

AlphaVibe는 이제 강력한 백테스팅 라이브러리인 Backtesting.py를 기본 엔진으로 사용하여 더욱 향상된 백테스팅 경험을 제공합니다:

- **빠른 백테스팅 속도**: 벡터화된 연산으로 백테스팅 속도 향상
- **다양한 성능 지표**: 승률, 손익비, 샤프 비율, 최대 낙폭 등 자세한 성능 지표 제공
- **고급 시각화**: 거래 내역, 수익 곡선 등을 포함한 상세한 차트 제공
- **간소화된 전략 개발**: 직관적인 API로 전략 개발 간소화

자세한 내용은 [USAGE_GUIDE.md](./docs/USAGE_GUIDE.md)와 [ADDING_STRATEGIES.md](./docs/ADDING_STRATEGIES.md)를 참조하세요.

## 설치 및 요구사항

### 시스템 요구사항

- Python 3.8 이상
- Node.js 14 이상
- TA-Lib

### 시스템 라이브러리 설치

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y ta-lib

# macOS
brew install ta-lib
```

### 프로젝트 설치

1. 저장소 복제:
   ```bash
   git clone https://github.com/yourusername/alphavibe.git
   cd alphavibe
   ```

2. 가상 환경 생성 및 활성화:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 또는
   venv\Scripts\activate  # Windows
   ```

3. 백엔드 의존성 설치:
   ```bash
   pip install -r requirements.txt
   ```

4. 프론트엔드 의존성 설치:
   ```bash
   cd src/frontend
   npm install
   ```

## 실행 방법

### 백엔드 서버 실행

```bash
# 프로젝트 루트 디렉토리에서
PYTHONPATH=$PYTHONPATH:. uvicorn src.api.main:app --reload --port 8001
```

### 프론트엔드 개발 서버 실행

```bash
cd src/frontend
npm start
```

### 백테스팅 실행

```bash
# SMA 전략으로 BTC 백테스팅 (3개월, 1억원 초기자본)
./run.sh -b -s sma -p 3m -c BTC -i 100000000

# 파라미터 수정하여 백테스팅
./run.sh -b -s sma -p 6m -c BTC -i 100000000 --params short_window=20,long_window=50

# 여러 코인에 대해 백테스팅
./run.sh -b -s sma -p 3m -c BTC,ETH,SOL -i 100000000
```

## API 문서

FastAPI 서버가 실행되면 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## 프로젝트 구조

프로젝트의 구조와 각 파일에 대한 설명은 [PROJECT_STRUCTURE.md](./docs/PROJECT_STRUCTURE.md)를 참조하세요.

## 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE)에 따라 라이선스가 부여됩니다.