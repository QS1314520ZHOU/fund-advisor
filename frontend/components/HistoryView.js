export default {
    name: 'HistoryView',
    props: ['history', 'loading'],
    emits: ['fetch-history', 'analyze-fund'],
    setup(props, { emit }) {
        const categories = [
            { id: 'top10', label: '核心前十' },
            { id: 'high_alpha', label: '超额尖兵' },
            { id: 'long_term', label: '长跑健将' },
            { id: 'short_term', label: '短线爆发' },
            { id: 'low_beta', label: '稳健防御' }
        ];

        const getReturnClass = (val) => {
            if (!val) return '';
            return val >= 0 ? 'font-up' : 'font-down';
        };

        return { categories, getReturnClass };
    },
    template: `
        <div class="glass-card">
            <div class="section-header">
                <h2 class="section-title">🕒 推荐历史回顾</h2>
                <div style="display: flex; gap: 0.5rem;">
                    <button class="pro-btn" @click="$emit('fetch-history')">🔄 刷新</button>
                </div>
            </div>

            <div v-if="loading" style="text-align: center; padding: 3rem;">
                <div class="spinner-pro" style="margin: 0 auto 1rem;"></div>
                <p style="color: var(--text-muted);">正在回溯历史推荐表现...</p>
            </div>

            <div v-else-if="!Object.keys(history).length" style="padding: 4rem; text-align: center; color: var(--text-muted);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                <p>暂无历史推荐记录，系统将随着每日分析自动积累数据。</p>
            </div>

            <div v-else class="history-timeline">
                <div v-for="(dayData, date) in history" :key="date" class="history-day">
                    <div class="history-date">
                        <div class="date-dot"></div>
                        <span class="date-text">{{ date }}</span>
                    </div>
                    
                    <div class="history-content">
                        <div v-for="(funds, cat) in dayData" :key="cat" class="history-category-block">
                            <div class="history-category-title">{{ categories.find(c => c.id === cat)?.label || cat }}</div>
                            <div class="history-grid">
                                <div v-for="fund in funds" :key="fund.fund_code" class="fund-history-card" @click="$emit('analyze-fund', fund.fund_code)">
                                    <div class="history-fund-name">{{ fund.fund_name }}</div>
                                    <div class="history-fund-meta">
                                        <span>{{ fund.fund_code }}</span>
                                        <span :class="getReturnClass(fund.return_since_recommend)" style="font-weight: 700;">
                                            推荐以来: {{ fund.return_since_recommend >= 0 ? '+' : '' }}{{ fund.return_since_recommend?.toFixed(2) }}%
                                        </span>
                                    </div>
                                    <div class="history-fund-metrics" style="font-size: 0.75rem; opacity: 0.7; margin-top: 4px;">
                                        推荐价: {{ fund.nav_at_recommend?.toFixed(4) }} → 当前: {{ fund.current_nav?.toFixed(4) }}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};
