
export default {
    name: 'RecommendView',
    props: ['loading', 'recommendations', 'recTab', 'predictions', 'marketNews', 'compareList', 'renderMarkdown', 'getSentimentText', 'getScoreClass'],
    emits: ['update:recTab', 'analyze-fund', 'toggle-compare', 'search-query'],
    computed: {
        currentList() {
            if (!this.recommendations?.recommendations) return [];
            return this.recommendations.recommendations[this.recTab] || [];
        }
    },
    template: `
        <div v-if="recommendations || loading">
            <div style="display: grid; grid-template-columns: 240px 1fr; gap: 1.5rem; margin-bottom: 2rem; align-items: start;">
                <!-- Left Module: Market Sentiment -->
                <div class="glass-card" style="display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 1.5rem;">
                    <div style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 0.5rem;">市场情绪指数</div>
                    <div style="font-size: 3.5rem; font-weight: 800; line-height: 1; margin-bottom: 0.5rem;"
                        :style="{color: (recommendations?.market_sentiment || 50) > 60 ? 'var(--primary)' : ((recommendations?.market_sentiment || 50) < 40 ? 'var(--success)' : '#ecf0f1')}">
                        {{ recommendations?.market_sentiment || 50 }}
                    </div>
                    <div class="score-pill"
                        :class="{'score-A': (recommendations?.market_sentiment || 50) >= 70, 'score-B': (recommendations?.market_sentiment || 50) >= 50 && (recommendations?.market_sentiment || 50) < 70, 'score-C': (recommendations?.market_sentiment || 50) < 50}"
                        style="margin-bottom: 0.75rem; font-size: 1rem; padding: 4px 12px;">
                        {{ getSentimentText(recommendations?.market_sentiment || 50) }}
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">
                        📅 {{ new Date().toLocaleDateString() }}
                    </div>
                </div>

                <!-- Right Module: AI Strategy Insight -->
                <div style="display: flex; flex-direction: column;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem; padding-left: 0.5rem;">
                        <h2 class="section-title" style="font-size: 1.2rem; margin: 0;">🧠 AI 策略洞察</h2>
                    </div>

                    <div v-if="loading" class="glass-card" style="min-height: 300px; display: flex; align-items: center; justify-content: center; color: var(--text-muted);">
                        <div class="spinner-pro" style="margin-right: 10px;"></div> 正在生成策略...
                    </div>

                    <div v-else-if="!recommendations" class="glass-card" style="min-height: 300px; display: flex; align-items: center; justify-content: center; color: var(--text-muted);">
                        暂无数据，请同步云端快照
                    </div>

                    <div v-else class="strategy-container">
                        <!-- 1. Stats Grid -->
                        <div class="stats-grid">
                            <div class="data-card">
                                <div class="data-number" style="color: #FFB800">
                                    {{ recommendations?.stats?.avg_score || '47.3' }}<span style="font-size:12px; color:var(--text-muted); font-weight:400;">分</span>
                                </div>
                                <div class="data-label">平均评分(严选池)</div>
                            </div>
                            <div class="data-card">
                                <div class="data-number" style="color: #4ECDC4">
                                    {{ recommendations?.stats?.high_alpha_count || '86' }}<span style="font-size:12px; color:var(--text-muted); font-weight:400;">只</span>
                                </div>
                                <div class="data-label">高Alpha基金(>10%)</div>
                            </div>
                            <div class="data-card">
                                <div class="data-number" style="color: #96CEB4">
                                    {{ recommendations?.stats?.low_risk_count || '32' }}<span style="font-size:12px; color:var(--text-muted); font-weight:400;">只</span>
                                </div>
                                <div class="data-label">低风险稳健(&lt;15%)</div>
                            </div>
                        </div>

                        <!-- 2. AI Summary Text -->
                        <div class="ai-summary-box" v-if="recommendations.ai_summary" v-html="renderMarkdown(recommendations.ai_summary)"></div>

                        <!-- 3. Advice Grid -->
                        <div class="advice-grid">
                            <div class="advice-card" :class="{active: recTab === 'top10'}" style="--card-color: #FF6B6B" @click="$emit('update:recTab', 'top10')">
                                <div class="advice-header">
                                    <div class="advice-title"><span style="font-size:1.2rem">🏆</span> TOP10 精选</div>
                                    <div v-if="recTab === 'top10'"
                                        style="font-size: 0.75rem; color: var(--card-color); font-weight: 700; border: 1px solid var(--card-color); padding: 2px 6px; border-radius: 4px;">
                                        当前选中</div>
                                </div>
                                <div class="advice-desc">综合评分最高的基金，适合作为核心持仓</div>
                                <div class="advice-arrow">查看详情 →</div>
                            </div>
                            <div class="advice-card" :class="{active: recTab === 'high_alpha'}" style="--card-color: #4ECDC4" @click="$emit('update:recTab', 'high_alpha')">
                                <div class="advice-header">
                                    <div class="advice-title"><span style="font-size:1.2rem">🚀</span> 高 Alpha 进攻</div>
                                    <div v-if="recTab === 'high_alpha'"
                                        style="font-size: 0.75rem; color: var(--card-color); font-weight: 700; border: 1px solid var(--card-color); padding: 2px 6px; border-radius: 4px;">
                                        当前选中</div>
                                </div>
                                <div class="advice-desc">超额收益突出，适合进攻型投资者</div>
                                <div class="advice-arrow">查看详情 →</div>
                            </div>
                            <div class="advice-card" :class="{active: recTab === 'long_term'}" style="--card-color: #45B7D1" @click="$emit('update:recTab', 'long_term')">
                                <div class="advice-header">
                                    <div class="advice-title"><span style="font-size:1.2rem">⏳</span> 长线持有</div>
                                    <div v-if="recTab === 'long_term'"
                                        style="font-size: 0.75rem; color: var(--card-color); font-weight: 700; border: 1px solid var(--card-color); padding: 2px 6px; border-radius: 4px;">
                                        当前选中</div>
                                </div>
                                <div class="advice-desc">夏普比率高且回撤控制好，适合长期配置</div>
                                <div class="advice-arrow">查看详情 →</div>
                            </div>
                            <div class="advice-card" :class="{active: recTab === 'low_beta'}" style="--card-color: #96CEB4" @click="$emit('update:recTab', 'low_beta')">
                                <div class="advice-header">
                                    <div class="advice-title"><span style="font-size:1.2rem">🛡️</span> 稳健防守</div>
                                    <div v-if="recTab === 'low_beta'"
                                        style="font-size: 0.75rem; color: var(--card-color); font-weight: 700; border: 1px solid var(--card-color); padding: 2px 6px; border-radius: 4px;">
                                        当前选中</div>
                                </div>
                                <div class="advice-desc">波动和回撤都较低，适合稳健型投资者</div>
                                <div class="advice-arrow">查看详情 →</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Fund List Results -->
            <div class="glass-card">
                <div class="section-header">
                    <h2 class="section-title">📋 推荐列表</h2>
                    <div style="font-size: 0.9rem; color: var(--text-muted);">共筛选出 {{ currentList.length }} 只优质标的</div>
                </div>

                <div v-if="loading" style="padding: 4rem; text-align: center;">
                    <div class="spinner-pro" style="margin: 0 auto 1rem;"></div>
                    <p style="color: var(--text-muted);">正在计算优选方案...</p>
                </div>

                <div v-else-if="currentList.length" class="item-list">
                    <div v-for="fund in currentList" :key="fund.code" class="fund-card" @click="$emit('analyze-fund', fund.code)">
                        <div class="fund-info-header" style="position: relative;">
                            <div style="flex: 1; overflow: hidden;">
                                <div class="fund-name" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{{ fund.name }}</div>
                                <div class="fund-code">{{ fund.code }}</div>
                            </div>
                            <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 0.5rem;">
                                <div class="score-pill" :class="getScoreClass(fund.grade)">{{ fund.score }} 分</div>
                                <div @click.stop="$emit('toggle-compare', fund)" class="score-pill"
                                    style="font-size: 0.65rem; padding: 2px 8px; cursor: pointer; border: 1px solid var(--primary);"
                                    :style="{background: compareList.some(f => f.code === fund.code) ? 'var(--primary)' : 'transparent', color: compareList.some(f => f.code === fund.code) ? 'white' : 'var(--text-muted)'}">
                                    {{ compareList.some(f => f.code === fund.code) ? '✓ 已入PK栏' : '🥇 PK对比' }}
                                </div>
                            </div>
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <span class="score-pill" style="background: rgba(243, 156, 18, 0.1); color: var(--primary); font-size: 0.75rem;">{{ fund.invest_type }}</span>
                        </div>
                        <div class="metrics-row" style="grid-template-columns: 1fr 1fr;">
                            <div class="metric-card" style="padding: 0.75rem; border: none; background: rgba(255,255,255,0.02);">
                                <div class="metric-label" style="font-size: 0.7rem;">Alpha (超额)</div>
                                <div class="metric-value" style="font-size: 1.1rem;" :class="fund.alpha > 0 ? 'text-up' : 'text-down'">{{ fund.alpha }}%</div>
                            </div>
                            <div class="metric-card" style="padding: 0.75rem; border: none; background: rgba(255,255,255,0.02);">
                                <div class="metric-label" style="font-size: 0.7rem;">Sharpe (夏普)</div>
                                <div class="metric-value" style="font-size: 1.1rem;">{{ fund.sharpe }}</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div v-else style="padding: 4rem; text-align: center; color: var(--text-muted);">暂无数据</div>
            </div>

            <!-- Predictions & News -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-top: 2rem;">
                <div class="glass-card">
                    <h2 class="section-title" style="font-size: 1.2rem; margin-bottom: 1rem;">🚀 明日强势预判</h2>
                    <div v-if="predictions.length" style="display: flex; flex-direction: column; gap: 0.75rem;">
                        <div v-for="p in predictions.slice(0, 3)" :key="p.code" @click="$emit('analyze-fund', p.code)"
                            style="background: rgba(255,255,255,0.03); padding: 0.75rem; border-radius: 8px; display: flex; align-items: center; justify-content: space-between; cursor: pointer;">
                            <div>
                                <div style="font-weight: 600;">{{ p.name }}</div>
                                <div style="font-size: 0.75rem; color: var(--text-muted);">{{ p.code }}</div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 0.8rem; color: var(--primary);">上涨概率</div>
                                <div style="font-weight: 800; color: var(--success);">{{ p.probability }}%</div>
                            </div>
                        </div>
                    </div>
                    <div v-else style="color: var(--text-muted); padding: 1rem; text-align: center;">正在计算...</div>
                </div>

                <div class="glass-card">
                    <h2 class="section-title" style="font-size: 1.2rem; margin-bottom: 1rem;">📰 实时电报</h2>
                    <div v-if="marketNews.length" style="display: flex; flex-direction: column; gap: 0.75rem;">
                        <div v-for="news in marketNews.slice(0, 3)" :key="news.title"
                            @click="$emit('search-query', news.title.slice(0, 10))"
                            style="background: rgba(255,255,255,0.03); padding: 0.75rem; border-radius: 8px; cursor: pointer;">
                            <div style="font-size: 0.85rem; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">{{ news.title }}</div>
                            <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 0.25rem;">{{ news.time || news.date }} · {{ news.source }}</div>
                        </div>
                    </div>
                    <div v-else style="color: var(--text-muted); padding: 1rem; text-align: center;">暂无资讯</div>
                </div>
            </div>
        </div>
        <div v-else style="padding: 2rem; text-align: center; color: var(--text-muted);">
            正在初始化推荐模块...
        </div>
    `
};
