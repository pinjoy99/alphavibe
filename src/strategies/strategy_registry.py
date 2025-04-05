import importlib
import inspect
import os
import sys
from typing import Dict, List, Type, Any, Optional
from .base_strategy import BaseStrategy

class StrategyRegistry:
    """전략 레지스트리: 모든 전략을 자동으로 등록하고 관리합니다."""
    
    _strategies: Dict[str, Type[BaseStrategy]] = {}
    
    @classmethod
    def register(cls, strategy_class: Type[BaseStrategy]) -> None:
        """전략 클래스 등록"""
        if hasattr(strategy_class, 'STRATEGY_CODE') and strategy_class.STRATEGY_CODE:
            code = strategy_class.STRATEGY_CODE
            cls._strategies[code] = strategy_class
    
    @classmethod
    def discover_strategies(cls) -> None:
        """strategies 디렉토리에서 모든 전략 발견 및 등록"""
        strategies_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 디렉토리 내 모든 .py 파일 탐색
        for filename in os.listdir(strategies_dir):
            if filename.endswith('_strategy.py') and filename != 'base_strategy.py' and filename != 'template_strategy.py' and filename != 'strategy_registry.py':
                module_name = os.path.splitext(filename)[0]
                
                try:
                    # 상대 경로로 모듈 로드
                    module = importlib.import_module(f".{module_name}", package="src.strategies")
                    
                    # 모듈 내 모든 클래스 검사
                    for _, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, BaseStrategy) and obj != BaseStrategy:
                            cls.register(obj)
                except (ImportError, AttributeError) as e:
                    print(f"Warning: 전략 모듈 '{module_name}' 로드 중 오류 발생: {e}")
    
    @classmethod
    def get_strategy_class(cls, strategy_code: str) -> Optional[Type[BaseStrategy]]:
        """전략 코드로 전략 클래스 가져오기"""
        if not cls._strategies:
            cls.discover_strategies()
        return cls._strategies.get(strategy_code)
    
    @classmethod
    def create_strategy(cls, strategy_code: str, **params) -> Optional[BaseStrategy]:
        """전략 코드와 파라미터로 전략 인스턴스 생성"""
        strategy_class = cls.get_strategy_class(strategy_code)
        if not strategy_class:
            return None
        
        # 전략 클래스에 필요한 파라미터만 필터링
        valid_params = {}
        if hasattr(strategy_class, 'register_strategy_params'):
            registered_params = strategy_class.register_strategy_params()
            param_names = [p['name'] for p in registered_params]
            valid_params = {k: v for k, v in params.items() if k in param_names}
        
        return strategy_class(**valid_params)
    
    @classmethod
    def get_available_strategies(cls) -> List[Dict[str, Any]]:
        """사용 가능한 모든 전략 정보 반환"""
        if not cls._strategies:
            cls.discover_strategies()
        
        strategies_info = []
        for code, strategy_class in cls._strategies.items():
            info = {
                'code': code,
                'name': getattr(strategy_class, 'STRATEGY_NAME', code),
                'description': getattr(strategy_class, 'STRATEGY_DESCRIPTION', ''),
                'params': strategy_class.register_strategy_params() if hasattr(strategy_class, 'register_strategy_params') else []
            }
            strategies_info.append(info)
        
        return strategies_info 