
export default {
    name: 'MonthlyReportView',
    props: ['reportData', 'loading'],
    emits: ['handle-export-image'],
    template: `
        <div class="glass-card monthly-report" id="monthly-report-card">
            <div class="section-header">
                <h2 class="section-title">📈 月度体检报告</h2>
                <div style="display: flex; gap: 0.5rem;">
                    <button class="pro-btn" style="padding: 0.4rem 0.8rem; font-size: 0.75rem; background: rgba(255,255,255,0.05);"
                        @click="$emit('handle-export-image', 'monthly-report-card')">📸 分享</button>
                </div>
            </div>

            <div v-if="loading" style="padding: 3rem; text-align: center;">
                <div class="spinner-pro"></div>
                <p style="color: var(--text-muted); margin-top: 0.5rem;">生成报告中...</p>
            </div>

            <div v-else-if="reportData" class="report-content">
                <!-- Month Badge -->
                <div class="report-month-badge">{{ reportData.month }} 月报</div>

                <!-- Portfolio Overview -->
                <div class="report-section">
                    <h3 class="report-section-title">💰 资产概况</h3>
                    <div class="report-grid">
                        <div class="report-metric-card">
                            <div class="report-metric-label">总资产</div>
                            <div class="report-metric-value">¥{{ formatN(reportData.portfolio.total_value) }}</div>
                        </div>
                        <div class="report-metric-card">
                            <div class="report-metric-label">本月收益率</div>
                            <div class="report-metric-value" :class="reportData.portfolio.monthly_return >= 0 ? 'font-up' : 'font-down'">
                                {{ reportData.portfolio.monthly_return >= 0 ? '+' : '' }}{{ reportData.portfolio.monthly_return }}%
                            </div>
                        </div>
                        <div class="report-metric-card">
                            <div class="report-metric-label">持仓数量</div>
                            <div class="report-metric-value">{{ reportData.portfolio.position_count }} 只</div>
                        </div>
                        <div class="report-metric-card">
                            <div class="report-metric-label">定投次数</div>
                            <div class="report-metric-value">{{ reportData.dca.execution_count }} 次</div>
                        </div>
                    </div>
                </div>

                <!-- DCA Summary -->
                <div class="report-section" v-if="reportData.dca.execution_count > 0">
                    <h3 class="report-section-title">⏳ 定投执行</h3>
                    <div class="report-highlight">
                        <span style="font-size: 1.5rem;">👏</span>
                        <div>
                            <div style="font-weight: 700;">本月执行了 {{ reportData.dca.execution_count }} 次定投</div>
                            <div style="font-size: 0.8rem; color: var(--text-muted);">累计投入 ¥{{ formatN(reportData.dca.total_invested) }}</div>
                        </div>
                    </div>
                </div>

                <!-- Market Temperature -->
                <div class="report-section" v-if="reportData.market_temperature">
                    <h3 class="report-section-title">🌡️ 市场温度</h3>
                    <div class="report-temp-bar">
                        <div class="temp-fill" :style="{width: reportData.market_temperature.temperature + '%', background: reportData.market_temperature.color}"></div>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;">
                        <span>冷 ❄️</span>
                        <span :style="{color: reportData.market_temperature.color, fontWeight: 700}">{{ reportData.market_temperature.label }} ({{ reportData.market_temperature.temperature }}°)</span>
                        <span>热 🔥</span>
                    </div>
                </div>

                <!-- AI Summary -->
                <div class="report-section">
                    <h3 class="report-section-title">🤖 AI 总结</h3>
                    <div class="report-ai-summary">{{ reportData.ai_summary }}</div>
                </div>
            </div>

            <div v-else style="padding: 2rem; text-align: center; color: var(--text-muted);">
                暂无报告数据，请先添加持仓记录
            </div>
        </div>
    `,
    methods: {
        formatN(n) {
            if (!n) return '0.00';
            return Number(n).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }
    },
    style: `
        .report-content { margin-top: 1.5rem; }
        .report-month-badge {
            text-align: center; font-size: 1rem; font-weight: 800; color: var(--primary);
            padding: 0.5rem; background: rgba(99,102,241,0.1); border-radius: 8px; margin-bottom: 1.5rem;
        }
        .report-section { margin-bottom: 1.5rem; }
        .report-section-title { font-size: 0.95rem; font-weight: 700; margin-bottom: 1rem; color: white; }
        .report-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
        .report-metric-card {
            padding: 1rem; border-radius: 12px; background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.05);
        }
        .report-metric-label { font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.5rem; }
        .report-metric-value { font-size: 1.25rem; font-weight: 800; }
        .report-highlight {
            display: flex; align-items: center; gap: 1rem; padding: 1rem;
            background: rgba(34,197,94,0.08); border-radius: 12px; border: 1px solid rgba(34,197,94,0.15);
        }
        .report-temp-bar { height: 8px; background: rgba(255,255,255,0.05); border-radius: 4px; overflow: hidden; }
        .temp-fill { height: 100%; border-radius: 4px; transition: width 0.8s ease; }
        .report-ai-summary {
            padding: 1.25rem; border-radius: 12px; background: rgba(99,102,241,0.06);
            border: 1px solid rgba(99,102,241,0.12); font-size: 0.9rem; line-height: 1.8;
            color: rgba(255,255,255,0.85);
        }
    `
};
