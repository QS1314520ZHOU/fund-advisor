# backend/services/snapshot.py
"""
快照服务 - 优化版
分阶段处理：快速筛选 → 批量获取净值 → 计算指标 → 排序入选
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..database import get_db
from ..config import get_settings
from .data_fetcher import get_data_fetcher

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """指标计算器"""
    
    @staticmethod
    def calculate_returns(nav_series: pd.Series, periods: Dict[str, int]) -> Dict[str, float]:
        """计算各期间收益率"""
        returns = {}
        if len(nav_series) < 2:
            return returns
        
        latest_nav = nav_series.iloc[-1]
        
        for name, days in periods.items():
            if len(nav_series) >= days:
                start_nav = nav_series.iloc[-days]
                ret = (latest_nav / start_nav - 1) * 100
                returns[name] = round(ret, 2)
            else:
                returns[name] = None
        
        return returns
    
    @staticmethod
    def calculate_annualized_return(nav_series: pd.Series, days: int) -> float:
        """计算年化收益率"""
        if len(nav_series) < 2:
            return 0.0
        
        total_return = nav_series.iloc[-1] / nav_series.iloc[0] - 1
        years = days / 252  # 交易日
        if years <= 0:
            return 0.0
        
        annualized = (1 + total_return) ** (1 / years) - 1
        return round(annualized * 100, 2)
    
    @staticmethod
    def calculate_volatility(returns: pd.Series) -> float:
        """计算年化波动率"""
        if len(returns) < 2:
            return 0.0
        
        daily_vol = returns.std()
        annual_vol = daily_vol * np.sqrt(252)
        return round(annual_vol * 100, 2)
    
    @staticmethod
    def calculate_max_drawdown(nav_series: pd.Series) -> Tuple[float, float]:
        """计算最大回撤和当前回撤，返回正数"""
        if len(nav_series) < 2:
            return 0.0, 0.0
        
        # 计算累计最高点
        cummax = nav_series.cummax()
        drawdown = (nav_series - cummax) / cummax
        
        max_dd = abs(drawdown.min()) * 100  # 转为正数百分比
        current_dd = abs(drawdown.iloc[-1]) * 100
        
        return round(max_dd, 2), round(current_dd, 2)
    
    @staticmethod
    def calculate_sharpe(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """计算夏普比率"""
        if len(returns) < 20:
            return 0.0
        
        excess_returns = returns - risk_free_rate / 252
        if excess_returns.std() == 0:
            return 0.0
        
        sharpe = np.sqrt(252) * excess_returns.mean() / excess_returns.std()
        return round(sharpe, 2)
    
    @staticmethod
    def calculate_alpha_beta(
        fund_returns: pd.Series, 
        benchmark_returns: pd.Series
    ) -> Tuple[float, float]:
        """计算 Alpha 和 Beta"""
        if len(fund_returns) < 20 or len(benchmark_returns) < 20:
            return 0.0, 1.0
        
        # 对齐数据
        aligned = pd.concat([fund_returns, benchmark_returns], axis=1, join='inner').dropna()
        if len(aligned) < 20:
            return 0.0, 1.0
        
        fund_ret = aligned.iloc[:, 0]
        bench_ret = aligned.iloc[:, 1]
        
        # 计算 Beta
        covariance = np.cov(fund_ret, bench_ret)[0, 1]
        variance = np.var(bench_ret)
        beta = covariance / variance if variance != 0 else 1.0
        
        # 计算 Alpha（年化）
        alpha = (fund_ret.mean() - beta * bench_ret.mean()) * 252
        
        return round(alpha * 100, 2), round(beta, 2)
    
    @staticmethod
    def calculate_win_rate(returns: pd.Series) -> float:
        """计算胜率"""
        if len(returns) < 2:
            return 0.0
        
        wins = (returns > 0).sum()
        total = len(returns.dropna())
        return round(wins / total * 100, 2) if total > 0 else 0.0
    
    @staticmethod
    def calculate_profit_loss_ratio(returns: pd.Series) -> float:
        """计算盈亏比"""
        if len(returns) < 2:
            return 0.0
        
        gains = returns[returns > 0]
        losses = returns[returns < 0]
        
        avg_gain = gains.mean() if len(gains) > 0 else 0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0
        
        return round(avg_gain / avg_loss, 2) if avg_loss > 0 else 0.0


class SnapshotService:
    """快照服务"""
    
    # 评分权重配置 - 升级为多因子模型
    SCORE_WEIGHTS = {
        # 收益能力 (40%)
        'alpha': 0.15,
        'alpha_consistency': 0.10,  # 新增：Alpha稳定性
        'annual_return': 0.15,
        
        # 风险控制 (35%)
        'sharpe': 0.15,
        'max_drawdown': 0.10,      # 负向指标
        'volatility': 0.05,        # 负向指标
        'downside_sharpe': 0.05,   # 新增：下行夏普
        
        # 相对表现 (25%)
        'peer_percentile': 0.15,   # 新增：同类排名百分位
        'win_rate': 0.05,
        'profit_loss_ratio': 0.05
    }
    
    # 收益期间配置
    RETURN_PERIODS = {
        'return_1w': 5,
        'return_1m': 20,
        'return_3m': 60,
        'return_6m': 120,
        'return_1y': 250,
        'return_1d': 1
    }
    
    def __init__(self):
        self.db = get_db()
        self.settings = get_settings()
        self.fetcher = get_data_fetcher()
        self.calculator = MetricsCalculator()
        
        # 进度状态
        self._progress = {
            'status': 'idle',
            'step': '',
            'current': 0,
            'total': 0,
            'message': ''
        }
        self._is_updating = False
        self._benchmark_data: Optional[pd.DataFrame] = None
    
    def is_updating(self) -> bool:
        return self._is_updating
    
    def get_progress(self) -> Dict:
        return self._progress.copy()
    
    def _set_progress(self, step: str, current: int, total: int, message: str):
        self._progress = {
            'status': 'running' if self._is_updating else 'idle',
            'step': step,
            'current': current,
            'total': total,
            'message': message,
            'percentage': round(current / total * 100, 1) if total > 0 else 0
        }
        logger.info(f"[{step}] {current}/{total} - {message}")
    
    def _progress_callback(self, step: str, current: int, total: int, message: str):
        """进度回调函数"""
        self._set_progress(step, current, total, message)
    
    def create_full_snapshot(self, max_qualified: int = 230, skip_filter: bool = False) -> Dict[str, Any]:
        """
        创建完整快照
        分阶段执行：筛选 → 获取净值 → 计算指标 → 排序入选
        """
        if self._is_updating:
            return {'success': False, 'error': '更新任务正在进行中'}
        
        self._is_updating = True
        start_time = datetime.now()
        log_id = None
        
        try:
            # 创建更新日志
            log_id = self.db.create_update_log('full_snapshot')
            
            # ========== 阶段1：获取基准数据 ==========
            self._set_progress('benchmark', 0, 1, '正在获取基准数据...')
            self._benchmark_data = self.fetcher.get_benchmark_data(
                symbol=self.settings.DEFAULT_BENCHMARK.replace('.', '')
            )
            
            if self._benchmark_data is None or len(self._benchmark_data) < 60:
                raise Exception('基准数据获取失败或数据不足')
            
            self._set_progress('benchmark', 1, 1, f'基准数据获取完成: {len(self._benchmark_data)} 条')
            
            # ========== 阶段2：快速筛选候选基金 ==========
            if skip_filter:
                logger.info("执行无过滤全量同步 (0-5点夜间模式)")
                
            candidates = self.fetcher.filter_candidate_funds(
                progress_callback=self._progress_callback,
                skip_filter=skip_filter
            )
            
            if not candidates:
                raise Exception('候选基金筛选失败，无符合条件的基金')
            
            total_candidates = len(candidates)
            self._set_progress('filtering', 1, 1, f'筛选完成: {total_candidates} 只候选基金')
            
            # ========== 阶段3：批量获取净值数据 ==========
            codes = [c['code'] for c in candidates]
            
            # 构建代码到基金信息的映射
            code_to_info = {c['code']: c for c in candidates}
            
            # 批量获取净值
            nav_data_map = self.fetcher.get_fund_nav_batch(
                codes=codes,
                progress_callback=self._progress_callback
            )
            
            if not nav_data_map:
                raise Exception('净值数据获取失败')
            
            self._set_progress('fetching_nav', len(nav_data_map), total_candidates,
                             f'净值获取完成: {len(nav_data_map)}/{total_candidates} 只')
            
            # ========== 阶段4：计算指标并评分 ==========
            snapshot_date = datetime.now().strftime('%Y-%m-%d')
            
            # 创建快照记录
            snapshot_id = self.db.create_snapshot(
                snapshot_date=snapshot_date,
                total_funds=total_candidates,
                benchmark=self.settings.DEFAULT_BENCHMARK
            )
            
            scored_funds = []
            processed = 0
            total_to_process = len(nav_data_map)
            
            for code, nav_df in nav_data_map.items():
                processed += 1
                if processed % 100 == 0:
                    self._set_progress('calculating', processed, total_to_process,
                                     f'计算指标: {processed}/{total_to_process}')
                
                try:
                    metrics = self._calculate_fund_metrics(code, nav_df)
                    if metrics:
                        fund_info = code_to_info.get(code, {})
                        metrics['name'] = fund_info.get('name', '')
                        metrics['fund_type'] = fund_info.get('fund_type', '')
                        metrics['themes'] = fund_info.get('themes', [])
                        
                        # 计算综合评分
                        score = self._calculate_score(metrics)
                        metrics['score'] = score
                        
                        scored_funds.append(metrics)
                except Exception as e:
                    logger.debug(f"计算 {code} 指标失败: {e}")
            
            self._set_progress('calculating', total_to_process, total_to_process,
                             f'指标计算完成: {len(scored_funds)} 只')
            
            # ========== 阶段5：排序并入选 ==========
            self._set_progress('ranking', 0, 1, '正在排序入选...')
            
            # 按评分排序
            scored_funds.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            # 取前 max_qualified 只
            qualified_funds = scored_funds[:max_qualified]
            
            # 为入选基金分配投资标签
            qualified_funds = self._assign_investment_labels(qualified_funds)
            
            # 保存到数据库
            for fund in qualified_funds:
                # 保存基金基础信息
                self.db.upsert_fund(
                    code=fund['code'],
                    name=fund['name'],
                    fund_type=fund['fund_type'],
                    themes=fund.get('themes', [])
                )
                
                # 保存指标
                self.db.save_fund_metrics(
                    snapshot_id=snapshot_id,
                    code=fund['code'],
                    metrics=fund
                )
            
            # 完成快照
            self.db.complete_snapshot(
                snapshot_id=snapshot_id,
                qualified_funds=len(qualified_funds),
                status='success'
            )
            
            # 完成日志
            elapsed = (datetime.now() - start_time).total_seconds()
            self.db.complete_update_log(
                log_id=log_id,
                status='success',
                funds_processed=total_to_process,
                funds_qualified=len(qualified_funds),
                message=f'耗时 {elapsed:.1f} 秒'
            )
            
            self._set_progress('completed', 1, 1, 
                             f'快照创建成功: {len(qualified_funds)}/{total_candidates} 只入选')
            
            return {
                'success': True,
                'snapshot_id': snapshot_id,
                'snapshot_date': snapshot_date,
                'total_candidates': total_candidates,
                'qualified_count': len(qualified_funds),
                'elapsed_seconds': elapsed
            }
            
        except Exception as e:
            logger.error(f"创建快照失败: {e}", exc_info=True)
            
            if log_id:
                self.db.complete_update_log(
                    log_id=log_id,
                    status='failed',
                    message=str(e)
                )
            
            self._set_progress('failed', 0, 0, f'快照创建失败: {e}')
            
            return {'success': False, 'error': str(e)}
        
        finally:
            self._is_updating = False
    
    def _calculate_fund_metrics(self, code: str, nav_df: pd.DataFrame) -> Optional[Dict]:
        """计算单只基金的所有指标"""
        try:
            if nav_df is None or len(nav_df) < 60:
                return None
            
            nav_series = nav_df['nav']
            returns = nav_df['daily_return'] / 100  # 转为小数
            
            # 基础信息
            metrics = {
                'code': code,
                'latest_nav': round(nav_series.iloc[-1], 4),
                'nav_date': nav_df['date'].iloc[-1].strftime('%Y-%m-%d'),
                'return_1d': round(nav_df['daily_return'].iloc[-1], 2) if 'daily_return' in nav_df.columns else 0.0,
                'data_days': len(nav_df)
            }
            
            # 收益率
            period_returns = self.calculator.calculate_returns(nav_series, self.RETURN_PERIODS)
            metrics.update(period_returns)
            
            # 年化收益
            metrics['annual_return'] = self.calculator.calculate_annualized_return(
                nav_series, len(nav_df)
            )
            
            # 波动率
            metrics['volatility'] = self.calculator.calculate_volatility(returns)
            
            # 最大回撤
            max_dd, current_dd = self.calculator.calculate_max_drawdown(nav_series)
            metrics['max_drawdown'] = max_dd
            metrics['current_drawdown'] = current_dd
            
            # 夏普比率
            metrics['sharpe'] = self.calculator.calculate_sharpe(returns)
            
            # Alpha 和 Beta
            if self._benchmark_data is not None:
                # 对齐基准数据
                merged = pd.merge(
                    nav_df[['date', 'daily_return']],
                    self._benchmark_data[['date', 'benchmark_return']],
                    on='date',
                    how='inner'
                )
                
                if len(merged) >= 60:
                    fund_ret = merged['daily_return'] / 100
                    bench_ret = merged['benchmark_return']
                    
                    alpha, beta = self.calculator.calculate_alpha_beta(fund_ret, bench_ret)
                    metrics['alpha'] = alpha
                    metrics['beta'] = beta
                else:
                    metrics['alpha'] = 0.0
                    metrics['beta'] = 1.0
            else:
                metrics['alpha'] = 0.0
                metrics['beta'] = 1.0
            
            # 胜率和盈亏比
            metrics['win_rate'] = self.calculator.calculate_win_rate(returns)
            metrics['profit_loss_ratio'] = self.calculator.calculate_profit_loss_ratio(returns)
            
            return metrics
            
        except Exception as e:
            logger.debug(f"计算 {code} 指标异常: {e}")
            return None
    
    def _calculate_score(self, metrics: Dict) -> float:
        """计算综合评分（0-100）"""
        score = 0.0
        
        # Alpha 评分 (归一化到 0-100)
        alpha = metrics.get('alpha', 0)
        alpha_score = min(max((alpha + 10) / 30 * 100, 0), 100)
        score += alpha_score * self.SCORE_WEIGHTS['alpha']
        
        # 夏普比率评分
        sharpe = metrics.get('sharpe', 0)
        sharpe_score = min(max((sharpe + 0.5) / 3 * 100, 0), 100)
        score += sharpe_score * self.SCORE_WEIGHTS['sharpe']
        
        # 年化收益评分
        annual_return = metrics.get('annual_return', 0)
        return_score = min(max((annual_return + 10) / 50 * 100, 0), 100)
        score += return_score * self.SCORE_WEIGHTS['annual_return']
        
        # 最大回撤评分（负向，回撤越小越好）
        max_dd = metrics.get('max_drawdown', 50)
        dd_score = max(100 - max_dd * 2, 0)
        score += dd_score * self.SCORE_WEIGHTS['max_drawdown']
        
        # 波动率评分（负向）
        volatility = metrics.get('volatility', 30)
        vol_score = max(100 - volatility * 2, 0)
        score += vol_score * self.SCORE_WEIGHTS['volatility']
        
        # 胜率评分
        win_rate = metrics.get('win_rate', 50)
        score += win_rate * self.SCORE_WEIGHTS['win_rate']
        
        # 盈亏比评分
        pl_ratio = metrics.get('profit_loss_ratio', 1)
        pl_score = min(pl_ratio / 2 * 100, 100)
        score += pl_score * self.SCORE_WEIGHTS['profit_loss_ratio']
        
        return round(score, 2)
    
    def _assign_investment_labels(self, funds: List[Dict]) -> List[Dict]:
        """为基金分配投资标签"""
        for i, fund in enumerate(funds):
            labels = []
            reasons = []
            
            # TOP10
            if i < 10:
                labels.append('TOP10')
                reasons.append('综合评分前10')
            
            # 高 Alpha
            if fund.get('alpha', 0) > 10:
                labels.append('高Alpha')
                reasons.append(f"Alpha {fund['alpha']}%")
            
            # 长线持有
            if fund.get('sharpe', 0) > 1.5 and fund.get('max_drawdown', 100) < 20:
                labels.append('长线')
                reasons.append('夏普高+回撤低')
            
            # 短线交易
            if fund.get('volatility', 0) > 25 and fund.get('win_rate', 0) > 55:
                labels.append('短线')
                reasons.append('波动大+胜率高')
            
            # 防守型
            if fund.get('max_drawdown', 100) < 15 and fund.get('volatility', 100) < 15:
                labels.append('防守')
                reasons.append('低回撤+低波动')
            
            # 进攻型
            if fund.get('annual_return', 0) > 30 and fund.get('alpha', 0) > 5:
                labels.append('进攻')
                reasons.append('高收益+正Alpha')
            
            # 默认标签
            if not labels:
                labels.append('均衡')
                reasons.append('综合表现稳定')
            
            fund['labels'] = labels
            fund['reasons'] = reasons
        
        return funds
    
    async def get_recommendations(self, theme: str = None, category: str = None) -> Dict[str, Any]:
        """获取推荐列表 (异步支持 AI 宏观总结)"""
        snapshot = self.db.get_latest_snapshot()
        
        if not snapshot:
            return {
                'status': 'no_data',
                'message': '暂无快照数据，请先更新快照',
                'recommendations': {}
            }
        
        funds = self.db.get_recommendations(
            snapshot_id=snapshot['id'],
            theme=theme,
            limit=100
        )
        
        if not funds:
            return {
                'status': 'empty',
                'message': f'该{"主题" if theme else "分类"}暂无数据',
                'snapshot_date': snapshot['snapshot_date'],
                'total_funds': snapshot.get('total_funds', 0),
                'qualified_funds': snapshot.get('qualified_funds', 0),
                'recommendations': {}
            }
        
        # 按标签分类整理
        categorized = {
            'top10': [],
            'high_alpha': [],
            'long_term': [],
            'short_term': [],
            'low_beta': []
        }
        
        for fund in funds:
            labels = fund.get('labels', [])
            reasons = fund.get('reasons', [])
            
            fund_item = {
                'code': fund['code'],
                'name': fund.get('name', ''),
                'score': fund.get('score', 0),
                'grade': self._get_grade(fund.get('score', 0)),
                'alpha': fund.get('alpha', 0),
                'beta': fund.get('beta', 1.0),
                'sharpe': fund.get('sharpe', 0),
                'max_drawdown': fund.get('max_drawdown', 0),
                'invest_type': labels[0] if labels else '均衡',
                'invest_reason': reasons[0] if reasons else '综合表现稳定'
            }
            
            if 'TOP10' in labels: categorized['top10'].append(fund_item)
            if '高Alpha' in labels: categorized['high_alpha'].append(fund_item)
            if '长线' in labels: categorized['long_term'].append(fund_item)
            if '短线' in labels: categorized['short_term'].append(fund_item)
            if '防守' in labels: categorized['low_beta'].append(fund_item)
        
        # 生成 AI 摘要 (优先尝试宏观预测，增加超时保护)
        try:
            import asyncio
            from .ai_service import get_ai_service
            ai_service = get_ai_service()
            
            if ai_service:
                # 获取新闻用于增强分析
                from .news_service import get_news_service
                news_service = get_news_service()
                news_list = []
                if news_service:
                    news_list = await news_service.get_market_news(limit=60)

                # 使用新的 HTML 结构化摘要生成器 (含新闻舆情)
                summary_result = await ai_service.generate_recommendation_summary(funds, theme, news_list=news_list)
                ai_summary = summary_result.get('content', '')
            else:
                ai_summary = self._generate_summary(funds, theme)
        except Exception as e:
            logger.warning(f"生成 AI 摘要失败: {e}")
            ai_summary = self._generate_summary(funds, theme)
            
        # 计算核心统计数据供前端 UI 使用
        total_funds = len(funds)
        avg_score = sum(f.get('score', 0) for f in funds) / total_funds if total_funds else 0
        high_alpha_count = sum(1 for f in funds if f.get('alpha', 0) > 10)
        low_risk_count = sum(1 for f in funds if f.get('max_drawdown', 0) < 15)
        
        return {
            'status': 'success',
            'snapshot_date': snapshot['snapshot_date'],
            'snapshot_id': snapshot['id'],
            'total_funds': snapshot.get('total_funds', 0),
            'qualified_funds': snapshot.get('qualified_funds', 0),
            'benchmark': snapshot.get('benchmark', '000300.SH'),
            'recommendations': categorized,
            'ai_summary': ai_summary,
            'stats': {
                'avg_score': round(avg_score, 1),
                'high_alpha_count': high_alpha_count,
                'low_risk_count': low_risk_count
            }
        }
    
    def _get_grade(self, score: float) -> str:
        """根据分数获取等级"""
        if score >= 80:
            return 'A+'
        elif score >= 70:
            return 'A'
        elif score >= 60:
            return 'B+'
        elif score >= 50:
            return 'B'
        elif score >= 40:
            return 'C'
        else:
            return 'D'
    
    def _generate_summary(self, funds: List[Dict], theme: str = None) -> str:
        """生成AI摘要"""
        if not funds:
            return '暂无推荐数据'
        
        total = len(funds)
        avg_score = sum(f.get('score', 0) for f in funds) / total if total > 0 else 0
        high_alpha_count = sum(1 for f in funds if f.get('alpha', 0) > 10)
        low_risk_count = sum(1 for f in funds if f.get('max_drawdown', 100) < 15)
        
        theme_text = f'**{theme}主题**' if theme else '**全市场**'
        
        summary = f'''基于最新数据分析，{theme_text}共筛选出 **{total}** 只优质基金：

📊 **整体表现**
- 平均评分：**{avg_score:.1f}分**
- 高Alpha基金：**{high_alpha_count}只** (Alpha>10%)
- 低风险基金：**{low_risk_count}只** (最大回撤<15%)

💡 **投资建议**
- TOP10：综合评分最高的基金，适合作为核心持仓
- 高Alpha：超额收益突出，适合进攻型投资者
- 长线持有：夏普比率高且回撤控制好，适合长期配置
- 防守型：波动和回撤都较低，适合稳健型投资者
'''
        
        return summary
    
    def analyze_single_fund(self, code: str) -> Dict[str, Any]:
        """分析单只基金"""
        code = str(code).zfill(6)
        
        # 优先从数据库获取
        snapshot = self.db.get_latest_snapshot()
        if snapshot:
            metrics = self.db.get_fund_metrics(snapshot['id'], code)
            if metrics:
                fund_info = self.db.get_fund(code)
                
                # 获取净值历史用于图表
                chart_data = self._get_chart_data(code)
                
                # 扁平化返回，与前端期望一致
                result = {
                    'status': 'success',
                    'code': code,
                    'name': fund_info.get('name', '') if fund_info else metrics.get('name', ''),
                    'snapshot_date': snapshot['snapshot_date'],
                    'from_cache': True,
                    'chart_data': chart_data,
                    'metrics': {
                        **metrics,
                        'nav': metrics.get('latest_nav'),
                        'change_percent': metrics.get('return_1d'),
                        'latest_date': metrics.get('nav_date', ''),
                        'benchmark_symbol': snapshot.get('benchmark', '000300.SH').replace('.SH', '').replace('.SZ', '')
                    }
                }
                return result
        
        # 实时计算（基金不在数据库中）
        try:
            logger.info(f"基金 {code} 不在快照中，尝试在线获取数据...")
            
            # 获取基金净值数据
            nav_data = self.fetcher.get_fund_nav(code)
            if nav_data is None or len(nav_data) < 20:
                return {
                    'status': 'error',
                    'error': f'基金 {code} 净值数据不足或获取失败，请确认代码正确'
                }
            
            # 尝试在线获取基金基本信息
            fund_name = ''
            fund_type = ''
            themes = []
            
            try:
                import akshare as ak
                fund_info_df = ak.fund_name_em()
                fund_row = fund_info_df[fund_info_df['基金代码'] == code]
                if not fund_row.empty:
                    fund_name = fund_row.iloc[0]['基金简称']
                    fund_type = fund_row.iloc[0]['基金类型']
                    themes = self.fetcher.identify_themes(fund_name)
                    logger.info(f"在线获取基金信息成功: {fund_name} ({fund_type})")
            except Exception as e:
                logger.warning(f"在线获取基金信息失败: {e}")
            
            # 获取基准数据
            if self._benchmark_data is None:
                self._benchmark_data = self.fetcher.get_benchmark_data()
            
            metrics = self._calculate_fund_metrics(code, nav_data)
            if metrics:
                metrics['name'] = fund_name
                metrics['fund_type'] = fund_type
                metrics['themes'] = themes
                metrics['score'] = self._calculate_score(metrics)
                metrics['grade'] = self._get_grade(metrics['score'])
                
                # 准备图表数据（从nav_data中提取）
                chart_data = self._prepare_chart_data_from_df(nav_data)
                
                # 扁平化返回
                result = {
                    'status': 'success',
                    'code': code,
                    'name': fund_name or f'基金{code}',
                    'from_cache': False,
                    'realtime': True,
                    'chart_data': chart_data,
                    'metrics': {
                        **metrics,
                        'nav': metrics.get('latest_nav'),
                        'change_percent': metrics.get('return_1d'),
                        'latest_date': metrics.get('nav_date', ''),
                        'benchmark_symbol': self.settings.DEFAULT_BENCHMARK.replace('.SH', '').replace('.SZ', '')
                    }
                }
                return result
            
            return {
                'status': 'error',
                'error': '指标计算失败'
            }
            
        except Exception as e:
            logger.error(f"分析基金 {code} 失败: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_chart_data(self, code: str, days: int = 60) -> List[Dict]:
        """从数据库获取净值历史用于图表"""
        try:
            # 先从本地缓存获取
            nav_history = self.db.get_nav_history(code, days)
            
            if nav_history and len(nav_history) >= days * 0.7:
                # 数据足够，直接返回（需要反转为正序）
                return [{
                    'date': h['date'][-5:],  # MM-DD 格式
                    'nav': h['nav']
                } for h in reversed(nav_history) if h.get('nav')]
            
            # 数据不足，尝试在线获取
            nav_df = self.fetcher.get_fund_nav(code)
            if nav_df is not None and len(nav_df) > 0:
                # 保存到缓存
                nav_data = []
                for _, row in nav_df.iterrows():
                    nav_data.append({
                        'date': row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date']),
                        'nav': float(row['nav']) if row['nav'] else None
                    })
                self.db.save_nav_history(code, nav_data)
                
                # 返回最近N天
                recent = nav_data[-days:] if len(nav_data) > days else nav_data
                return [{'date': d['date'][-5:], 'nav': d['nav']} for d in recent if d.get('nav')]
            
            return []
        except Exception as e:
            logger.warning(f"获取图表数据失败: {e}")
            return []
    
    def _prepare_chart_data_from_df(self, nav_df, days: int = 60) -> List[Dict]:
        """从 DataFrame 中准备图表数据"""
        try:
            if nav_df is None or len(nav_df) == 0:
                return []
            
            chart_df = nav_df.tail(days)[['date', 'nav']].copy()
            result = []
            for _, row in chart_df.iterrows():
                date_str = row['date'].strftime('%m-%d') if hasattr(row['date'], 'strftime') else str(row['date'])[-5:]
                if row['nav']:
                    result.append({'date': date_str, 'nav': float(row['nav'])})
            return result
        except Exception as e:
            logger.warning(f"准备图表数据失败: {e}")
            return []

    def get_ranking_list(self, sort_by: str = 'score', limit: int = 20, theme: str = None) -> Dict[str, Any]:
        """获取多维排行列表"""
        snapshot = self.db.get_latest_snapshot()
        if not snapshot:
            return {'status': 'error', 'message': '请更新快照数据'}
            
        funds = self.db.get_ranking(
            snapshot_id=snapshot['id'],
            sort_by=sort_by,
            limit=limit,
            theme=theme
        )
        
        # 补充额外信息，对接前端字段
        for f in funds:
            f['grade'] = self._get_grade(f.get('score', 0))
            # 兼容前端字段名
            f['nav'] = f.get('latest_nav')
            f['change_percent'] = f.get('return_1d') or 0.0
            
        return {
            'status': 'success',
            'data': funds,
            'count': len(funds),
            'snapshot_date': snapshot['snapshot_date'],
            'sort_by': sort_by
        }

    def calculate_holding_similarity(self, code1: str, code2: str) -> Dict[str, Any]:
        """计算两只基金的持仓相似度"""
        try:
            h1 = self.fetcher.get_fund_holdings(code1)
            h2 = self.fetcher.get_fund_holdings(code2)
            
            if not h1 or not h2:
                return {'overlap_ratio': 0, 'common_holdings': [], 'status': 'no_data'}
            
            set1 = {item['name'] for item in h1}
            set2 = {item['name'] for item in h2}
            
            common = set1.intersection(set2)
            
            # 计算重合权重 (简化：如果名称相同，取平均权重之和)
            weights1 = {item['name']: item['ratio'] for item in h1}
            weights2 = {item['name']: item['ratio'] for item in h2}
            
            total_overlap = 0
            common_details = []
            for name in common:
                w1 = weights1.get(name, 0)
                w2 = weights2.get(name, 0)
                # 取重合部分的最小值作为重合权重
                overlap_w = min(w1, w2)
                total_overlap += overlap_w
                common_details.append({
                    'name': name,
                    'weight1': w1,
                    'weight2': w2,
                    'overlap': overlap_w
                })
            
            return {
                'overlap_ratio': round(total_overlap, 2),
                'common_holdings': sorted(common_details, key=lambda x: x['overlap'], reverse=True),
                'status': 'success'
            }
        except Exception as e:
            logger.error(f"计算持仓相似度失败: {e}")
            return {'overlap_ratio': 0, 'common_holdings': [], 'status': 'error'}

    def get_comparison_matrix(self, codes: List[str]) -> Dict[str, Any]:
        """获取多只基金的对比矩阵"""
        results = []
        snapshot = self.db.get_latest_snapshot()
        
        for code in codes:
            # 1. 获取指标
            fund_data = {}
            if snapshot:
                metrics = self.db.get_fund_metrics(snapshot['id'], code)
                if metrics:
                    fund_data = metrics
            
            if not fund_data:
                # 尝试补充基本信息
                fund_info = self.db.get_fund(code)
                if fund_info:
                    fund_data = {'code': code, 'name': fund_info['name']}
                else:
                    fund_data = {'code': code, 'name': code}
            
            # 2. 获取持仓
            fund_data['holdings'] = self.fetcher.get_fund_holdings(code)
            
            # 3. 获取经理
            fund_data['manager_info'] = self.fetcher.get_fund_manager_info(code)
            
            # 4. 补充评级
            fund_data['grade'] = self._get_grade(fund_data.get('score', 0))
            
            results.append(fund_data)
            
        # 5. 计算相似度 (如果是两只基金对比)
        similarity = None
        if len(codes) == 2:
            similarity = self.calculate_holding_similarity(codes[0], codes[1])
            
        return {
            'status': 'success',
            'data': results,
            'similarity': similarity
        }

    def query_funds_advanced(self, filters: Dict[str, Any], limit: int = 10) -> Dict[str, Any]:
        """
        根据复杂条件筛选基金 (Phase 4 核心)
        支持: min_alpha, max_drawdown, min_sharpe, themes, fund_type 等
        """
        try:
            snapshot = self.db.get_latest_snapshot()
            if not snapshot:
                return {'status': 'error', 'message': 'No snapshot found'}
            
            # 1. 从数据库读取该快照下的所有入选基金
            all_funds = self.db.get_snapshot_metrics(snapshot['id'])
            
            # 2. 内存过滤 (灵活性更高)
            qualified = []
            for f in all_funds:
                # 基础信息解析
                f['themes'] = json.loads(f.get('themes_json', '[]')) if 'themes_json' in f else f.get('themes', [])
                
                # 开始匹配
                match = True
                
                # 指标匹配
                if 'min_alpha' in filters and f.get('alpha', 0) < filters['min_alpha']: match = False
                if 'max_drawdown' in filters and f.get('max_drawdown', 0) > filters['max_drawdown']: match = False
                if 'min_sharpe' in filters and f.get('sharpe', 0) < filters['min_sharpe']: match = False
                if 'min_score' in filters and f.get('score', 0) < filters['min_score']: match = False
                
                # 标签/主题匹配
                if 'themes' in filters and filters['themes']:
                    # 只要包含任意一个请求的主题即可
                    if not any(theme in f['themes'] for theme in filters['themes']):
                        match = False
                
                # 类型匹配
                if 'fund_type' in filters and filters['fund_type'] != 'all':
                    if filters['fund_type'] not in f.get('fund_type', ''):
                        match = False
                        
                if match:
                    # 补充等级
                    f['grade'] = self._get_grade(f.get('score', 0))
                    qualified.append(f)
            
            # 3. 排序
            sort_by = filters.get('sort_by', 'score')
            # 确保字段存在
            if qualified and sort_by in qualified[0]:
                reverse = True
                if sort_by == 'max_drawdown': reverse = False # 回撤越小越好
                qualified.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
            
            return {
                'status': 'success',
                'data': qualified[:limit],
                'count': len(qualified),
                'total_in_snapshot': len(all_funds)
            }
        except Exception as e:
            logger.error(f"高级筛选失败: {e}")
            return {'status': 'error', 'message': str(e)}


# 全局单例
_snapshot_service: Optional[SnapshotService] = None

def get_snapshot_service() -> SnapshotService:
    global _snapshot_service
    if _snapshot_service is None:
        _snapshot_service = SnapshotService()
    return _snapshot_service
