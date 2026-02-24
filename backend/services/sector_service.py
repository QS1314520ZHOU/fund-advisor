# backend/services/sector_service.py
"""
板块服务 - 板块数据聚合和预测
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import statistics

from ..database import get_db
from .ai_service import get_ai_service

logger = logging.getLogger(__name__)

# 板块服务类
class SectorService:
    """板块服务类"""
    
    # 主题图标映射
    THEME_ICONS = {
        '大消费': '🛒', '白酒': '🍷', '食品饮料': '🍔', '家电': '📺', '美妆': '💄', '旅游酒店': '🏨', '农业养殖': '🐷',
        '科技TMT': '💻', '半导体芯片': '🔌', '计算机': '💾', '电子': '📱', '通信': '📡', '传媒游戏': '🎮',
        '新能源': '⚡', '光伏': '☀️', '新能源车': '🚗', '风电': '🌬️', '储能': '🔋',
        '医药医疗': '🏥', '创新药': '🧪', '医疗器械': '🩺', '医疗服务': '👨‍⚕️', '中药': '🌿', '生物疫苗': '💉',
        '金融': '🏦', '银行': '🏧', '券商': '📈', '保险': '🛡️', '房地产': '🏠',
        '周期': '🔩', '煤炭': '🌑', '钢铁': '🏗️', '有色金属': '🔶', '化工': '🧪',
        '高端制造': '⚙️', '军工': '🚀', '航空航天': '🛰️', '国防军工': '🛡️', '航天军工': '🛰️', '机器人': '🤖',
        '红利': '💰', '人工智能': '🧠', 'AI': '🤖', '算力': '🏢', 'ESG': '🌱', '中特估': '🏛️', '出海': '🌐',
        '权益类': '📈', '固收类': '💵', '商品类': '🏆', 'REITs': '🏢'
    }
    
    def __init__(self):
        self.db = get_db()
        self.ai_service = get_ai_service()
    
    def get_available_sectors(self) -> List[Dict]:
        """获取可用的板块列表（动态从数据库获取）"""
        try:
            # 从数据库获取所有唯一主题
            themes = self.db.get_all_themes()
            
            if not themes:
                # 如果没有主题数据，返回默认列表
                return self._get_default_sectors()
            
            sectors = []
            for theme_info in themes:
                theme_name = theme_info['name']
                count = theme_info['count']
                
                sectors.append({
                    'id': theme_name,
                    'name': theme_name,
                    'fund_count': count,
                    'icon': self._get_sector_icon(theme_name)
                })
            
            return sectors
        except Exception as e:
            logger.error(f"获取板块列表失败: {e}")
            return self._get_default_sectors()
    
    def _get_default_sectors(self) -> List[Dict]:
        """返回默认板块列表"""
        default_themes = ['大消费', '科技TMT', '新能源', '医药医疗', '金融', '高端制造', '红利', '人工智能']
        return [
            {'id': t, 'name': t, 'fund_count': 0, 'icon': self._get_sector_icon(t)}
            for t in default_themes
        ]
    
    def _get_sector_icon(self, sector: str) -> str:
        """获取板块图标"""
        # 先精确匹配
        if sector in self.THEME_ICONS:
            return self.THEME_ICONS[sector]
        
        # 再模糊匹配
        for key, icon in self.THEME_ICONS.items():
            if key in sector or sector in key:
                return icon
        
        return '📊'  # 默认图标
    
    def get_sector_metrics(self, sector: str) -> Dict:
        """
        获取板块的聚合指标
        
        Args:
            sector: 板块名称
            
        Returns:
            包含板块指标的字典
        """
        try:
            snapshot = self.db.get_latest_snapshot()
            if not snapshot:
                return {
                    'success': False,
                    'error': '暂无快照数据'
                }
            
            # 获取板块内的所有基金
            funds = self._get_sector_funds(snapshot['id'], sector)
            
            # 如果本地没找到基金，尝试在线寻找
            if not funds:
                logger.info(f"板块 {sector} 在本地快照中无数据，尝试在线搜索相关基金...")
                try:
                    from .data_fetcher import get_data_fetcher
                    from .snapshot import get_snapshot_service
                    from concurrent.futures import ThreadPoolExecutor, as_completed
                    
                    fetcher = get_data_fetcher()
                    snapshot_service = get_snapshot_service()
                    
                    # 1. 联网搜索与该板块名称相关的基金
                    import akshare as ak
                    all_funds_df = ak.fund_name_em()
                    # 匹配名称包含板块名 (akshare 返回的列名是 '基金简称')
                    mask = all_funds_df['基金简称'].str.contains(sector, na=False)
                    online_candidates = all_funds_df[mask].head(10)
                    
                    # 定义单个基金分析函数
                    def analyze_fund_task(row_data):
                        code = str(row_data['基金代码']).zfill(6)
                        name = row_data['基金简称']
                        try:
                            analysis = snapshot_service.analyze_single_fund(code)
                            if analysis.get('status') == 'success' and 'metrics' in analysis:
                                fund_data = analysis['metrics']
                                fund_data['code'] = code
                                fund_data['name'] = analysis.get('name', name)
                                return fund_data
                        except Exception as e:
                            logger.warning(f"分析基金 {code} 失败: {e}")
                        return None
                    
                    # 使用线程池并行分析基金（最多5个并行）
                    realtime_funds = []
                    candidates_list = [row for _, row in online_candidates.iterrows()]
                    
                    with ThreadPoolExecutor(max_workers=5) as executor:
                        future_to_code = {
                            executor.submit(analyze_fund_task, row): str(row['基金代码']).zfill(6) 
                            for row in candidates_list
                        }
                        
                        for future in as_completed(future_to_code):
                            code = future_to_code[future]
                            try:
                                result = future.result(timeout=30)
                                if result:
                                    realtime_funds.append(result)
                            except Exception as e:
                                logger.warning(f"并行分析基金 {code} 超时或失败: {e}")
                    
                    if realtime_funds:
                        funds = realtime_funds
                        logger.info(f"在线发现 {len(funds)} 只相关基金用于板块 {sector} 分析")
                except Exception as online_err:
                    logger.warning(f"在线获取板块基金失败: {online_err}")

            if not funds:
                return {
                    'success': False,
                    'error': f'板块 {sector} 暂无符合条件的基金，且在线检索未发现相关产品'
                }
            
            # 聚合计算板块指标
            metrics = self._aggregate_metrics(funds)
            
            return {
                'success': True,
                'sector': sector,
                'fund_count': len(funds),
                'snapshot_date': snapshot.get('snapshot_date'),
                'metrics': metrics,
                'top_funds': funds[:5]  # 只返回前5只基金
            }
            
        except Exception as e:
            logger.error(f"获取板块指标失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_sector_funds(self, snapshot_id: int, sector: str) -> List[Dict]:
        """获取板块内的基金列表"""
        try:
            # 直接使用数据库方法按主题获取基金
            return self.db.get_funds_by_theme(snapshot_id, sector, limit=100)
        except Exception as e:
            logger.error(f"获取板块基金列表失败: {e}")
            return []
    
    def _aggregate_metrics(self, funds: List[Dict]) -> Dict:
        """聚合计算板块指标"""
        if not funds:
            return {}
        
        # 提取各项指标
        alphas = [f.get('alpha', 0) for f in funds if f.get('alpha') is not None]
        betas = [f.get('beta', 1) for f in funds if f.get('beta') is not None]
        sharpes = [f.get('sharpe', 0) for f in funds if f.get('sharpe') is not None]
        returns_1y = [f.get('return_1y', 0) for f in funds if f.get('return_1y') is not None]
        returns_1m = [f.get('return_1m', 0) for f in funds if f.get('return_1m') is not None]
        returns_1w = [f.get('return_1w', 0) for f in funds if f.get('return_1w') is not None]
        drawdowns = [f.get('max_drawdown', 0) for f in funds if f.get('max_drawdown') is not None]
        
        def safe_mean(values):
            return round(statistics.mean(values), 2) if values else 0
        
        def safe_median(values):
            return round(statistics.median(values), 2) if values else 0
        
        return {
            'avg_alpha': safe_mean(alphas),
            'median_alpha': safe_median(alphas),
            'avg_beta': safe_mean(betas),
            'avg_sharpe': safe_mean(sharpes),
            'avg_return_1y': safe_mean(returns_1y),
            'avg_return_1m': safe_mean(returns_1m),
            'avg_return_1w': safe_mean(returns_1w),
            'avg_drawdown': safe_mean(drawdowns),
            'best_fund_score': funds[0].get('score', 0) if funds else 0,
            'best_fund_name': funds[0].get('name', '') if funds else ''
        }
    
    async def get_sector_sentiment(self, sector: str) -> Dict[str, Any]:
        """根据板块内基金表现判断板块情绪"""
        try:
            snapshot = self.db.get_latest_snapshot()
            if not snapshot: 
                return {"sentiment": "Neutral", "ratio": 0.5}
            
            funds = self.db.get_funds_by_theme(snapshot['id'], sector, limit=50)
            if not funds:
                return {"sentiment": "Neutral", "ratio": 0.5}
            
            # 使用 return_1d 计算涨跌比
            up_count = sum(1 for f in funds if (f.get('return_1d') or 0) > 0)
            ratio = up_count / len(funds)
            
            label = "Neutral"
            if ratio > 0.8: label = "Extreme Positive"
            elif ratio > 0.65: label = "Positive"
            elif ratio < 0.2: label = "Extreme Negative"
            elif ratio < 0.35: label = "Negative"
            
            return {
                "sentiment": label,
                "ratio": round(ratio, 2),
                "up_count": up_count,
                "down_count": len(funds) - up_count
            }
        except Exception as e:
            logger.warning(f"获取板块情绪失败: {e}")
            return {"sentiment": "Neutral", "ratio": 0.5}

    async def predict_sector(self, sector: str, period: str = 'tomorrow') -> Dict:
        """
        预测板块走势
        
        Args:
            sector: 板块名称
            period: 预测周期 ('tomorrow' 或 'week')
            
        Returns:
            包含AI预测结果的字典
        """
        try:
            # 获取板块指标
            metrics_result = self.get_sector_metrics(sector)
            
            if not metrics_result.get('success'):
                return metrics_result
            
            metrics = metrics_result.get('metrics', {})
            fund_count = metrics_result.get('fund_count', 0)
            top_funds = metrics_result.get('top_funds', [])
            
            # 调用AI服务生成预测
            if not self.ai_service:
                return {
                    'success': False,
                    'error': 'AI服务未配置'
                }
            
            prediction = await self._generate_ai_prediction(
                sector=sector,
                metrics=metrics,
                fund_count=fund_count,
                top_funds=top_funds,
                period=period
            )
            
            return {
                'success': True,
                'sector': sector,
                'period': period,
                'period_display': '明天' if period == 'tomorrow' else '本周',
                'fund_count': fund_count,
                'metrics': metrics,
                'prediction': prediction,
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"预测板块失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _generate_ai_prediction(self, sector: str, metrics: Dict, 
                                     fund_count: int, top_funds: List[Dict],
                                     period: str) -> str:
        """生成AI预测"""
        try:
            period_text = "明天" if period == 'tomorrow' else "未来一周"
            
            # 构建提示词
            prompt = f"""你是一位资深的基金投资分析师，请基于以下{sector}板块的数据，预测{period_text}的走势。

## 板块概况
- 板块名称：{sector}
- 入选基金数：{fund_count}只
- 最佳基金：{metrics.get('best_fund_name', '暂无')}（{metrics.get('best_fund_score', 0)}分）

## 板块平均指标（所有入选基金的平均值）
- Alpha（超额收益）：{metrics.get('avg_alpha', 0)}%
- Beta（市场敏感度）：{metrics.get('avg_beta', 1.0)}
- 夏普比率：{metrics.get('avg_sharpe', 0)}
- 近1周收益：{metrics.get('avg_return_1w', 0)}%
- 近1月收益：{metrics.get('avg_return_1m', 0)}%
- 近1年收益：{metrics.get('avg_return_1y', 0)}%
- 平均最大回撤：{metrics.get('avg_drawdown', 0)}%

## 板块龙头基金（前3名）
{self._format_top_funds(top_funds[:3])}

## 预测要求
请从以下几个维度进行分析，并给出{period_text}的预测：

1. **趋势预测**：看涨📈 / 看跌📉 / 震荡📊（选择其一）
2. **置信度**：给出0-100的评分
3. **关键驱动因素**：列出2-3个影响该板块走势的主要因素
4. **风险提示**：列出1-2个需要注意的风险点
5. **投资建议**：给出简明的操作建议

请用简洁清晰的语言回答，使用Markdown格式，多用emoji增强可读性。"""

            # 调用AI生成
            response = await self.ai_service.ask_ai(prompt)
            
            if response.get('success'):
                return response.get('content', '暂无预测')
            else:
                return f"AI预测失败: {response.get('error', '未知错误')}"
                
        except Exception as e:
            logger.error(f"生成AI预测失败: {e}")
            return f"生成预测时出错: {str(e)}"
    
    def _format_top_funds(self, funds: List[Dict]) -> str:
        """格式化头部基金列表"""
        if not funds:
            return "暂无数据"
        
        lines = []
        for i, fund in enumerate(funds, 1):
            lines.append(
                f"{i}. {fund.get('name', '未知')}({fund.get('code', '')}) - "
                f"得分{fund.get('score', 0)}分, "
                f"Alpha {fund.get('alpha', 0)}%, "
                f"近1月 {fund.get('return_1m', 0)}%"
            )
        
        return '\n'.join(lines)


# 单例
_sector_service = None


def get_sector_service() -> Optional[SectorService]:
    """获取板块服务实例"""
    global _sector_service
    if _sector_service is None:
        try:
            _sector_service = SectorService()
        except Exception as e:
            logger.error(f"初始化板块服务失败: {e}")
            return None
    return _sector_service
