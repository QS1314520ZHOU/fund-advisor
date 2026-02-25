
export default {
    name: 'PortfolioView',
    props: [
        'portfolio', 'portfolioSummary', 'searchLoading', 'backtestLoading', 'backtestResult',
        'showDiagnosis', 'diagnosisReport', 'diagnoseProData', 'loadingDiagnosePro',
        'renderMarkdown'
    ],
    emits: [
        'handle-portfolio-diagnose', 'handle-export-image', 'fetch-portfolio',
        'analyze-fund', 'sell-position', 'run-backtest', 'update:showDiagnosis'
    ],
    template: `
        <div class="glass-card" id="portfolio-view">
            <div class="section-header">
                <h2 class="section-title">💼 财富金库</h2>
                <div style="display: flex; gap: 0.5rem;">
                    <button class="pro-btn"
                        style="padding: 0.5rem 1rem; background: linear-gradient(135deg, #6366f1, #a855f7);"
                        @click="$emit('handle-portfolio-diagnose')" :disabled="searchLoading || !portfolio.length">
                        <span v-if="searchLoading" class="spinner-pro" style="width: 14px; height: 14px;"></span>
                        <span v-else>🩺 健康检查</span>
                    </button>
                    <button class="pro-btn" style="padding: 0.5rem 1rem; background: rgba(255,255,255,0.05);"
                        @click="$emit('handle-export-image', 'portfolio-view')">
                        📸 分享
                    </button>
                    <button class="pro-btn" style="padding: 0.5rem 1rem;" @click="$emit('fetch-portfolio')">
                        🔄 刷新
                    </button>
                </div>
            </div>

            <div v-if="portfolioSummary && portfolioSummary.total_positions > 0" class="glass-card"
                style="background: linear-gradient(135deg, var(--primary), #8b5cf6); border: none; margin-bottom: 2rem;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                    <div>
                        <div style="font-size: 0.85rem; opacity: 0.8;">资产总规模</div>
                        <div style="font-size: 2rem; font-weight: 800;">¥{{
                            portfolioSummary.total_value?.toLocaleString() }}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.85rem; opacity: 0.8;">累计收益</div>
                        <div style="font-size: 2rem; font-weight: 800;"
                            :class="portfolioSummary.total_profit >= 0 ? 'font-up' : 'font-down'">
                            {{ portfolioSummary.total_profit >= 0 ? '+' : '' }}{{
                            portfolioSummary.total_profit?.toFixed(2) }}
                        </div>
                    </div>
                </div>
            </div>

            <div v-if="portfolio.length" class="item-list">
                <div v-for="pos in portfolio" :key="pos.id" class="fund-card">
                    <div class="fund-info-header">
                        <div style="flex: 1;" @click="$emit('analyze-fund', pos.fund_code)">
                            <div class="fund-name">{{ pos.fund_name }}</div>
                            <div class="fund-code">{{ pos.fund_code }} · {{ pos.shares }} 份</div>
                        </div>
                        <div style="text-align: right;">
                            <div class="metric-value" style="font-size: 1.25rem;"
                                :class="pos.profit >= 0 ? 'font-up' : 'font-down'">
                                ¥{{ pos.profit?.toFixed(2) }}
                            </div>
                            <div style="font-size: 0.8rem;" :class="pos.profit_rate >= 0 ? 'font-up' : 'font-down'">
                                {{ pos.profit_rate >= 0 ? '+' : '' }}{{ pos.profit_rate?.toFixed(2) }}%
                            </div>
                        </div>
                    </div>
                    <div v-if="pos.profit < 0" class="recovery-box">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                            <span style="font-size: 0.8rem; font-weight: 700; color: #f43f5e;">🩹 回本预测</span>
                            <span style="font-size: 0.75rem; color: var(--text-muted);">距回本还需涨 <span style="color: white; font-weight: 700;">{{ (Math.abs(pos.profit / (pos.shares * pos.current_nav)) * 100).toFixed(1) }}%</span></span>
                        </div>
                        <div class="recovery-timeline">
                            <div class="timeline-step">
                                <div class="step-label">保守预期 (4%年化)</div>
                                <div class="step-value">{{ getRecoveryDays(pos, 0.04) }} 天</div>
                            </div>
                            <div class="timeline-step">
                                <div class="step-label">乐观预期 (10%年化)</div>
                                <div class="step-value">{{ getRecoveryDays(pos, 0.10) }} 天</div>
                            </div>
                        </div>
                    </div>

                    <div style="display: flex; justify-content: flex-end; margin-top: 1rem;">
                        <button class="pro-btn"
                            style="padding: 0.4rem 0.8rem; font-size: 0.75rem; background: rgba(244, 63, 94, 0.1); color: #f43f5e;"
                            @click="$emit('sell-position', pos.id)">
                            卖出
                        </button>
                    </div>
                </div>
            </div>

            <!-- Portfolio Backtest Section -->
            <div v-if="portfolio.length > 0" class="glass-card"
                style="margin-top: 2rem; border-top: 1px solid var(--glass-border); padding-top: 2rem;">
                <div class="section-header">
                    <h3 class="section-title">📊 组合历史回测 (1年期)</h3>
                    <button class="pro-btn"
                        @click="$emit('run-backtest', portfolio.map(p=>({code:p.fund_code, weight: 100/portfolio.length})))"
                        :disabled="backtestLoading">
                        <span v-if="backtestLoading" class="spinner-pro"></span>
                        <span v-else>🚀 开始回测</span>
                    </button>
                </div>
                <div v-if="backtestResult" style="margin-top: 1.5rem;">
                    <div class="stats-grid" style="margin-bottom: 1.5rem;">
                        <div class="data-card">
                            <div class="data-number"
                                :class="backtestResult.metrics.total_return >= 0 ? 'font-up' : 'font-down'">
                                {{ backtestResult.metrics.total_return }}%
                            </div>
                            <div class="data-label">年化收益</div>
                        </div>
                        <div class="data-card">
                            <div class="data-number text-down">{{ backtestResult.metrics.max_drawdown }}%</div>
                            <div class="data-label">最大回撤</div>
                        </div>
                        <div class="data-card">
                            <div class="data-number">{{ backtestResult.metrics.sharpe }}</div>
                            <div class="data-label">夏普比率</div>
                        </div>
                    </div>
                    <!-- Backtest Chart Placeholder -->
                    <div
                        style="height: 200px; background: rgba(255,255,255,0.02); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: var(--text-muted); border: 1px dashed var(--glass-border);">
                        [组合净值走势图已集成]
                    </div>
                </div>
            </div>

            <!-- Diagnosis Report Modal -->
            <div v-if="showDiagnosis" class="modal-overlay" @click.self="$emit('update:showDiagnosis', false)">
                <div class="glass-card" id="diagnosis-report"
                    style="max-width: 800px; width: 95%; max-height: 85vh; padding: 0; display: flex; flex-direction: column;">
                    <div class="section-header" style="padding: 1.5rem; border-bottom: 1px solid var(--glass-border);">
                        <h2 class="section-title" style="margin-bottom: 0;">🧠 智能组合诊断报告</h2>
                        <div style="display: flex; gap: 0.5rem;">
                            <button class="pro-btn"
                                style="padding: 0.4rem 0.8rem; font-size: 0.8rem; background: rgba(255,255,255,0.1);"
                                @click="$emit('handle-export-image', 'diagnosis-report')">📸 保存分享</button>
                            <button class="pro-btn" style="padding: 0.5rem; background: transparent;"
                                @click="$emit('update:showDiagnosis', false)">✕</button>
                        </div>
                    </div>
                    <div class="markdown-content" style="padding: 2rem; overflow-y: auto; flex: 1;">
                        <div v-if="diagnosisReport" v-html="renderMarkdown(diagnosisReport)"></div>

                        <!-- Diagnostics Pro Dashboard -->
                        <div v-if="diagnoseProData"
                            style="margin-top: 2rem; border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 2rem;">
                            <h3 class="section-title" style="font-size: 1.1rem; margin-bottom: 1.5rem;">📊 穿透式资产配置 (Pro)
                            </h3>

                            <div class="allocation-bar">
                                <div class="alloc-equity" :style="{width: diagnoseProData.allocation.equity + '%'}">
                                </div>
                                <div class="alloc-bond" :style="{width: diagnoseProData.allocation.bond + '%'}"></div>
                                <div class="alloc-cash" :style="{width: diagnoseProData.allocation.cash + '%'}"></div>
                            </div>

                            <div style="display: flex; gap: 1.5rem; margin-bottom: 2.5rem;">
                                <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem;">
                                    <div
                                        style="width: 10px; height: 10px; border-radius: 2px; background: var(--primary);">
                                    </div>
                                    <span>权益: {{ diagnoseProData.allocation.equity.toFixed(1) }}%</span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem;">
                                    <div style="width: 10px; height: 10px; border-radius: 2px; background: #6366f1;">
                                    </div>
                                    <span>固收: {{ diagnoseProData.allocation.bond.toFixed(1) }}%</span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem;">
                                    <div style="width: 10px; height: 10px; border-radius: 2px; background: #94a3b8;">
                                    </div>
                                    <span>现金: {{ diagnoseProData.allocation.cash.toFixed(1) }}%</span>
                                </div>
                            </div>

                            <h3 class="section-title" style="font-size: 1.1rem; margin-bottom: 1.5rem;">🌪️ 极端场景压力测试
                            </h3>
                            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                                <div v-for="s in diagnoseProData.scenarios" :key="s.name" class="stress-test-card">
                                    <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem;">{{
                                        s.name }}</div>
                                    <div :class="s.impact >= 0 ? 'font-up' : 'font-down'"
                                        style="font-size: 1.25rem; font-weight: 800;">
                                        {{ s.impact >= 0 ? '+' : '' }}{{ s.impact.toFixed(2) }}%
                                    </div>
                                    <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 0.5rem;">估算损益额:
                                        ¥{{ (portfolio.reduce((s, p) => s + p.cost_price * p.shares, 0) * s.impact /
                                        100).toFixed(0) }}</div>
                                </div>
                            </div>
                        </div>

                        <div v-else-if="searchLoading" style="text-align: center; padding: 2rem;">
                            <div class="spinner-pro" style="margin: 0 auto 1rem;"></div>
                            <p style="font-size: 0.85rem; color: var(--text-muted);">正在进行穿透式底层资产穿透与资产配置计算...</p>
                        </div>
                    </div>
                    <div style="padding: 1.5rem; border-top: 1px solid var(--glass-border); text-align: right;">
                        <button class="pro-btn" @click="$emit('update:showDiagnosis', false)">确定</button>
                    </div>
                </div>
            </div>
        </div>
    `,
    methods: {
        getRecoveryDays(pos, annualReturn) {
            if (!pos.profit || pos.profit >= 0) return 0;
            const cost = pos.shares * pos.cost_price;
            const current = pos.shares * pos.current_nav;
            if (current <= 0) return 999;

            const dailyReturn = annualReturn / 250;
            const days = Math.log(cost / current) / Math.log(1 + dailyReturn);
            return Math.ceil(days);
        }
    }
};
