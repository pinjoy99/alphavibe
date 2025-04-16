import importlib
import inspect
import os
import sys
from typing import Dict, List, Type, Any, Optional
from backtesting import Strategy

class StrategyRegistry:
    """전략 레지스트리: 모든 전략을 자동으로 등록하고 관리합니다."""
    
    _strategies: Dict[str, Type[Strategy]] = {}
    
    @classmethod
    def register(cls, strategy_class: Type[Strategy]) -> None:
        """전략 클래스 등록"""
        if hasattr(strategy_class, 'CODE') and strategy_class.CODE:
            code = strategy_class.CODE
            cls._strategies[code] = strategy_class
    
    @classmethod
    def discover_strategies(cls) -> None:
        """strategies 디렉토리에서 모든 Backtesting.py 기반 전략 발견 및 등록"""
        cls._strategies = {}  # 기존 전략 목록 초기화
        strategies_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 디렉토리 내 모든 .py 파일 탐색
        for filename in os.listdir(strategies_dir):
            if filename.endswith('_bt.py') and filename != 'strategy_registry.py':
                module_name = os.path.splitext(filename)[0]
                
                try:
                    # 상대 경로로 모듈 로드
                    module = importlib.import_module(f".{module_name}", package="src.strategies")
                    
                    # 모듈 내 모든 클래스 검사
                    for _, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, Strategy) and obj != Strategy:
                            # 필수 속성 확인 (CODE, NAME, DESCRIPTION)
                            if all(hasattr(obj, attr) for attr in ['CODE', 'NAME', 'DESCRIPTION']):
                                print(f"등록: {obj.__name__}, {obj.__module__}, CODE={getattr(obj, 'CODE', None)}")
                                cls.register(obj)
                            else:
                                print(f"Warning: 전략 클래스 '{obj.__name__}'에 필수 속성이 누락되었습니다.")
                except (ImportError, AttributeError) as e:
                    print(f"Warning: 전략 모듈 '{module_name}' 로드 중 오류 발생: {e}")
    
    @classmethod
    def get_strategy_class(cls, strategy_code: str) -> Optional[Type[Strategy]]:
        """전략 코드로 전략 클래스 가져오기"""
        if not cls._strategies:
            cls.discover_strategies()
        return cls._strategies.get(strategy_code)
    
    @classmethod
    def get_available_strategies(cls) -> List[Dict[str, Any]]:
        """사용 가능한 모든 전략 정보 반환"""
        if not cls._strategies:
            cls.discover_strategies()
        
        strategies_info = []
        for code, strategy_class in cls._strategies.items():
            # get_parameters 메서드가 있는지 확인
            params = []
            if hasattr(strategy_class, 'get_parameters') and callable(getattr(strategy_class, 'get_parameters')):
                param_dict = strategy_class.get_parameters()
                for name, details in param_dict.items():
                    param_info = {
                        'name': name,
                        'type': details.get('type', 'any'),
                        'default': details.get('default', None),
                        'description': details.get('description', ''),
                        'min': details.get('min', None),
                        'max': details.get('max', None)
                    }
                    params.append(param_info)
            
            info = {
                'code': code,
                'name': getattr(strategy_class, 'NAME', code),
                'description': getattr(strategy_class, 'DESCRIPTION', ''),
                'params': params
            }
            strategies_info.append(info)
        
        return strategies_info
