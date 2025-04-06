"""
시각화 모듈

차트 생성 및 시각화 기능을 제공하는 모듈입니다.
"""

# 스타일 관련 함수
from src.visualization.styles import (
    apply_style, 
    create_custom_style, 
    register_mplfinance_style, 
    get_available_styles
)

# 기본 차트 함수
from src.visualization.base_charts import (
    create_base_chart,
    plot_candlestick,
    plot_ohlc,
    plot_line,
    plot_volume,
    add_moving_averages,
    add_bollinger_bands,
    add_support_resistance,
    add_markers,
    add_annotations,
    plot_price_with_indicators
)

# 분석 차트 함수
from src.visualization.analysis_charts import (
    plot_market_analysis,
    plot_technical_indicators,
    plot_support_resistance
)

# 지표 차트 함수
from src.visualization.indicator_charts import (
    plot_macd,
    plot_rsi,
    plot_stochastic,
    plot_atr,
    plot_cci,
    plot_indicator_chart
)

# 백테스트 차트 함수
from src.visualization.backtest_charts import (
    plot_backtest_results,
    plot_strategy_performance,
    plot_strategy_comparison
)

# 트레이딩 차트 함수
from src.visualization.trading_charts import (
    plot_asset_distribution,
    plot_profit_loss,
    plot_trade_history,
    plot_portfolio_history
)

# 헬퍼 함수
from src.visualization.viz_helpers import (
    prepare_ohlcv_dataframe,
    add_colormap_to_values,
    create_chart_title,
    calculate_chart_grid_size,
    adjust_figure_size
)

# 유틸리티 함수 - src/utils/chart_utils.py 에서 가져옴
from src.utils.chart_utils import (
    setup_chart_dir,
    format_date_axis,
    format_price_axis,
    save_chart,
    generate_filename,
    detect_chart_type
)

__all__ = [
    # 스타일 관련 함수
    'apply_style',
    'create_custom_style',
    'register_mplfinance_style',
    'get_available_styles',
    
    # 유틸리티 함수
    'setup_chart_dir',
    'format_date_axis',
    'format_price_axis',
    'save_chart',
    'generate_filename',
    'detect_chart_type',
    
    # 기본 차트 함수
    'create_base_chart',
    'plot_candlestick',
    'plot_ohlc',
    'plot_line',
    'plot_volume',
    'add_moving_averages',
    'add_bollinger_bands',
    'add_support_resistance',
    'add_markers',
    'add_annotations',
    'plot_price_with_indicators',
    
    # 분석 차트 함수
    'plot_market_analysis',
    'plot_technical_indicators',
    'plot_support_resistance',
    
    # 지표 차트 함수
    'plot_macd',
    'plot_rsi',
    'plot_stochastic',
    'plot_atr',
    'plot_cci',
    'plot_indicator_chart',
    
    # 백테스트 차트 함수
    'plot_backtest_results',
    'plot_strategy_performance',
    'plot_strategy_comparison',
    
    # 트레이딩 차트 함수
    'plot_asset_distribution',
    'plot_profit_loss',
    'plot_trade_history',
    'plot_portfolio_history',
    
    # 헬퍼 함수
    'prepare_ohlcv_dataframe',
    'add_colormap_to_values',
    'create_chart_title',
    'calculate_chart_grid_size',
    'adjust_figure_size'
]
