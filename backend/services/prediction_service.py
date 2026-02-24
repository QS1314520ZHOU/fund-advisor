"""
趋势预测服务模块
结合技术指标和新闻情绪进行趋势预测
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import datetime
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """技术指标计算"""
    
    @staticmethod
    def calculate_ma(prices: pd.Series, periods: List[int] = [5, 10, 20, 60]) -> Dict[str, float]:
        """计算移动平均线"""
        result = {}
        for p in periods:
            if len(prices) >= p:
                result[f'ma{p}'] = float(prices.rolling(window=p).mean().iloc[-1])
            else:
                result[f'ma{p}'] = None
        return result
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
        """计算MACD"""
        if len(prices) < slow + signal:
            return {'macd': None, 'signal': None, 'histogram': None, 'trend': 'unknown'}
        
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        
        # 判断趋势
        if histogram.iloc[-1] > 0 and histogram.iloc[-1] > histogram.iloc[-2]:
            trend = 'bullish'  # 上升趋势增强
        elif histogram.iloc[-1] > 0:
            trend = 'bullish_weakening'  # 上升趋势减弱
        elif histogram.iloc[-1] < 0 and histogram.iloc[-1] < histogram.iloc[-2]:
            trend = 'bearish'  # 下降趋势增强
        else:
            trend = 'bearish_weakening'  # 下降趋势减弱
        
        return {
            'macd': float(macd.iloc[-1]),
            'signal': float(signal_line.iloc[-1]),
            'histogram': float(histogram.iloc[-1]),
            'trend': trend
        }
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> Dict[str, float]:
        """计算RSI"""
        if len(prices) < period + 1:
            return {'rsi': None, 'signal': 'unknown'}
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_value = float(rsi.iloc[-1])
        
        # 判断信号
        if rsi_value > 70:
            signal = 'overbought'  # 超买
        elif rsi_value < 30:
            signal = 'oversold'  # 超卖
        elif rsi_value > 50:
            signal = 'bullish'
        else:
            signal = 'bearish'
        
        return {
            'rsi': round(rsi_value, 2),
            'signal': signal
        }
    
    @staticmethod
    def calculate_bollinger(prices: pd.Series, period: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
        """计算布林带"""
        if len(prices) < period:
            return {'upper': None, 'middle': None, 'lower': None, 'position': 'unknown'}
        
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        current_price = float(prices.iloc[-1])
        upper_val = float(upper.iloc[-1])
        lower_val = float(lower.iloc[-1])
        middle_val = float(middle.iloc[-1])
        
        # 判断位置
        band_width = upper_val - lower_val
        position_pct = (current_price - lower_val) / band_width * 100 if band_width > 0 else 50
        
        if current_price > upper_val:
            position = 'above_upper'
        elif current_price < lower_val:
            position = 'below_lower'
        elif position_pct > 80:
            position = 'near_upper'
        elif position_pct < 20:
            position = 'near_lower'
        else:
            position = 'middle'
        
        return {
            'upper': round(upper_val, 4),
            'middle': round(middle_val, 4),
            'lower': round(lower_val, 4),
            'position': position,
            'position_pct': round(position_pct, 1)
        }
    
    @staticmethod
    def calculate_momentum(prices: pd.Series, period: int = 10) -> Dict[str, float]:
        """计算动量指标"""
        if len(prices) < period + 1:
            return {'momentum': None, 'momentum_pct': None}
        
        momentum = float(prices.iloc[-1] - prices.iloc[-period-1])
        momentum_pct = (prices.iloc[-1] / prices.iloc[-period-1] - 1) * 100
        
        return {
            'momentum': round(momentum, 4),
            'momentum_pct': round(float(momentum_pct), 2)
        }


class TrendPredictor:
    """趋势预测器"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> Dict:
        """计算所有技术指标"""
        if 'nav' not in df.columns or len(df) < 10:
            return {'error': '数据不足'}
        
        prices = df['nav']
        
        return {
            'ma': self.indicators.calculate_ma(prices),
            'macd': self.indicators.calculate_macd(prices),
            'rsi': self.indicators.calculate_rsi(prices),
            'bollinger': self.indicators.calculate_bollinger(prices),
            'momentum': self.indicators.calculate_momentum(prices)
        }
    
    def predict_trend(self, 
                      df: pd.DataFrame, 
                      news_sentiment: Optional[Dict] = None) -> Dict:
        """
        预测趋势
        
        Args:
            df: 包含 'nav' 和 'date' 列的DataFrame
            news_sentiment: 新闻情绪分析结果
            
        Returns:
            {
                'prediction': 'up'/'down'/'neutral',
                'probability': float,  # 预测概率 0-100
                'confidence': 'high'/'medium'/'low',
                'factors': [...],  # 影响因素
                'technical_score': float,  # 技术面得分 -100到100
                'sentiment_score': float,  # 情绪面得分
                'indicators': {...}  # 详细指标
            }
        """
        if df is None or len(df) < 20:
            return {
                'prediction': 'unknown',
                'probability': 50,
                'confidence': 'low',
                'error': '历史数据不足，无法预测',
                'factors': []
            }
        
        # 计算技术指标
        indicators = self.calculate_all_indicators(df)
        
        # 技术面评分
        tech_score = 0
        factors = []
        
        # 1. MACD信号 (权重30%)
        macd = indicators.get('macd', {})
        if macd.get('trend') == 'bullish':
            tech_score += 30
            factors.append({'factor': 'MACD', 'signal': '金叉上行', 'impact': 'positive'})
        elif macd.get('trend') == 'bullish_weakening':
            tech_score += 15
            factors.append({'factor': 'MACD', 'signal': '多头减弱', 'impact': 'slightly_positive'})
        elif macd.get('trend') == 'bearish':
            tech_score -= 30
            factors.append({'factor': 'MACD', 'signal': '死叉下行', 'impact': 'negative'})
        elif macd.get('trend') == 'bearish_weakening':
            tech_score -= 15
            factors.append({'factor': 'MACD', 'signal': '空头减弱', 'impact': 'slightly_negative'})
        
        # 2. RSI信号 (权重25%)
        rsi = indicators.get('rsi', {})
        rsi_value = rsi.get('rsi')
        if rsi_value:
            if rsi_value > 70:
                tech_score -= 25
                factors.append({'factor': 'RSI', 'signal': f'超买({rsi_value})', 'impact': 'negative'})
            elif rsi_value < 30:
                tech_score += 25
                factors.append({'factor': 'RSI', 'signal': f'超卖({rsi_value})', 'impact': 'positive'})
            elif rsi_value > 50:
                tech_score += 10
                factors.append({'factor': 'RSI', 'signal': f'偏多({rsi_value})', 'impact': 'slightly_positive'})
            else:
                tech_score -= 10
                factors.append({'factor': 'RSI', 'signal': f'偏空({rsi_value})', 'impact': 'slightly_negative'})
        
        # 3. 布林带位置 (权重20%)
        boll = indicators.get('bollinger', {})
        if boll.get('position') == 'below_lower':
            tech_score += 20
            factors.append({'factor': '布林带', 'signal': '触及下轨', 'impact': 'positive'})
        elif boll.get('position') == 'above_upper':
            tech_score -= 20
            factors.append({'factor': '布林带', 'signal': '触及上轨', 'impact': 'negative'})
        elif boll.get('position') == 'near_lower':
            tech_score += 10
            factors.append({'factor': '布林带', 'signal': '接近下轨', 'impact': 'slightly_positive'})
        elif boll.get('position') == 'near_upper':
            tech_score -= 10
            factors.append({'factor': '布林带', 'signal': '接近上轨', 'impact': 'slightly_negative'})
        
        # 4. 动量 (权重15%)
        momentum = indicators.get('momentum', {})
        mom_pct = momentum.get('momentum_pct')
        if mom_pct is not None:
            if mom_pct > 5:
                tech_score += 15
                factors.append({'factor': '动量', 'signal': f'强势({mom_pct}%)', 'impact': 'positive'})
            elif mom_pct > 0:
                tech_score += 7
                factors.append({'factor': '动量', 'signal': f'偏强({mom_pct}%)', 'impact': 'slightly_positive'})
            elif mom_pct > -5:
                tech_score -= 7
                factors.append({'factor': '动量', 'signal': f'偏弱({mom_pct}%)', 'impact': 'slightly_negative'})
            else:
                tech_score -= 15
                factors.append({'factor': '动量', 'signal': f'弱势({mom_pct}%)', 'impact': 'negative'})
        
        # 5. 均线排列 (权重10%)
        ma = indicators.get('ma', {})
        if ma.get('ma5') and ma.get('ma10') and ma.get('ma20'):
            if ma['ma5'] > ma['ma10'] > ma['ma20']:
                tech_score += 10
                factors.append({'factor': '均线', 'signal': '多头排列', 'impact': 'positive'})
            elif ma['ma5'] < ma['ma10'] < ma['ma20']:
                tech_score -= 10
                factors.append({'factor': '均线', 'signal': '空头排列', 'impact': 'negative'})
        
        # 情绪面评分
        sentiment_score = 0
        if news_sentiment:
            sentiment_score = news_sentiment.get('sentiment_score', 0)
            if sentiment_score > 20:
                factors.append({'factor': '市场情绪', 'signal': '积极', 'impact': 'positive'})
            elif sentiment_score < -20:
                factors.append({'factor': '市场情绪', 'signal': '悲观', 'impact': 'negative'})
            else:
                factors.append({'factor': '市场情绪', 'signal': '中性', 'impact': 'neutral'})
        
        # 综合评分 (技术面70% + 情绪面30%)
        final_score = tech_score * 0.7 + sentiment_score * 0.3
        
        # 计算预测概率
        # 将评分映射到概率: -100~100 -> 20%~80%
        probability = 50 + final_score * 0.3
        probability = max(20, min(80, probability))  # 限制在20-80之间
        
        # 确定预测方向
        if final_score > 15:
            prediction = 'up'
        elif final_score < -15:
            prediction = 'down'
        else:
            prediction = 'neutral'
        
        # 确定置信度
        if abs(final_score) > 40:
            confidence = 'high'
        elif abs(final_score) > 20:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        return {
            'prediction': prediction,
            'probability': round(probability, 1),
            'confidence': confidence,
            'technical_score': round(tech_score, 1),
            'sentiment_score': round(sentiment_score, 1),
            'final_score': round(final_score, 1),
            'factors': factors,
            'indicators': indicators,
            'predicted_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'disclaimer': '本预测仅供参考，不构成任何投资建议。市场有风险，投资需谨慎。'
        }
    
    def get_prediction_summary(self, prediction: Dict) -> str:
        """生成预测摘要文本"""
        pred = prediction.get('prediction', 'unknown')
        prob = prediction.get('probability', 50)
        conf = prediction.get('confidence', 'low')
        
        pred_text = {'up': '看涨', 'down': '看跌', 'neutral': '震荡', 'unknown': '未知'}
        conf_text = {'high': '高', 'medium': '中', 'low': '低'}
        
        return f"{pred_text.get(pred, '未知')} | 概率 {prob}% | 置信度 {conf_text.get(conf, '低')}"


# 全局单例
_predictor: Optional[TrendPredictor] = None

def get_trend_predictor() -> TrendPredictor:
    global _predictor
    if _predictor is None:
        _predictor = TrendPredictor()
    return _predictor
