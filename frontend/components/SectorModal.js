
export default {
    name: 'SectorModal',
    props: ['showSectorModal', 'selectedSector', 'getSectorIcon', 'sectorDetail', 'loadingSectorDetail', 'renderMarkdown'],
    emits: ['update:showSectorModal', 'analyze-fund', 'search-by-theme'],
    template: `
        <div v-if="showSectorModal" class="modal-overlay" @click.self="$emit('update:showSectorModal', false)">
            <div class="sector-modal-content">
                <div class="section-header" style="padding: 1.5rem; border-bottom: 1px solid var(--glass-border);">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <span style="font-size: 2rem;">{{ getSectorIcon(selectedSector) }}</span>
                        <div>
                            <h2 class="section-title" style="margin: 0; font-size: 1.5rem;">{{ selectedSector }} 板块深度洞察
                            </h2>
                            <div v-if="sectorDetail?.sentiment" class="sentiment-pill"
                                :class="'pill-' + sectorDetail.sentiment.sentiment.toLowerCase().replace(' ', '-')">
                                板块情绪: {{ sectorDetail.sentiment.sentiment }} ({{
                                (sectorDetail.sentiment.ratio*100).toFixed(0) }}% 领涨)
                            </div>
                        </div>
                    </div>
                    <button class="pro-btn" style="padding: 0.5rem; background: transparent;"
                        @click="$emit('update:showSectorModal', false)">✕</button>
                </div>

                <div v-if="loadingSectorDetail" style="padding: 5rem; text-align: center;">
                    <div class="spinner-pro" style="margin: 0 auto 1rem;"></div>
                    <p style="color: var(--text-muted);">正在聚合板块最新动向与 AI 预测...</p>
                </div>

                <div v-else-if="sectorDetail" style="padding: 2rem;">
                    <!-- 1. Prediction Banner -->
                    <div class="glass-card"
                        style="border: 1px solid #FFD700; background: rgba(255, 215, 0, 0.05); margin-bottom: 2rem; padding: 1.5rem;">
                        <div
                            style="display: flex; align-items: center; gap: 0.75rem; color: #FFD700; font-weight: 700;">
                            <span>🔮 AI 未来展望 (1d/1w)</span>
                        </div>
                        <div class="markdown-content" style="margin-top: 1rem;"
                            v-html="renderMarkdown(sectorDetail.prediction.prediction)"></div>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                        <!-- Left: Metrics -->
                        <div class="sector-modal-card">
                            <h3 class="section-title" style="font-size: 1rem; margin-bottom: 1.25rem;">核心表现</h3>
                            <div class="stats-grid" style="grid-template-columns: 1fr; gap: 1rem;">
                                <div class="data-card" style="display: flex; justify-content: space-between;">
                                    <span class="data-label">近1年收益率</span>
                                    <span class="data-number" style="font-size: 1.25rem;"
                                        :class="sectorDetail.metrics.metrics?.avg_return_1y >= 0 ? 'text-up' : 'text-down'">
                                        {{ (sectorDetail.metrics.metrics?.avg_return_1y || 0).toFixed(2) }}%
                                    </span>
                                </div>
                                <div class="data-card" style="display: flex; justify-content: space-between;">
                                    <span class="data-label">平均夏普比率</span>
                                    <span class="data-number" style="font-size: 1.25rem; color: var(--primary);">
                                        {{ (sectorDetail.metrics.metrics?.avg_sharpe || 0).toFixed(2) }}
                                    </span>
                                </div>
                                <div class="data-card" style="display: flex; justify-content: space-between;">
                                    <span class="data-label">平均回撤</span>
                                    <span class="data-number" style="font-size: 1.25rem; color: var(--accent);">
                                        {{ (sectorDetail.metrics.metrics?.avg_drawdown || 0).toFixed(2) }}%
                                    </span>
                                </div>
                            </div>
                        </div>

                        <!-- Right: Top Funds -->
                        <div class="sector-modal-card">
                            <h3 class="section-title" style="font-size: 1rem; margin-bottom: 1.25rem;">板块领涨标的</h3>
                            <div class="item-list">
                                <div v-for="fund in sectorDetail.metrics.top_funds || []" :key="fund.code"
                                    class="fund-card" style="padding: 0.75rem;" @click="$emit('analyze-fund', fund.code)">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <div style="font-size: 0.9rem; font-weight: 600;">{{ fund.name }}</div>
                                        <div class="text-up" style="font-family: 'Outfit'; font-weight: 700;">+{{
                                            fund.return_1y || 0 }}%</div>
                                    </div>
                                    <div style="font-size: 0.7rem; color: var(--text-muted);">{{ fund.code }}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div style="margin-top: 2rem; text-align: center;">
                        <button class="pro-btn" style="padding: 0.75rem 2rem;" @click="$emit('search-by-theme', selectedSector)">
                            🔍 在深度搜索中查看更多 {{ selectedSector }} 基金
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `
};
