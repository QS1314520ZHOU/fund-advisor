
export default {
    name: 'WatchlistView',
    props: ['watchlistLoading', 'watchlist', 'generateSparkline'],
    emits: ['fetch-watchlist', 'analyze-fund', 'remove-from-watchlist'],
    template: `
        <div class="glass-card">
            <div class="section-header">
                <h2 class="section-title">⭐ 我的自选</h2>
                <button class="pro-btn" style="padding: 0.5rem 1rem;" @click="$emit('fetch-watchlist')">
                    🔄 刷新
                </button>
            </div>

            <div v-if="watchlistLoading" style="padding: 4rem; text-align: center;">
                <div class="spinner-pro" style="margin: 0 auto;"></div>
            </div>

            <div v-else-if="watchlist.length" class="item-list">
                <div v-for="fund in watchlist" :key="fund.code" class="fund-card"
                    @click="$emit('analyze-fund', fund.code)">
                    <div class="fund-info-header">
                        <div style="flex: 1;">
                            <div class="fund-name">{{ fund.name }}</div>
                            <div class="fund-code">{{ fund.code }}</div>
                        </div>
                        <div style="text-align: right; margin-right: 1rem;">
                            <div class="metric-value" style="font-size: 1.1rem;"
                                :class="fund.estimation_growth >= 0 ? 'font-up' : 'font-down'">
                                {{ fund.estimation_nav?.toFixed(4) || '--' }}
                            </div>
                            <div style="font-size: 0.8rem;"
                                :class="fund.estimation_growth >= 0 ? 'font-up' : 'font-down'">
                                {{ fund.estimation_growth >= 0 ? '+' : '' }}{{ fund.estimation_growth?.toFixed(2)
                                }}% (估)
                            </div>
                        </div>
                        <button class="pro-btn" style="padding: 0.4rem; background: transparent; color: #f43f5e;"
                            @click.stop="$emit('remove-from-watchlist', fund.code)">
                            🗑️
                        </button>
                    </div>
                    <!-- Sparkline Chart -->
                    <div v-if="fund.chart_data && fund.chart_data.length"
                        style="margin-top: 0.8rem; height: 30px; opacity: 0.6;">
                        <svg width="100%" height="30" preserveAspectRatio="none">
                            <path :d="generateSparkline(fund.chart_data)" fill="none"
                                :stroke="fund.estimation_growth >= 0 ? 'var(--success)' : 'var(--accent)'"
                                stroke-width="1.5" />
                        </svg>
                    </div>
                </div>
            </div>

            <div v-else style="padding: 5rem; text-align: center;">
                <p style="color: var(--text-muted); margin-bottom: 2rem;">暂无自选</p>
                <button class="pro-btn" @click="$emit('switch-mode', 'search')">去搜索基金</button>
            </div>
        </div>
    `
};
