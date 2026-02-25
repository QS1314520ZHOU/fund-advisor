# backend/services/health_service.py
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class HealthService:
    """
    基金健康度诊断服务
    基于多维度量化指标，输出红黄绿三色诊断报告
    """
    
    def __init__(self):
        # 延迟导入以避免循环依赖
        pass

    def diagnose_fund(self, code: str, name: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        对单只基金进行健康度诊断
        """
        try:
            indicators = []
            
            # 1. 盈利能力 (Annual Return)
            # metrics['annual_return'] 为百分比 (如 15.32 表示 15.32%)
            annual_ret = metrics.get('annual_return', 0)
            
            ret_status = 'green' if annual_ret > 15 else ('yellow' if annual_ret > 5 else 'red')
            indicators.append({
                'name': '盈利能力',
                'status': ret_status,
                'value': f"{annual_ret:.2f}%",
                'desc': f'历史年化收益率为 {annual_ret:.2f}%'
            })
            
            # 2. 风险控制 (Max Drawdown)
            # metrics['max_drawdown'] 为正数百分比 (如 15.32 表示 15.32% 回撤)
            mdd = abs(metrics.get('max_drawdown', 0))
            
            mdd_status = 'green' if mdd < 15 else ('yellow' if mdd < 25 else 'red')
            indicators.append({
                'name': '回撤控制',
                'status': mdd_status,
                'value': f"{mdd:.2f}%",
                'desc': '最大回撤水平，越小越稳健'
            })
            
            # 3. 效率比率 (Sharpe Ratio)
            # sharpe 是比率数值 (如 1.25)
            sharpe = metrics.get('sharpe', 0)
            sharpe_status = 'green' if sharpe > 1.2 else ('yellow' if sharpe > 0.8 else 'red')
            indicators.append({
                'name': '投资效率',
                'status': sharpe_status,
                'value': f"{sharpe:.2f}",
                'desc': '夏普比率，衡量风险调整后的收益'
            })
            
            # 4. 超额收益 (Alpha)
            # alpha 为百分比 (如 5.4 表示 5.4%)
            alpha = metrics.get('alpha', 0)
            
            alpha_status = 'green' if alpha > 5 else ('yellow' if alpha > 0 else 'red')
            indicators.append({
                'name': '超额能力',
                'status': alpha_status,
                'value': f"{alpha:.2f}%",
                'desc': 'Alpha 超额收益能力'
            })

            # 计算总分 (根据三色统计)
            status_counts = {'green': 0, 'yellow': 0, 'red': 0}
            for ind in indicators:
                status_counts[ind['status']] += 1
            
            final_status = 'green'
            if status_counts['red'] >= 2:
                final_status = 'red'
            elif status_counts['red'] == 1 or status_counts['yellow'] >= 2:
                final_status = 'yellow'
                
            summary = self._generate_summary(final_status, status_counts)
            
            return {
                'code': code,
                'name': name,
                'status': final_status,
                'indicators': indicators,
                'summary': summary
            }
        except Exception as e:
            logger.error(f"Failed to diagnose fund {code}: {e}")
            return {'error': str(e)}

    def _generate_summary(self, status: str, counts: Dict[str, int]) -> str:
        if status == 'green':
            return "基金整体表现非常健康，指标全面占优，适合稳健持有。"
        elif status == 'yellow':
            return "基金部分指标出现波动或弱于同类，建议保持关注，审慎增持。"
        else:
            return "基金风险指标或盈利能力显著恶化，存在较多预警，建议考虑减仓或调仓。"

_health_service = None

def get_health_service() -> HealthService:
    global _health_service
    if _health_service is None:
        _health_service = HealthService()
    return _health_service
