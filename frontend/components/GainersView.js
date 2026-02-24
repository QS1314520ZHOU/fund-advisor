
export default {
    name: 'GainersView',
    props: ['gainerPeriods', 'gainerPeriod', 'gainerLoading', 'topGainers', 'compareList'],
    emits: ['update:gainerPeriod', 'fetch-top-gainers', 'analyze-fund', 'toggle-compare'],
    template: `
        <div class="glass-card">
            <div class="section-header">
                <h2 class="section-title">📈 涨幅榜单</h2>
                <div style="display: flex; gap: 0.5rem;">
                    <button v-for="p in gainerPeriods" :key="p.value" class="pro-btn"
                        :style="{padding: '0.4rem 0.8rem', fontSize: '0.8rem', background: gainerPeriod === p.value ? '' : 'rgba(255,255,255,0.05)', opacity: gainerPeriod === p.value ? 1 : 0.7}"
                        @click="$emit('update:gainerPeriod', p.value); $emit('fetch-top-gainers')">
                        {{ p.label }}
                    </button>
                </div>
            </div>

            <div v-if="gainerLoading" style="padding: 4rem; text-align: center;">
                <div class="spinner-pro" style="margin: 0 auto 1rem;"></div>
                <p style="color: var(--text-muted);">获取榜单中...</p>
            </div>

            <div v-else-if="topGainers.length" class="item-list">
                <div v-for="(fund, idx) in topGainers" :key="fund.code" class="fund-card"
                    @click="$emit('analyze-fund', fund.code)">
                    <div class="fund-info-header" style="align-items: center;">
                        <div style="display: flex; align-items: center; gap: 1rem; flex: 1;">
                            <div class="rank-badge" :class="'rank-' + (idx + 1)">{{ idx + 1 }}</div>
                            <div>
                                <div class="fund-name">{{ fund.name }}</div>
                                <div class="fund-code">{{ fund.code }}</div>
                            </div>
                        </div>
                        <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 0.5rem;">
                            <div class="metric-value font-up" style="font-size: 1.25rem;">
                                +{{ fund.gain }}%
                            </div>
                            <div @click.stop="$emit('toggle-compare', fund)" class="score-pill"
                                style="font-size: 0.65rem; padding: 2px 8px; cursor: pointer; border: 1px solid var(--primary);"
                                :style="{background: compareList.some(f => f.code === fund.code) ? 'var(--primary)' : 'transparent', color: compareList.some(f => f.code === fund.code) ? 'white' : 'var(--text-muted)'}">
                                PK
                            </div>
                        </div>
                    </div>
                    <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
                        <span class="score-pill"
                            style="background: rgba(255,255,255,0.05); color: var(--text-muted); font-size: 0.7rem; padding: 2px 6px;">{{
                            fund.type }}</span>
                    </div>
                </div>
            </div>
            <div v-else style="padding: 5rem; text-align: center; color: var(--text-muted);">
                暂无数据，请刷新重试
            </div>
        </div>
    `
};
