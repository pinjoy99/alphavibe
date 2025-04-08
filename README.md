# AlphaVibe

암호화폐 거래 전략 백테스팅 및 분석을 위한 강력한 도구

## 소개

AlphaVibe는 암호화폐 시장에서 거래 전략을 개발하고 평가하기 위한 종합적인 프레임워크입니다. 이 도구는 다양한
기술적 지표를 활용한 전략 백테스팅, 시장 분석, 결과 시각화를 제공합니다.

### 주요 기능

- 다양한 기술적 지표 기반 거래 전략 구현 및 백테스팅
- 실시간 시장 데이터 분석
- 자세한 성능 메트릭 및 결과 시각화
- 사용자 정의 전략 개발 용이성

## 새로운 기능: Backtesting.py 라이브러리 통합

이제 AlphaVibe는 강력한 백테스팅 라이브러리인 Backtesting.py를 통합하여 더욱 향상된 백테스팅 경험을 제공합니다:

- **더 빠른 백테스팅 속도**: 벡터화된 연산으로 백테스팅 속도 향상
- **향상된 성능 지표**: 다양한 내장 성능 지표 제공
- **고급 시각화**: 거래 내역, 수익 곡선 등을 포함한 상세한 차트
- **간소화된 전략 개발**: 직관적인 API로 전략 개발 간소화

기존 백테스팅 엔진과 함께 사용 가능하며, 보다 상세한 내용은 [USAGE_GUIDE.md](./docs/USAGE_GUIDE.md)와 [ADDING_STRATEGIES.md](./docs/ADDING_STRATEGIES.md)를 참조하세요.

## 설치 및 요구사항

### 요구사항

- Python 3.8 이상
- pip (Python 패키지 관리자)

### 설치 방법

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

3. 필요 패키지 설치:
   ```bash
   pip install -r requirements.txt
   ```

## 사용 방법

기본 사용법:

```bash
./run.sh --help  # 사용 가능한 모든 옵션 표시
```

백테스팅 실행:

```bash
# 기본 백테스팅 엔진 사용
./run.sh -b -s sma -p 3m -c BTC -i 10000000

# Backtesting.py 엔진 사용 (SMA 전략)
./run.sh -b -s sma_bt -p 3m -c BTC -i 10000000
```

자세한 사용법은 [USAGE_GUIDE.md](./docs/USAGE_GUIDE.md)를 참조하세요.

## 전략 개발

새로운 전략 개발 방법에 대한 자세한 내용은 [ADDING_STRATEGIES.md](./docs/ADDING_STRATEGIES.md)를 참조하세요.

## 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE)에 따라 라이선스가 부여됩니다.