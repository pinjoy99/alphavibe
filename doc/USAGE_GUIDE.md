# 사용 방법

## 기본 사용법

1. 환경 설정:
```
./setup.sh
```

2. 기본 실행:
```
./run.sh  # 기본 실행 (가격 분석)
./run.sh --telegram  # 텔레그램 알림 활성화
./run.sh -t  # 텔레그램 알림 활성화 (단축 옵션)
```

3. 코인 선택 및 데이터 간격 옵션:
```
./run.sh --coins BTC,SOL  # BTC와 SOL만 분석
./run.sh -c BTC,ETH,DOGE  # 여러 코인 지정 (단축 옵션)
./run.sh --interval minute15  # 15분봉 데이터로 분석 (차트 및 데이터)
./run.sh -v minute60  # 1시간봉 데이터로 분석 (단축 옵션)
./run.sh -c BTC -v minute15 -p 1m  # BTC를 15분봉으로 1개월 데이터 분석
```

데이터 간격 옵션(-v 또는 --interval)을 사용하면 해당 간격으로 데이터를 조회하고 차트를 생성합니다. 지원되는 간격은 다음과 같습니다:
- day: 일봉 데이터
- minute1, minute3, minute5: 1분, 3분, 5분봉
- minute15, minute30: 15분, 30분봉
- minute60, minute240: 1시간, 4시간봉

## 백테스팅 활용

1. 사용 가능한 전략 확인:
```
./run.sh --help
```
이 명령을 실행하면 현재 시스템에서 사용 가능한 모든 전략이 자동으로 표시됩니다. 새로운 전략을 추가하면 별도의 설정 없이 이 목록에 자동으로 표시됩니다.

2. 백테스팅 실행:
```
./run.sh --backtest --strategy sma  # SMA 전략 백테스팅
./run.sh -b -s bb  # 볼린저 밴드 전략 백테스팅 (단축 옵션)
./run.sh -b -s macd -p 6m -i 5000000  # MACD 전략, 6개월, 5백만원 초기 자본
./run.sh -b -c SOL -s rsi  # SOL 코인에 대해 RSI 전략으로 백테스팅
./run.sh -b -c BTC,ETH -v minute240  # BTC, ETH에 대해 4시간봉 데이터로 백테스팅
```

## 계좌 정보 조회

```
./run.sh --account  # 계좌 정보 조회
./run.sh -a  # 계좌 정보 조회 (단축 옵션)
./run.sh -a -t  # 계좌 정보 조회 및 텔레그램 알림 활성화
```

계좌 정보 조회 기능은 다음 정보를 제공합니다:
- 보유 현금
- 총 자산 가치
- 코인별 보유 현황 (가치 기준 정렬)
- 코인별 손익 정보 (금액 및 백분율)
- 소액 코인 통합 요약
- 최근 주문 내역
- 자산 분포 및 손익 시각화 차트

## 결과 확인

- 콘솔에 각 종목의 기본 통계 정보가 출력됩니다.
- `results/analysis` 폴더에 분석 차트 이미지가 저장됩니다.
- `results/strategy_results` 폴더에 백테스트 결과 차트 이미지가 저장됩니다.
- `results/account` 폴더에 계좌 정보 차트 이미지가 저장됩니다.
- `results/account_history` 폴더에 계좌 정보 히스토리가 CSV 파일로 저장됩니다.
- 텔레그램 알림을 활성화한 경우, 봇을 통해 알림과 차트가 전송됩니다. 