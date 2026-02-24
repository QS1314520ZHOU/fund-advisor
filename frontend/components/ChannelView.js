
export default {
    name: 'ChannelView',
    props: ['marketHotspots', 'rankTab', 'rankingListData', 'hotSectors', 'loadingRankings', 'loadingHotspots', 'loadingSectors', 'getSectorIcon', 'getScoreClass'],
    emits: ['update:rankTab', 'open-sector-detail', 'analyze-fund', 'fetch-rankings'],
    template: `
        <div>
            <!-- 1. Market Hotspots -->
            <div class="glass-card" style="margin-bottom: 2rem; padding: 2rem;">
                <div class="section-title"
                    style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <span>🔥 市场热点透视</span>
                        <div v-if="marketHotspots.sentiment" class="sentiment-pill"
                            :class="'pill-' + marketHotspots.sentiment.fear_greed.toLowerCase().replace(' ', '-')">
                            {{ marketHotspots.sentiment.fear_greed }} ({{ marketHotspots.sentiment.score }})
                        </div>
                    </div>
                    <span class="score-pill"
                        style="font-size: 0.8rem; background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3);">AI
                        实时聚合</span>
                </div>

                <div v-if="marketHotspots.sentiment?.breadth && marketHotspots.sentiment.breadth.total > 0"
                    style="margin: 1rem 0;">
                    <div
                        style="display: flex; justify-content: space-between; font-size: 0.75rem; margin-bottom: 4px; color: var(--text-muted);">
                        <span>上涨: {{ marketHotspots.sentiment.breadth.up }}</span>
                        <span>下跌: {{ marketHotspots.sentiment.breadth.down }}</span>
                    </div>
                    <div class="breadth-bar">
                        <div class="breadth-up" :style="{width: marketHotspots.sentiment.breadth.up_ratio + '%'}"></div>
                        <div class="breadth-down"
                            :style="{width: (100 - marketHotspots.sentiment.breadth.up_ratio) + '%'}">
                        </div>
                    </div>
                </div>

                <div v-if="loadingHotspots" style="padding: 2rem; text-align: center;">
                    <div class="spinner-pro" style="margin: 0 auto;"></div>
                </div>
                <div v-else class="hotspots-grid">
                    <div v-for="item in marketHotspots.hotspots" :key="item.id" class="hotspot-card">
                        <div class="hotspot-header">
                            <div class="hotspot-tag-pro"
                                :style="{background: item.type === 'bullish' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', color: item.type === 'bullish' ? '#10b981' : '#ef4444'}">
                                {{ item.type === 'bullish' ? '利好' : '风险' }}
                            </div>
                            <div class="hotspot-time">{{ item.time }}</div>
                        </div>

                        <!-- Block 1: What Happened -->
                        <div class="hotspot-section">
                            <div class="hotspot-label">发生了什么</div>
                            <p class="hotspot-content">{{ item.what_happened }}</p>
                        </div>

                        <!-- Block 2: Sectors -->
                        <div class="hotspot-section">
                            <div class="hotspot-label">涉及板块</div>
                            <div class="hotspot-tags" v-if="item.sectors && item.sectors.length">
                                <span v-for="tag in item.sectors" :key="tag" class="hotspot-tag"
                                    @click="window.appSearch(tag)">
                                    {{ tag }}
                                </span>
                            </div>
                            <p v-else class="hotspot-content" style="opacity: 0.5;">暂无明确板块</p>
                        </div>

                        <!-- Block 3: Comment -->
                        <div class="hotspot-section" style="margin-bottom: 0;">
                            <div class="hotspot-label">简评</div>
                            <div class="hotspot-comment">
                                <p class="hotspot-content">{{ item.comment }}</p>
                            </div>
                        </div>
                    </div>

                    <div v-if="!marketHotspots.hotspots || marketHotspots.hotspots.length === 0"
                        style="color: var(--text-muted); text-align: center; padding: 2rem;">
                        暂无深度热点解析
                    </div>
                </div>
            </div>

            <!-- 2. Hot Sectors -->
            <div style="margin-bottom: 2rem;">
                <div class="section-title">
                    <span>📊 热门行业板块</span>
                </div>
                <div v-if="loadingSectors" style="padding: 2rem; text-align: center;">
                    <div class="spinner-pro" style="margin: 0 auto;"></div>
                </div>
                <div v-else class="sector-scroll-container">
                    <div v-for="sector in hotSectors" :key="sector.sector" class="glass-card sector-mini-card"
                        @click="$emit('open-sector-detail', sector.sector)">
                        <div class="sector-icon">{{ getSectorIcon(sector.sector) }}</div>
                        <div class="sector-info">
                            <div class="sector-name">{{ sector.sector }}</div>
                            <div class="sector-gain" :class="sector.avg_return >= 0 ? 'text-up' : 'text-down'">
                                {{ sector.avg_return >= 0 ? '+' : '' }}{{ (sector.avg_return || 0).toFixed(2) }}%
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 3. Ranking Hub -->
            <div class="glass-card" style="margin-bottom: 3rem;">
                <div class="section-header-flex">
                    <h2 class="section-title" style="margin: 0; display: flex; align-items: center; gap: 1rem;">
                        📋 基金榜单中心
                    </h2>
                    <div class="ranking-tabs">
                        <div class="ranking-tab" :class="{active: rankTab === 'score'}" @click="$emit('fetch-rankings', 'score')">
                            综合优选</div>
                        <div class="ranking-tab" :class="{active: rankTab === 'return_1y'}"
                            @click="$emit('fetch-rankings', 'return_1y')">年化收益</div>
                        <div class="ranking-tab" :class="{active: rankTab === 'sharpe'}"
                            @click="$emit('fetch-rankings', 'sharpe')">稳健先锋</div>
                        <div class="ranking-tab" :class="{active: rankTab === 'alpha'}" @click="$emit('fetch-rankings', 'alpha')">
                            超额进攻</div>
                        <div class="ranking-tab" :class="{active: rankTab === 'max_drawdown'}"
                            @click="$emit('fetch-rankings', 'max_drawdown')">回撤控制</div>
                    </div>
                </div>

                <div v-if="loadingRankings" style="padding: 4rem; text-align: center;">
                    <div class="spinner-pro" style="margin: 0 auto 1rem;"></div>
                    <p style="color: var(--text-muted);">正在实时计算全市场排行...</p>
                </div>
                <div v-else class="item-list">
                    <div v-for="(fund, index) in rankingListData" :key="fund.code" class="fund-card"
                        @click="$emit('analyze-fund', fund.code)">
                        <div class="fund-info-header" style="margin-bottom: 1.25rem;">
                            <div style="display: flex; align-items: center; gap: 0.75rem;">
                                <div class="rank-badge" :class="'rank-' + (index + 1)" v-if="index < 3">{{ index + 1 }}
                                </div>
                                <div class="rank-badge" v-else>{{ index + 1 }}</div>
                                <div>
                                    <div class="fund-name" style="font-size: 1rem;">{{ fund.name }}</div>
                                    <div class="fund-code">{{ fund.code }}</div>
                                </div>
                            </div>
                            <div class="score-pill" :class="getScoreClass(fund.grade)">{{ fund.grade }}</div>
                        </div>
                        <div class="core-metrics-grid" style="margin-bottom: 1rem;">
                            <div class="metric-card"
                                style="padding: 0.75rem; border: none; background: rgba(255,255,255,0.02);">
                                <div class="metric-label" style="font-size: 0.7rem;">最新净值 ({{ fund.nav_date }})</div>
                                <div class="metric-value" style="font-size: 1.1rem;">{{ fund.nav || '--' }}</div>
                            </div>
                            <div class="metric-card"
                                style="padding: 0.75rem; border: none; background: rgba(255,255,255,0.02);">
                                <div class="metric-label" style="font-size: 0.7rem;">日涨跌幅</div>
                                <div class="metric-value" style="font-size: 1.1rem;"
                                    :class="fund.change_percent >= 0 ? 'text-up' : 'text-down'">
                                    {{ fund.change_percent >= 0 ? '+' : '' }}{{ fund.change_percent }}%
                                </div>
                            </div>
                            <div class="metric-card"
                                style="padding: 0.75rem; border: none; background: rgba(255,255,255,0.02);">
                                <div class="metric-label" style="font-size: 0.7rem;">{{ rankTab === 'score' ? '综合评分' :
                                    (rankTab === 'sharpe' ? '夏普比率' : (rankTab === 'max_drawdown' ? '最大回测' : '表现指标')) }}
                                </div>
                                <div class="metric-value" style="font-size: 1.1rem; color: var(--primary);">
                                    {{ rankTab === 'score' ? fund.score : (rankTab === 'max_drawdown' ?
                                    fund.max_drawdown + '%' : fund[rankTab]) }}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};
