# backend/services/calculator.py
"""
量化指标计算服务 - 精确口径
"""
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, Optional, List
import logging

try:
    from config import get_settings
except ImportError:
    from backend.config import get_settings

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """量化指标计算器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.risk_free_rate = self.settings.RISK_FREE_RATE
        self.min_data_days = self.settings.MIN_DATA_DAYS
    
    def calculate_metrics(self, df: pd.DataFrame, 
                          benchmark_df: pd.DataFrame = None,
                          benchmark_symbol: str = None) -> Optional[Dict]:
        """
        计算全部量化指标
        
        Args:
            df: 基金净值数据，必须包含 'date' 和 'nav' 列
            benchmark_df: 基准数据，包含 'date' 和 'benchmark_return' 列
            benchmark_symbol: 基准代码
        
        Returns:
            指标字典，或 None（数据不足）
        """
        df = df.copy()
        df['daily_return'] = df['nav'].pct_change()
        returns = df['daily_return'].dropna()
        
        if len(returns) < self.min_data_days:
            logger.warning(f"数据不足: {len(returns)} < {self.min_data_days}")
            return None
        
        daily_rf = self.risk_free_rate / 252
        
        # === 1. 收益指标（基于实际日期计算年化） ===
        first_date = df['date'].iloc[0]
        last_date = df['date'].iloc[-1]
        actual_days = (last_date - first_date).days
        actual_years = actual_days / 365.0
        
        total_return = df['nav'].iloc[-1] / df['nav'].iloc[0] - 1
        annual_return = (1 + total_return) ** (1 / actual_years) - 1 if actual_years > 0 else 0
        
        # 区间收益（使用实际交易日）
        return_1w = self._get_return(df, 5)
        return_1m = self._get_return(df, 22)
        return_3m = self._get_return(df, 66)
        return_6m = self._get_return(df, 132)
        return_1y = self._get_return(df, 252)
        
        # === 2. 风险指标 ===
        volatility = returns.std() * np.sqrt(252)
        
        # 回撤计算（统一为负数存储，正数展示）
        df['cum_max'] = df['nav'].cummax()
        df['drawdown'] = (df['nav'] - df['cum_max']) / df['cum_max']
        max_drawdown = df['drawdown'].min()  # 负数
        current_drawdown = df['drawdown'].iloc[-1]  # 负数
        
        # 下行标准差
        downside_returns = returns[returns < daily_rf]
        downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0.001
        
        # === 3. 风险调整收益 ===
        excess_return = annual_return - self.risk_free_rate
        sharpe = excess_return / volatility if volatility > 0 else 0
        sortino = excess_return / downside_std if downside_std > 0 else 0
        calmar = abs(annual_return / max_drawdown) if max_drawdown != 0 else 0
        
        # === 4. Alpha/Beta（相对基准） ===
        alpha, beta, info_ratio, treynor, tracking_error = 0, 1, 0, 0, 0
        
        if benchmark_df is not None and len(benchmark_df) > 0:
            try:
                merged = pd.merge(
                    df[['date', 'daily_return']], 
                    benchmark_df[['date', 'benchmark_return']], 
                    on='date', how='inner'
                ).dropna()
                
                if len(merged) > 30:
                    fund_ret = merged['daily_return'].values
                    bench_ret = merged['benchmark_return'].values
                    
                    # Beta = Cov(fund, benchmark) / Var(benchmark)
                    cov = np.cov(fund_ret, bench_ret)[0, 1]
                    var = np.var(bench_ret)
                    beta = cov / var if var > 0 else 1
                    
                    # Alpha = 基金年化 - (无风险 + Beta * (基准年化 - 无风险))
                    fund_annual = (1 + fund_ret.mean()) ** 252 - 1
                    bench_annual = (1 + bench_ret.mean()) ** 252 - 1
                    alpha = fund_annual - (self.risk_free_rate + beta * (bench_annual - self.risk_free_rate))
                    
                    # 跟踪误差与信息比率
                    excess = fund_ret - bench_ret
                    tracking_error = np.std(excess) * np.sqrt(252)
                    info_ratio = (excess.mean() * 252) / tracking_error if tracking_error > 0 else 0
                    
                    # Treynor
                    treynor = excess_return / beta if beta != 0 else 0
            except Exception as e:
                logger.warning(f"计算 Alpha/Beta 失败: {e}")
        
        # === 5. 统计指标 ===
        win_rate = (returns > 0).sum() / len(returns)
        avg_win = returns[returns > 0].mean() if (returns > 0).any() else 0
        avg_loss = abs(returns[returns < 0].mean()) if (returns < 0).any() else 0.001
        profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        # === 5.5 高级指标（多因子模型新增） ===
        # 下行夏普比率
        downside_sharpe = excess_return / downside_std if downside_std > 0 else 0
        
        # Alpha 稳定性（滚动窗口 Alpha 的变异系数）
        alpha_consistency = self._calculate_alpha_consistency(df, benchmark_df) if benchmark_df is not None else 0.5
        
        # === 6. 综合评分 ===
        score = self._calculate_score(
            sharpe=sharpe,
            max_drawdown=max_drawdown,
            alpha=alpha,
            info_ratio=info_ratio,
            win_rate=win_rate,
            downside_sharpe=downside_sharpe,
            alpha_consistency=alpha_consistency
        )
        
        grade, grade_text = self._get_grade(score)
        invest_type, invest_reason = self._get_invest_advice(
            sharpe=sharpe,
            max_drawdown=max_drawdown,
            alpha=alpha,
            beta=beta,
            current_drawdown=current_drawdown,
            return_1m=return_1m
        )
        
        # === 7. 图表数据 ===
        chart_data = self._prepare_chart_data(df)
        rolling_drawdown = self._calculate_rolling_drawdown(df)
        
        return {
            "latest_nav": round(df['nav'].iloc[-1], 4),
            "latest_date": last_date.strftime("%Y-%m-%d"),
            "benchmark_symbol": benchmark_symbol or self.settings.DEFAULT_BENCHMARK,
            
            "return_1w": return_1w,
            "return_1m": return_1m,
            "return_3m": return_3m,
            "return_6m": return_6m,
            "return_1y": return_1y,
            "annual_return": round(annual_return * 100, 2),
            
            "volatility": round(volatility * 100, 2),
            "max_drawdown": round(max_drawdown * 100, 2),  # 负数，展示时取绝对值
            "current_drawdown": round(current_drawdown * 100, 2),
            
            "sharpe": round(sharpe, 2),
            "sortino": round(sortino, 2),
            "calmar": round(calmar, 2),
            
            "alpha": round(alpha * 100, 2),
            "beta": round(beta, 2),
            "info_ratio": round(info_ratio, 2),
            "treynor": round(treynor * 100, 2),
            "tracking_error": round(tracking_error * 100, 2),
            
            "win_rate": round(win_rate * 100, 1),
            "profit_loss_ratio": round(profit_loss_ratio, 2),
            
            # 新增多因子指标
            "downside_sharpe": round(downside_sharpe, 2),
            "alpha_consistency": round(alpha_consistency, 2),
            
            "score": score,
            "grade": grade,
            "grade_text": grade_text,
            "invest_type": invest_type,
            "invest_reason": invest_reason,
            
            "chart_data": chart_data,
            "rolling_drawdown": rolling_drawdown,
        }
    
    def _calculate_rolling_drawdown(self, df: pd.DataFrame, window: int = 252) -> List[Dict]:
        """计算滚动最大回撤"""
        try:
            temp_df = df.copy()
            temp_df['rolling_max'] = temp_df['nav'].rolling(window=window, min_periods=20).max()
            temp_df['rolling_dd'] = (temp_df['nav'] - temp_df['rolling_max']) / temp_df['rolling_max']
            
            # 仅取最近 60 个点用于展示
            result = temp_df.tail(60)[['date', 'rolling_dd']].copy()
            result['date'] = result['date'].dt.strftime('%m-%d')
            result['rolling_dd'] = (result['rolling_dd'] * 100).round(2)
            return result.to_dict(orient='records')
        except Exception:
            return []
    
    def _calculate_alpha_consistency(self, df: pd.DataFrame, benchmark_df: pd.DataFrame, window: int = 60) -> float:
        """
        计算 Alpha 稳定性
        使用滚动窗口计算 Alpha，然后计算变异系数（标准差/均值）
        返回 0-1 之间的值，越高表示越稳定
        """
        try:
            if benchmark_df is None or len(benchmark_df) < window * 2:
                return 0.5
            
            merged = pd.merge(
                df[['date', 'daily_return']], 
                benchmark_df[['date', 'benchmark_return']], 
                on='date', how='inner'
            ).dropna()
            
            if len(merged) < window * 2:
                return 0.5
            
            rolling_alphas = []
            for i in range(window, len(merged), window // 2):  # 滑动步长为窗口的一半
                window_data = merged.iloc[i-window:i]
                fund_ret = window_data['daily_return'].values
                bench_ret = window_data['benchmark_return'].values
                
                cov = np.cov(fund_ret, bench_ret)[0, 1]
                var = np.var(bench_ret)
                beta = cov / var if var > 0 else 1
                
                fund_annual = (1 + fund_ret.mean()) ** 252 - 1
                bench_annual = (1 + bench_ret.mean()) ** 252 - 1
                window_alpha = fund_annual - (self.risk_free_rate + beta * (bench_annual - self.risk_free_rate))
                rolling_alphas.append(window_alpha)
            
            if len(rolling_alphas) < 2:
                return 0.5
            
            alphas = np.array(rolling_alphas)
            mean_alpha = np.mean(alphas)
            std_alpha = np.std(alphas)
            
            # 变异系数，越小越稳定
            cv = abs(std_alpha / mean_alpha) if abs(mean_alpha) > 0.001 else 1
            
            # 转换为 0-1 的稳定性分数，cv 越小，分数越高
            consistency = max(0, min(1, 1 - cv))
            return consistency
            
        except Exception as e:
            logger.warning(f"计算 Alpha 稳定性失败: {e}")
            return 0.5
    
    @staticmethod
    def calculate_peer_percentile(fund_score: float, peer_scores: list) -> float:
        """
        计算同类排名百分位
        
        Args:
            fund_score: 当前基金分数
            peer_scores: 同类基金分数列表
        
        Returns:
            0-100 的百分位，越高表示排名越靠前
        """
        if not peer_scores:
            return 50.0
        
        # 计算有多少比它低的
        lower_count = sum(1 for s in peer_scores if s < fund_score)
        percentile = (lower_count / len(peer_scores)) * 100
        return round(percentile, 1)
    
    def _get_return(self, df: pd.DataFrame, days: int) -> Optional[float]:
        """获取区间收益"""
        if len(df) > days:
            return round((df['nav'].iloc[-1] / df['nav'].iloc[-days] - 1) * 100, 2)
        return None
    
    def _calculate_score(self, sharpe: float, max_drawdown: float, 
                         alpha: float, info_ratio: float, win_rate: float,
                         downside_sharpe: float = 0, alpha_consistency: float = 0.5,
                         peer_percentile: float = 50) -> int:
        """
        计算综合评分 - 多因子模型
        
        评分维度：
        - 夏普比率: 最高 20 分
        - 最大回撤: 最高 15 分
        - Alpha: 最高 12 分
        - 下行夏普: 最高 8 分
        - Alpha 稳定性: 最高 8 分
        - 同类排名: 最高 10 分
        - 信息比率: 最高 5 分
        - 胜率: 最高 5 分
        - 基础分: 20 分
        """
        score = 20  # 基础分
        
        # 夏普评分 (最高20分)
        if sharpe >= 2:
            score += 20
        elif sharpe >= 1.5:
            score += 16
        elif sharpe >= 1:
            score += 10
        elif sharpe >= 0.5:
            score += 5
        elif sharpe < 0:
            score -= 10
        
        # 回撤评分 (最高15分)
        if max_drawdown > -0.1:
            score += 15
        elif max_drawdown > -0.2:
            score += 10
        elif max_drawdown > -0.3:
            score += 5
        elif max_drawdown < -0.5:
            score -= 10
        
        # Alpha评分 (最高12分)
        if alpha > 0.15:
            score += 12
        elif alpha > 0.1:
            score += 8
        elif alpha > 0.05:
            score += 4
        elif alpha < -0.1:
            score -= 8
        
        # 下行夏普评分 (最高8分) - 新增
        if downside_sharpe >= 2:
            score += 8
        elif downside_sharpe >= 1.5:
            score += 6
        elif downside_sharpe >= 1:
            score += 4
        elif downside_sharpe >= 0.5:
            score += 2
        
        # Alpha稳定性评分 (最高8分) - 新增
        if alpha_consistency >= 0.8:
            score += 8
        elif alpha_consistency >= 0.6:
            score += 6
        elif alpha_consistency >= 0.4:
            score += 4
        elif alpha_consistency >= 0.2:
            score += 2
        
        # 同类排名评分 (最高10分) - 新增
        if peer_percentile >= 90:
            score += 10
        elif peer_percentile >= 75:
            score += 7
        elif peer_percentile >= 50:
            score += 4
        elif peer_percentile >= 25:
            score += 2
        
        # 信息比率加分 (最高5分)
        if info_ratio > 1:
            score += 5
        elif info_ratio > 0.5:
            score += 2
        
        # 胜率加分 (最高5分)
        if win_rate > 0.55:
            score += 5
        elif win_rate > 0.52:
            score += 2
        
        return max(0, min(100, score))
    
    def _get_grade(self, score: int) -> tuple:
        """获取评级"""
        if score >= 85:
            return "A+", "极优"
        elif score >= 75:
            return "A", "优秀"
        elif score >= 65:
            return "B", "良好"
        elif score >= 55:
            return "C", "中等"
        else:
            return "D", "较差"
    
    def _get_invest_advice(self, sharpe: float, max_drawdown: float,
                           alpha: float, beta: float, 
                           current_drawdown: float, return_1m: float) -> tuple:
        """获取投资建议"""
        if sharpe > 1.5 and max_drawdown > -0.2 and alpha > 0.05:
            return "长线定投", "高夏普正Alpha，适合长期持有"
        elif return_1m and return_1m > 3 and current_drawdown > -0.05:
            return "短线机会", "近期强势回撤小，短期有机会"
        elif current_drawdown < -0.15 and sharpe > 1:
            return "抄底机会", "优质基金回调中，可分批建仓"
        elif sharpe > 1 and alpha > 0:
            return "均衡配置", "风险收益均衡，适合核心持仓"
        elif beta < 0.8 and max_drawdown > -0.15:
            return "防守配置", "低Beta低波动，适合避险"
        else:
            return "观望", "暂不符合买入条件"
    
    def _prepare_chart_data(self, df: pd.DataFrame, days: int = 60) -> List[Dict]:
        """准备图表数据"""
        chart_df = df.tail(days)[['date', 'nav']].copy()
        chart_df['date'] = chart_df['date'].dt.strftime('%m-%d')
        return chart_df.to_dict(orient='records')

    def analyze_market_sentiment(self, news: List[Dict], breadth: Dict[str, Any]) -> Dict[str, Any]:
        """
        市场情绪分析 - 统一入口
        """
        if not news and breadth.get('total', 0) == 0:
            return {"score": 50, "trend": "中性", "summary": "暂未获取到足够资讯进行分析。"}

        # 1. 关键词情绪分析
        pos_words = ["上涨", "利好", "反弹", "surge", "gain", "bull", "growth", "profit", "jump", "高开", "复苏", "大涨", "回暖"]
        neg_words = ["下跌", "利空", "回调", "drop", "loss", "bear", "decline", "risk", "warn", "低开", "衰退", "大跌", "跳水"]
        
        news_score = 50
        pos_count = 0
        neg_count = 0
        
        for n in news:
            text = (n.get('title', '') + " " + n.get('content', '')).lower()
            p = sum(1 for w in pos_words if w in text)
            ne = sum(1 for w in neg_words if w in text)
            pos_count += p
            neg_count += ne
            
        news_score += (pos_count - neg_count) * 1.5
        
        # 2. 市场分时情绪 (Breadth)
        breadth_score = 50
        if breadth.get('total', 0) > 0:
            breadth_score = breadth.get('up_ratio', 50)
            
        # 3. 综合评分 (60% 市场宽度, 40% 新闻情绪)
        combined_score = (breadth_score * 0.6) + (news_score * 0.4)
        combined_score = max(5, min(95, combined_score))
        
        # 4. 标签映射
        trend = "震荡"
        fear_greed = "Neutral"
        if combined_score > 60: trend, fear_greed = "偏多", "Greed"
        if combined_score > 80: trend, fear_greed = "乐观", "Extreme Greed"
        if combined_score < 40: trend, fear_greed = "偏空", "Fear"
        if combined_score < 20: trend, fear_greed = "悲观", "Extreme Fear"
        
        summary = f"基于 {len(news)} 条全网快讯及全市场 {breadth.get('total', 0)} 只 A 股表现分析：当前市场处于 {fear_greed} 状态。"
        if breadth.get('total', 0) > 0:
            summary += f" 涨跌比为 {breadth.get('up', 0)}:{breadth.get('down', 0)}，活跃度{trend}。"

        return {
            "score": int(combined_score),
            "trend": trend,
            "fear_greed": fear_greed,
            "breadth": breadth,
            "summary": summary,
            "news_stats": {"pos": pos_count, "neg": neg_count},
            "hot_sectors": ["全球市场", "混合资产"]
        }


# 全局实例
_calculator = None

def get_calculator() -> MetricsCalculator:
    """获取计算器实例"""
    global _calculator
    if _calculator is None:
        _calculator = MetricsCalculator()
    return _calculator
