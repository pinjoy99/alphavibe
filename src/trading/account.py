import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import os
import time

from src.api.upbit_api import get_account_info, get_order_history, get_current_price, get_ticker_list
from src.utils import format_timestamp, ensure_directory

class AccountManager:
    """계좌 정보 관리 및 분석 클래스"""
    
    def __init__(self):
        """초기화"""
        self.balances = None
        self.orders = None
        self.last_update = None
        self.total_asset_value = 0
        self.total_profit_loss = 0
        self._current_prices = {}  # 현재가 캐시
        
    def refresh(self) -> bool:
        """
        계좌 정보 새로고침
        
        Returns:
            bool: 성공 여부
        """
        self.balances = get_account_info()
        if self.balances:
            self.last_update = datetime.now()
            # 캐시 초기화
            self._current_prices = {}
            return True
        return False
    
    def _get_cached_current_price(self, tickers: List[str]) -> Dict[str, float]:
        """
        현재가 조회 (캐싱 적용)
        
        Parameters:
            tickers (List[str]): 티커 리스트
            
        Returns:
            Dict[str, float]: 티커별 현재가
        """
        # 조회할 티커 필터링 (캐시에 없는 것만)
        uncached_tickers = [t for t in tickers if t not in self._current_prices]
        
        # 티커가 없으면 빈 딕셔너리 반환
        if not uncached_tickers:
            return {t: self._current_prices.get(t, 0) for t in tickers}
            
        # 여러 티커 한 번에 조회
        if len(uncached_tickers) > 1:
            prices = get_current_price(uncached_tickers)
            if prices and isinstance(prices, dict):
                # 캐시에 저장
                for ticker, price in prices.items():
                    self._current_prices[ticker] = price
        # 단일 티커 조회
        elif len(uncached_tickers) == 1:
            price = get_current_price(uncached_tickers[0])
            if price and isinstance(price, (int, float)):
                self._current_prices[uncached_tickers[0]] = price
        
        # 결과 반환 (요청된 티커만)
        result = {}
        for ticker in tickers:
            if ticker in self._current_prices:
                result[ticker] = self._current_prices[ticker]
            else:
                result[ticker] = 0  # 티커가 없는 경우 0으로 설정
        
        return result
        
    def get_summary(self, min_value: float = 500.0, sort_by: str = 'value') -> Dict[str, Any]:
        """
        계좌 요약 정보
        
        Parameters:
            min_value (float): 표시할 최소 코인 가치 (KRW)
            sort_by (str): 정렬 기준 ('value', 'profit', 'profit_pct')
            
        Returns:
            Dict[str, Any]: 계좌 요약 정보 딕셔너리
        """
        if not self.balances:
            return {}
            
        # 요약 정보 초기화
        summary = {
            'total_krw': 0,
            'total_asset_value': 0,
            'coins': [],
            'others': {  # 소액 코인 통합 정보
                'count': 0,
                'total_value': 0,
                'total_profit_loss': 0,
            }
        }
        
        # KRW 잔고 확인
        for balance in self.balances:
            if balance['currency'] == 'KRW':
                summary['total_krw'] = float(balance['balance'])
                break
        
        # 코인 티커 목록 생성
        coin_tickers = []
        for balance in self.balances:
            if balance['currency'] == 'KRW':
                continue
            coin_tickers.append(f"KRW-{balance['currency']}")
        
        # 전체 현재가를 한 번에 조회
        current_prices = self._get_cached_current_price(coin_tickers)
        
        # 코인별 정보 계산
        for balance in self.balances:
            if balance['currency'] == 'KRW':
                continue
                
            coin_ticker = f"KRW-{balance['currency']}"
            balance_float = float(balance['balance'])
            avg_buy_price = float(balance['avg_buy_price'])
            
            # 현재가 획득
            current_price = current_prices.get(coin_ticker, avg_buy_price)
            
            # 코인별 가치 계산
            current_value = balance_float * current_price
            invested_value = balance_float * avg_buy_price
            profit_loss = current_value - invested_value
            profit_loss_pct = (profit_loss / invested_value * 100) if invested_value > 0 else 0
            
            # 코인 정보 생성
            coin_info = {
                'ticker': coin_ticker,
                'currency': balance['currency'],
                'balance': balance_float,
                'avg_buy_price': avg_buy_price,
                'current_price': current_price,
                'current_value': current_value,
                'invested_value': invested_value,
                'profit_loss': profit_loss,
                'profit_loss_pct': profit_loss_pct
            }
            
            # 최소 가치 이상인 코인만 개별 표시
            if current_value >= min_value and balance_float > 0:
                summary['coins'].append(coin_info)
            else:
                # 소액 코인은 'others'에 합산
                summary['others']['count'] += 1
                summary['others']['total_value'] += current_value
                summary['others']['total_profit_loss'] += profit_loss
            
            # 총 자산 가치에는 모든 코인 포함
            summary['total_asset_value'] += current_value
        
        # 코인 정렬
        if sort_by == 'value':
            summary['coins'].sort(key=lambda x: x['current_value'], reverse=True)
        elif sort_by == 'profit':
            summary['coins'].sort(key=lambda x: x['profit_loss'], reverse=True)
        elif sort_by == 'profit_pct':
            summary['coins'].sort(key=lambda x: x['profit_loss_pct'], reverse=True)
        
        # 총 자산 가치 = 현금 + 코인 가치
        summary['total_asset_value'] += summary['total_krw']
        self.total_asset_value = summary['total_asset_value']
        
        # 전체 손익 계산
        total_invested = sum(coin['invested_value'] for coin in summary['coins'])
        total_current = sum(coin['current_value'] for coin in summary['coins'])
        
        # 소액 코인의 손익도 포함
        total_invested += (summary['others']['total_value'] - summary['others']['total_profit_loss'])
        total_current += summary['others']['total_value']
        
        self.total_profit_loss = total_current - total_invested
        summary['total_profit_loss'] = self.total_profit_loss
        summary['total_profit_loss_pct'] = (self.total_profit_loss / total_invested * 100) if total_invested > 0 else 0
        
        # 업데이트 시간 추가
        summary['last_update'] = self.last_update.strftime('%Y-%m-%d %H:%M:%S') if self.last_update else None
        
        return summary
        
    def get_recent_orders(self, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        최근 주문 내역 조회 및 가공
        
        Parameters:
            limit (int): 최대 조회 건수
            
        Returns:
            Optional[List[Dict[str, Any]]]: 가공된 주문 내역 또는 실패 시 None
        """
        # 주문 내역 조회
        orders = get_order_history(limit=limit)
        if not orders:
            return []
            
        # 주문 내역 가공
        processed_orders = []
        for order in orders:
            try:
                # 필수 필드 검증
                market = order.get('market', '')
                side = order.get('side', '')
                created_at_str = order.get('created_at', '')
                
                if not (market and side and created_at_str):
                    continue
                
                # 금액 관련 데이터 변환
                try:
                    executed_volume = float(order.get('executed_volume', 0))
                    price = float(order.get('price', 0))
                except (ValueError, TypeError):
                    executed_volume = 0
                    price = 0
                
                # 거래량이 없으면 건너뛰기
                if executed_volume <= 0:
                    continue
                
                # 날짜 포맷 변환 (안전하게 처리)
                formatted_date = format_timestamp(created_at_str)
                
                processed_order = {
                    'uuid': order.get('uuid', ''),
                    'ticker': market,
                    'side': '매수' if side == 'bid' else '매도',
                    'price': price,
                    'volume': float(order.get('volume', 0) or 0),
                    'executed_volume': executed_volume,
                    'state': order.get('state', ''),
                    'created_at': formatted_date,
                    'amount': price * executed_volume,
                }
                
                processed_orders.append(processed_order)
            except Exception as e:
                # 개별 주문 처리 실패 시 오류 출력 후 계속 진행
                print(f"주문 처리 오류: {e}, 해당 주문은 건너뜁니다.")
                continue
            
        return processed_orders
    
    def save_account_history(self, history_dir: str = 'results/account_history') -> str:
        """
        계좌 정보 히스토리 저장
        
        Parameters:
            history_dir (str): 저장 디렉토리
            
        Returns:
            str: 저장된 파일 경로
        """
        # 디렉토리 생성
        ensure_directory(history_dir)
        
        # 현재 시간
        now = datetime.now()
        
        # 파일 이름 생성
        filename = f"account_history_{now.strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(history_dir, filename)
        
        # 계좌 정보가 없으면 새로고침
        if not self.balances:
            self.refresh()
            
        if not self.balances:
            return ""
            
        # 계좌 정보를 DataFrame으로 변환
        summary = self.get_summary(min_value=0)  # 모든 코인 포함
        
        # 코인만 추출
        df = pd.DataFrame(summary['coins'])
        
        # 현재 시간 정보 추가
        df['timestamp'] = now
        df['total_krw'] = summary['total_krw']
        df['total_asset_value'] = summary['total_asset_value']
        
        # 파일 저장
        df.to_csv(filepath, index=False)
        
        return filepath 