
export default {
    name: 'DashboardView',
    props: ['dashboardData', 'loading'],
    emits: ['switch-mode', 'analyze-fund', 'refresh'],
    template: `
        <div class="dashboard-view">
            <!-- Loading state -->
            <div v-if="loading && !dashboardData" style="padding: 3rem; text-align: center;">
                <div class="spinner-pro"></div>
                <p style="color: var(--text-muted); margin-top: 1rem;">加载中...</p>
            </div>

            <template v-else>
                <!-- Hero Asset Card -->
                <div class="asset-hero glass-card">
                    <div class="asset-hero-top">
                        <div>
                            <div class="asset-label">我的总资产</div>
                            <div class="asset-value">¥{{ formatNum(summary.total_value) }}</div>
                        </div>
                        <div style="text-align: right;">
                            <div class="asset-label">持仓数量</div>
                            <div style="font-size: 1.5rem; font-weight: 800;">{{ summary.position_count || 0 }}</div>
                        </div>
                    </div>
                    <div class="asset-hero-bottom">
                        <div class="asset-metric">
                            <span class="asset-metric-label">累计收益</span>
                            <span :class="summary.total_profit >= 0 ? 'font-up' : 'font-down'" style="font-weight: 700;">
                                {{ summary.total_profit >= 0 ? '+' : '' }}¥{{ formatNum(summary.total_profit) }}
                            </span>
                        </div>
                        <div class="asset-metric">
                            <span class="asset-metric-label">收益率</span>
                            <span :class="summary.profit_rate >= 0 ? 'font-up' : 'font-down'" style="font-weight: 700;">
                                {{ summary.profit_rate >= 0 ? '+' : '' }}{{ summary.profit_rate?.toFixed(2) || '0.00' }}%
                            </span>
                        </div>
                        <div class="asset-metric">
                            <span class="asset-metric-label">今日盈亏</span>
                            <span :class="summary.today_pnl >= 0 ? 'font-up' : 'font-down'" style="font-weight: 700;">
                                {{ summary.today_pnl >= 0 ? '+' : '' }}¥{{ formatNum(summary.today_pnl) }}
                            </span>
                        </div>
                    </div>
                </div>

                <!-- Market Thermometer -->
                <div v-if="marketTemp" class="glass-card thermo-card" @click="$emit('switch-mode', 'macro')">
                    <div class="thermo-row">
                        <div class="thermo-gauge">
                            <svg width="80" height="80" viewBox="0 0 80 80">
                                <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="6"/>
                                <circle cx="40" cy="40" r="34" fill="none" 
                                    :stroke="marketTemp.color" stroke-width="6"
                                    stroke-linecap="round"
                                    :stroke-dasharray="(marketTemp.temperature / 100 * 213.6) + ' 213.6'"
                                    stroke-dashoffset="0"
                                    transform="rotate(-90 40 40)"
                                    style="transition: all 1s ease;"/>
                                <text x="40" y="38" text-anchor="middle" fill="white" font-size="18" font-weight="800">{{ marketTemp.temperature }}</text>
                                <text x="40" y="52" text-anchor="middle" fill="rgba(255,255,255,0.5)" font-size="8">°温度</text>
                            </svg>
                        </div>
                        <div class="thermo-info">
                            <div class="thermo-label" :style="{color: marketTemp.color}">🌡️ {{ marketTemp.label }}</div>
                            <div class="thermo-suggestion">{{ marketTemp.suggestion }}</div>
                        </div>
                    </div>
                </div>

                <!-- Today's Actions -->
                <div class="glass-card">
                    <div class="section-header">
                        <h3 class="section-title" style="margin-bottom: 0;">📋 今日该做什么</h3>
                        <button class="pro-btn" style="padding: 0.4rem 0.8rem; font-size: 0.75rem;" @click="$emit('switch-mode', 'recommend')">
                            查看全部 →
                        </button>
                    </div>
                    <div v-if="actions.length === 0" style="padding: 2rem; text-align: center; color: var(--text-muted);">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">☕</div>
                        <p>今天没有需要操作的基金，安心持有即可</p>
                    </div>
                    <div v-else class="action-cards">
                        <div v-for="a in actions" :key="a.fund_code || a.code" class="action-item-card" @click="$emit('analyze-fund', a.fund_code || a.code)">
                            <div class="action-type-badge" :class="'action-' + a.action_type || a.action">
                                {{ (a.action_type || a.action) === 'buy' ? '买入' : (a.action_type || a.action) === 'sell' ? '卖出' : '持有' }}
                            </div>
                            <div class="action-info">
                                <div style="font-weight: 700; font-size: 0.9rem;">{{ a.fund_name || a.name }}</div>
                                <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem;">{{ a.reason }}</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Quick Entry Buttons -->
                <div class="quick-entries">
                    <button class="quick-btn" @click="$emit('switch-mode', 'portfolio')">
                        <span class="quick-icon">💼</span>
                        <span>查看持仓</span>
                    </button>
                    <button class="quick-btn" @click="$emit('switch-mode', 'dca')">
                        <span class="quick-icon">⏳</span>
                        <span>定投中心</span>
                    </button>
                    <button class="quick-btn" @click="$emit('switch-mode', 'tools')">
                        <span class="quick-icon">🛠️</span>
                        <span>工具箱</span>
                    </button>
                    <button class="quick-btn" @click="$emit('switch-mode', 'search')">
                        <span class="quick-icon">🔍</span>
                        <span>找基金</span>
                    </button>
                </div>
            </template>
        </div>
    `,
    computed: {
        summary() {
            return this.dashboardData?.portfolio_summary || {};
        },
        actions() {
            return this.dashboardData?.daily_actions || [];
        },
        marketTemp() {
            return this.dashboardData?.market_temperature;
        }
    },
    methods: {
        formatNum(n) {
            if (n === undefined || n === null) return '0.00';
            return Number(n).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }
    },
    style: `
        .dashboard-view { display: flex; flex-direction: column; gap: 1.5rem; }
        .asset-hero {
            background: linear-gradient(135deg, #6366f1, #8b5cf6, #a855f7) !important;
            border: none !important; padding: 2rem;
        }
        .asset-hero-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem; }
        .asset-label { font-size: 0.85rem; opacity: 0.8; margin-bottom: 0.5rem; }
        .asset-value { font-size: 2.5rem; font-weight: 900; letter-spacing: -0.02em; }
        .asset-hero-bottom { display: flex; gap: 2rem; padding-top: 1.25rem; border-top: 1px solid rgba(255,255,255,0.15); }
        .asset-metric { display: flex; flex-direction: column; gap: 0.25rem; }
        .asset-metric-label { font-size: 0.75rem; opacity: 0.7; }
        .thermo-card { cursor: pointer; transition: transform 0.2s; }
        .thermo-card:hover { transform: translateY(-2px); }
        .thermo-row { display: flex; align-items: center; gap: 1.5rem; }
        .thermo-info { flex: 1; }
        .thermo-label { font-size: 1.1rem; font-weight: 700; margin-bottom: 0.5rem; }
        .thermo-suggestion { font-size: 0.85rem; color: var(--text-muted); line-height: 1.5; }
        .action-cards { display: flex; flex-direction: column; gap: 0.75rem; margin-top: 1rem; }
        .action-item-card {
            display: flex; align-items: center; gap: 1rem; padding: 1rem;
            background: rgba(255,255,255,0.03); border-radius: 12px; cursor: pointer;
            transition: all 0.2s; border: 1px solid rgba(255,255,255,0.05);
        }
        .action-item-card:hover { background: rgba(255,255,255,0.06); transform: translateX(4px); }
        .action-type-badge {
            padding: 0.4rem 0.75rem; border-radius: 8px; font-size: 0.75rem; font-weight: 700;
            white-space: nowrap;
        }
        .action-buy { background: rgba(34,197,94,0.15); color: #22c55e; }
        .action-sell { background: rgba(244,63,94,0.15); color: #f43f5e; }
        .action-hold { background: rgba(99,102,241,0.15); color: #6366f1; }
        .action-info { flex: 1; min-width: 0; }
        .quick-entries { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; }
        .quick-btn {
            display: flex; flex-direction: column; align-items: center; gap: 0.5rem;
            padding: 1.25rem 0.5rem; border-radius: 16px; cursor: pointer; transition: all 0.2s;
            background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
            font-size: 0.8rem; color: var(--text-muted);
        }
        .quick-btn:hover { background: rgba(255,255,255,0.08); color: white; transform: translateY(-2px); }
        .quick-icon { font-size: 1.5rem; }
    `
};
