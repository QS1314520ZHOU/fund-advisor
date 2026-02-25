
export default {
    name: 'FundDetailModal',
    props: [
        'fundDetail', 'activeFundTab', 'getScoreClass', 'showRadar', 'defaultRadar',
        'renderAIContent', 'chartPath', 'crashMarkers', 'fundRanks', 'showDca',
        'dcaResults', 'calculateTotalFee', 'fundManager', 'fundNews',
        'renderMarkdown'
    ],
    emits: [
        'close', 'update:activeFundTab', 'update:showRadar', 'update:showDca',
        'run-dca-simulation', 'buy-fund', 'add-to-watchlist', 'analyze-fund'
    ],
    template: `
        <transition name="fade">
            <div v-if="fundDetail" class="deep-dive-overlay">
                <button class="close-btn" @click="$emit('close')">
                    <i data-lucide="x"></i>
                </button>

                <div style="max-width: 1000px; margin: 0 auto; padding-top: 2rem;">
                    <!-- Header -->
                    <div style="margin-bottom: 2rem;">
                        <div
                            style="display: flex; gap: 1rem; align-items: center; margin-bottom: 0.5rem; position: relative;">
                            <h1 style="font-size: 2rem; font-weight: 700; margin: 0;">{{ fundDetail.name }}</h1>

                            <!-- Status Badges -->
                            <div style="display: flex; gap: 0.25rem;">
                                <span v-if="fundDetail.score > 85" class="status-badge badge-hot">🔥 热门</span>
                                <span v-if="parseFloat(fundDetail.metrics?.max_drawdown) < 10"
                                    class="status-badge badge-steady">💎 稳健</span>
                                <span v-if="fundDetail.grade && fundDetail.grade.includes('D')"
                                    class="status-badge badge-warning">⚠️ 风格漂移</span>
                            </div>

                            <div style="position: relative;">
                                <span class="score-pill" :class="getScoreClass(fundDetail.grade)"
                                    @click="$emit('update:showRadar', !showRadar)" style="cursor: pointer; position: relative;">
                                    {{ fundDetail.score }}分
                                    <span style="font-size: 0.7rem; margin-left: 4px; opacity: 0.7;">ⓘ</span>
                                </span>

                                <!-- Radar Chart Overlay -->
                                <div v-if="showRadar" class="radar-overlay" @click.stop>
                                    <div
                                        style="font-weight: 700; margin-bottom: 1rem; border-bottom: 1px solid var(--white-10); padding-bottom: 0.5rem;">
                                        五维能力透视</div>
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
                                        <div v-for="(val, key) in fundDetail.radar_data || defaultRadar" :key="key">
                                            <div class="radar-label help-wrapper">
                                                {{ key }}
                                                <span class="help-icon">?</span>
                                                <knowledge-card :term="getTermKey(key)"></knowledge-card>
                                            </div>
                                            <div class="radar-value">{{ val }}</div>
                                            <div class="rank-bar-container" style="height: 3px;">
                                                <div class="rank-bar-fill" :style="{width: val + '%'}"></div>
                                            </div>
                                        </div>
                                    </div>
                                    <div
                                        style="margin-top: 1rem; font-size: 0.7rem; color: var(--text-muted); line-height: 1.4;">
                                        * 基于近1年收益历、抗跌力、性价比及经理过往表现综合计算。
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div style="display: flex; gap: 1rem; color: var(--text-muted); font-size: 0.9rem;">
                            <span>{{ fundDetail.code }}</span>
                            <span>{{ fundDetail.type }}</span>
                            <span>风险等级: {{ fundDetail.risk_level || '中风险' }}</span>
                        </div>

                        <div style="display: flex; gap: 3rem; margin-top: 1.5rem;">
                            <div>
                                <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.25rem;">
                                    {{ fundDetail.metrics?.estimation_nav ? '今日估值' : '最新净值' }} ({{
                                    fundDetail.metrics?.realtime_time ? fundDetail.metrics?.realtime_time :
                                    fundDetail.metrics?.nav_date }})
                                </div>
                                <div
                                    style="font-size: 2.5rem; font-weight: 700; font-family: 'Outfit'; position: relative;">
                                    {{ fundDetail.metrics?.estimation_nav || fundDetail.metrics?.nav || '--' }}
                                    <span v-if="fundDetail.metrics?.estimation_nav" class="realtime-badge">实时</span>
                                </div>
                            </div>
                            <div>
                                <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.25rem;">
                                    日涨跌幅 {{ fundDetail.metrics?.estimation_growth ? '(估算)' : '' }}
                                </div>
                                <div style="font-size: 2.5rem; font-weight: 700; font-family: 'Outfit';"
                                    :class="(fundDetail.metrics?.estimation_growth || fundDetail.metrics?.change_percent || 0) >= 0 ? 'text-up' : 'text-down'">
                                    {{ (fundDetail.metrics?.estimation_growth || fundDetail.metrics?.change_percent) >=
                                    0 ? '+' : '' }}{{
                                    fundDetail.metrics?.estimation_growth || fundDetail.metrics?.change_percent }}%
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Tabs -->
                    <div class="detail-tabs">
                        <div class="detail-tab" :class="{active: activeFundTab==='brief'}"
                            @click="$emit('update:activeFundTab', 'brief')">
                            基金简况</div>
                        <div class="detail-tab" :class="{active: activeFundTab==='holdings'}"
                            @click="$emit('update:activeFundTab', 'holdings')">持仓分析</div>
                        <div class="detail-tab" :class="{active: activeFundTab==='news'}" @click="$emit('update:activeFundTab', 'news')">
                            公告资讯
                        </div>
                    </div>

                    <!-- Tab Content: Brief -->
                    <div v-if="activeFundTab==='brief'">
                        <!-- v4.0 Analysis Cards (Horizontal Scroll) -->
                        <div v-if="fundDetail.ai_v4_analysis" class="analysis-cards-container"
                            style="margin-bottom: 2rem;">
                            <!-- Summary Card -->
                            <div class="analysis-card" style="border-left: 4px solid var(--primary);">
                                <div class="card-title">{{ fundDetail.ai_v4_analysis.summary_card?.title ||
                                    '策略基调'
                                    }}</div>
                                <div class="card-subtitle">{{ fundDetail.ai_v4_analysis.summary_card?.verdict }}
                                </div>
                                <div style="display: flex; gap: 0.25rem; flex-wrap: wrap; margin-top: 0.5rem;">
                                    <span v-for="tag in fundDetail.ai_v4_analysis.summary_card?.tags" :key="tag"
                                        class="score-pill"
                                        style="font-size: 0.7rem; padding: 2px 6px; background: rgba(99,102,241,0.1); color: var(--primary);">
                                        #{{ tag }}
                                    </span>
                                </div>
                                <div class="card-footer">数据源: {{
                                    fundDetail.ai_v4_analysis.summary_card?.citation
                                    }}</div>
                            </div>

                            <!-- Attribution Card -->
                            <div class="analysis-card">
                                <div class="card-title">{{ fundDetail.ai_v4_analysis.attribution_card?.title ||
                                    '业绩归因' }}</div>
                                <div class="points-list">
                                    <div v-for="(p, i) in fundDetail.ai_v4_analysis.attribution_card?.points" :key="i"
                                        class="point-item">
                                        <span class="dot"
                                            :style="{background: p.impact.includes('下') || p.impact.includes('-') ? 'var(--accent)' : 'var(--success)'}"></span>
                                        <div style="display: flex; flex-direction: column;">
                                            <span style="font-weight: 600;">{{ p.reason }}</span>
                                            <span style="font-size: 0.75rem; color: var(--text-muted);">{{
                                                p.impact }} ({{ p.source }})</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Stress Test Card -->
                            <div class="analysis-card">
                                <div class="card-title help-wrapper" style="font-size: 0.8rem; margin-bottom: 0.4rem;">
                                    压力测试 (If HS300 -10%)
                                    <span class="help-icon">?</span>
                                    <knowledge-card term="beta"></knowledge-card>
                                </div>
                                <div class="stress-value text-down">
                                    -{{ (fundDetail.metrics?.beta * 10 || 1.25 * 10).toFixed(1) }}%
                                </div>
                                <div class="card-footer">
                                    {{ fundDetail.v4_analysis.stress_test?.beta_ref || '基于历史 Beta 值计算' }}
                                </div>
                            </div>
                        </div>

                        <!-- Default AI Banner if no v4 analysis yet -->
                        <div v-else class="glass-card ai-banner" style="margin-bottom: 2rem;">
                            <h3
                                style="font-size: 1.2rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
                                🤖 AI 深度点评
                            </h3>
                            <div v-if="fundDetail.ai_analysis" class="ai-content"
                                v-html="renderAIContent(fundDetail.ai_analysis)"></div>
                            <div v-else style="color: var(--text-muted); padding: 1rem;">
                                <div class="spinner-pro"
                                    style="display: inline-block; margin-right: 0.5rem; vertical-align: middle;">
                                </div>
                                正在生成结构化分析...
                            </div>
                        </div>

                        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 2rem;">
                            <!-- Left: Performance & Charts -->
                            <div>
                                <!-- Price Chart with Crash Markers -->
                                <div class="glass-card" style="margin-bottom: 2rem; padding: 1.5rem;">
                                    <div
                                        style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                                        <h3 class="section-title" style="font-size: 1.1rem; margin: 0;">价格走势 &
                                            历史压力测试</h3>
                                        <div style="font-size: 0.75rem; color: var(--text-muted);">
                                            <span
                                                style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #ef4444; margin-right: 4px;"></span>
                                            关键压力
                                            <span
                                                style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #10b981; margin-left: 8px; margin-right: 4px;"></span>
                                            机会点
                                        </div>
                                    </div>
                                    <div
                                        style="position: relative; width: 100%; height: 220px; background: rgba(0,0,0,0.2); border-radius: 8px; overflow: hidden;">
                                        <svg width="100%" height="200" viewBox="0 0 800 200" preserveAspectRatio="none">
                                            <path :d="chartPath" fill="none" stroke="var(--primary)" stroke-width="2"
                                                vector-effect="non-scaling-stroke" />

                                            <!-- Crash Markers -->
                                            <g v-for="marker in crashMarkers" :key="marker.date">
                                                <line :x1="marker.x" y1="0" :x2="marker.x" y2="200"
                                                    :stroke="marker.color" stroke-dasharray="4,4" opacity="0.4" />
                                                <circle :cx="marker.x" :cy="marker.y" r="4" :fill="marker.color" />
                                                <rect :x="marker.x - 40"
                                                    :y="marker.y < 50 ? marker.y + 10 : marker.y - 25" width="80"
                                                    height="18" rx="4" fill="rgba(15,23,42,0.8)" />
                                                <text :x="marker.x" :y="marker.y < 50 ? marker.y + 22 : marker.y - 12"
                                                    text-anchor="middle" font-size="10" fill="white">{{
                                                    marker.label }}</text>
                                            </g>
                                        </svg>
                                        <div
                                            style="position: absolute; bottom: 5px; left: 0; width: 100%; display: flex; justify-content: space-between; padding: 0 10px; font-size: 0.7rem; color: var(--text-muted); opacity: 0.6;">
                                            <span>{{ fundDetail.history_nav?.[0]?.date }}</span>
                                            <span>{{ fundDetail.history_nav?.[fundDetail.history_nav.length -
                                                1]?.date }}</span>
                                        </div>
                                    </div>
                                    <div v-if="fundDetail.ai_v4_analysis?.stress_test"
                                        style="margin-top: 1rem; font-size: 0.8rem; color: var(--text-muted); line-height: 1.5; padding: 0.75rem; background: rgba(255,255,255,0.03); border-radius: 8px;">
                                        🛡️ **V4 压力测试 (AI)**：{{ fundDetail.ai_v4_analysis.stress_test.prediction
                                        }}
                                        <i>{{ fundDetail.ai_v4_analysis.stress_test.beta_ref }}</i>
                                    </div>
                                    <div v-else
                                        style="margin-top: 1rem; font-size: 0.8rem; color: var(--text-muted); line-height: 1.5; padding: 0.75rem; background: rgba(255,255,255,0.03); border-radius: 8px;">
                                        💡 **回撤修复能力分析**：该基金在最近大回调中表现稳健，修复天数优于同类产品。
                                    </div>
                                </div>

                                <div class="glass-card" style="margin-bottom: 2rem;">
                                    <h3 class="section-title" style="font-size: 1.1rem; margin-bottom: 1rem;">
                                        绩优榜单排名</h3>
                                    <table class="rank-table">
                                        <thead>
                                            <tr>
                                                <th>时间周期</th>
                                                <th>收益率</th>
                                                <th>同类排名</th>
                                                <th>同类平均</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr v-for="rank in fundRanks" :key="rank.period">
                                                <td>{{ rank.period }}</td>
                                                <td :class="parseFloat(rank.percent) > 0 ? 'text-up' : 'text-down'">
                                                    {{ rank.percent }}%
                                                </td>
                                                <td>
                                                    {{ rank.rank }}
                                                    <div class="rank-bar-container">
                                                        <div class="rank-bar-fill"
                                                            :style="{width: (100 - (parseInt(rank.rank.split('/')[0]) / parseInt(rank.rank.split('/')[1]) * 100 || 50)) + '%'}">
                                                        </div>
                                                    </div>
                                                </td>
                                                <td>{{ rank.peer_avg || '--' }}%</td>
                                            </tr>
                                            <!-- Fallback if no ranks -->
                                            <tr v-if="!fundRanks.length">
                                                <td>近1年</td>
                                                <td
                                                    :class="fundDetail.metrics?.return_1y > 0 ? 'text-up' : 'text-down'">
                                                    {{ fundDetail.metrics?.return_1y }}%
                                                </td>
                                                <td>--/--</td>
                                                <td>--</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>

                                <!-- DCA Time Machine -->
                                <div class="glass-card dca-panel" :class="{'dca-active': showDca}">
                                    <div class="dca-switch" @click="$emit('update:showDca', !showDca); if(!showDca) $emit('run-dca-simulation')">
                                        <div class="toggle-track">
                                            <div class="toggle-thumb"></div>
                                        </div>
                                        <span style="font-weight: 700;">开启“时光机”模拟定投</span>
                                        <button v-if="showDca" class="pro-btn" 
                                            style="margin-left: auto; padding: 4px 12px; font-size: 0.75rem; background: var(--success);"
                                            @click.stop="$emit('create-dca-plan', fundDetail.code, fundDetail.name)">
                                            🚀 立即开启定投
                                        </button>
                                    </div>
                                    <div v-if="showDca && dcaResults"
                                        style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; animation: fadeIn 0.4s;">
                                        <div>
                                            <div style="font-size: 0.8rem; color: var(--text-muted);">累计投入
                                                (每周1000)</div>
                                            <div style="font-size: 1.25rem; font-weight: 700;">¥{{
                                                dcaResults.totalInvested.toLocaleString() }}</div>
                                        </div>
                                        <div>
                                            <div style="font-size: 0.8rem; color: var(--text-muted);">定投收益率
                                            </div>
                                            <div style="font-size: 1.5rem; font-weight: 800;"
                                                :class="parseFloat(dcaResults.yield) >= 0 ? 'text-up' : 'text-down'">
                                                {{ parseFloat(dcaResults.yield) >= 0 ? '+' : '' }}{{
                                                dcaResults.yield }}%
                                            </div>
                                        </div>
                                        <div
                                            style="grid-column: span 2; padding: 1rem; background: rgba(16, 185, 129, 0.1); border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.2);">
                                            <div style="font-size: 0.85rem; color: #10b981; font-weight: 600;">
                                                AI 定投建议</div>
                                            <div style="font-size: 0.8rem; line-height: 1.5; margin-top: 0.25rem;">
                                                此基金{{ parseFloat(dcaResults.yield) > 0 ? '适合' : '近期' }}定投，微笑曲线{{
                                                parseFloat(dcaResults.yield) > 10 ? '已初步显现' : '正在形成' }}。{{
                                                parseFloat(dcaResults.yield) > 15 ? '建议继续持有。' : '当前仍是底部吸筹期。' }}
                                            </div>
                                        </div>
                                    </div>
                                    <div v-else-if="!showDca" style="font-size: 0.85rem; color: var(--text-muted);">
                                        穿越回过去，看看如果你从 3 年前开始每周定投 1000 元，现在赚了多少？
                                    </div>
                                </div>

                                <!-- Cost Revealer -->
                                <div class="glass-card"
                                    style="margin-top: 1.5rem; border-left: 4px solid var(--accent);">
                                    <h3 class="section-title help-wrapper" style="font-size: 1.1rem; margin-bottom: 1rem;">
                                        费率刺客：隐形成本折算
                                        <span class="help-icon">?</span>
                                        <knowledge-card term="fees"></knowledge-card>
                                    </h3>
                                    <div style="display: flex; flex-direction: column; gap: 1rem;">
                                        <div style="font-size: 0.85rem; color: var(--text-muted);">
                                            管理费+托管费+销售服务费：<span style="color: var(--accent); font-weight: 700;">{{
                                                fundDetail.metrics?.fees || '1.75' }}% /年</span></div>
                                        <div
                                            style="background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 12px;">
                                            <div
                                                style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                                <span style="font-size: 0.8rem;">10万持有 10 年，你交的费：</span>
                                                <span style="font-weight: 700; color: var(--accent);">¥{{
                                                    calculateTotalFee(100000, 10,
                                                    parseFloat(fundDetail.metrics?.fees ||
                                                    1.75)).toLocaleString(undefined, {minimumFractionDigits: 0,
                                                    maximumFractionDigits: 0}) }}</span>
                                            </div>
                                            <div class="rank-bar-container"
                                                style="height: 6px; background: rgba(255,255,255,0.05);">
                                                <div class="rank-bar-fill"
                                                    style="background: var(--accent); width: 100%;">
                                                </div>
                                            </div>
                                            <div
                                                style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;">
                                                💡 相当于你收益的 <span style="color: var(--white);">15-20%</span>
                                                都被费率吃掉了。建议关注 <span style="color: var(--primary);">ETF/C类</span>
                                                基金。
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- Transaction Guide -->
                                <div class="glass-card" style="margin-top: 1.5rem; border-left: 4px solid var(--success);">
                                    <h3 class="section-title" style="font-size: 1.1rem; margin-bottom: 1rem;">
                                        🛒 交易实务指引</h3>
                                    <div style="display: flex; flex-direction: column; gap: 0.8rem; font-size: 0.85rem;">
                                        <div style="display: flex; gap: 0.8rem; align-items: flex-start;">
                                            <div style="background: rgba(16, 185, 129, 0.1); padding: 4px 8px; border-radius: 4px; color: var(--success); font-weight: 700;">渠道</div>
                                            <div style="line-height: 1.6;">推荐通过 <span style="color: var(--white);">天天基金、蛋卷基金</span> 或 <span style="color: var(--white);">支付宝</span> 购买，申购费率通常 1 折（约 0.1% - 0.15%）。</div>
                                        </div>
                                        <div style="display: flex; gap: 0.8rem; align-items: flex-start;">
                                            <div style="background: rgba(16, 185, 129, 0.1); padding: 4px 8px; border-radius: 4px; color: var(--success); font-weight: 700;">申购</div>
                                            <div style="line-height: 1.6;">T 日 15:00 前申购，T+1 确认份额并开始盈利。</div>
                                        </div>
                                        <div style="display: flex; gap: 0.8rem; align-items: flex-start;">
                                            <div style="background: rgba(244, 63, 94, 0.1); padding: 4px 8px; border-radius: 4px; color: #f43f5e; font-weight: 700;">赎回</div>
                                            <div style="line-height: 1.6;">赎回资金通常在 T+2 至 T+4 个工作日到帐。</div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Right: Manager & Info -->
                            <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                                <div class="glass-card">
                                    <h3 class="section-title" style="font-size: 1.1rem; margin-bottom: 1rem;">
                                        基金经理</h3>
                                    <div v-if="fundManager" style="display: flex; flex-direction: column; gap: 1rem;">
                                        <div style="display: flex; align-items: center; gap: 1rem;">
                                            <div class="manager-avatar">{{ fundManager.name[0] }}</div>
                                            <div>
                                                <div style="display: flex; align-items: center; gap: 0.5rem;">
                                                    <div style="font-weight: 700; font-size: 1.2rem;">{{
                                                        fundManager.name }}</div>
                                                    <div v-if="fundDetail.manager_ai"
                                                        style="font-size: 0.75rem; padding: 2px 6px; background: var(--primary); color: white; border-radius: 4px; font-weight: 700;">
                                                        AI评级 {{ fundDetail.manager_ai.rating }}
                                                    </div>
                                                </div>
                                                <div style="font-size: 0.85rem; color: var(--text-muted);">{{
                                                    fundManager.company }}</div>
                                            </div>
                                        </div>
                                        <div v-if="fundDetail.manager_ai"
                                            style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 5px;">
                                            <span
                                                style="font-size: 0.7rem; padding: 2px 8px; background: rgba(255,255,255,0.05); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);">
                                                风格: {{ fundDetail.manager_ai.style }}
                                            </span>
                                            <span v-for="pro in fundDetail.manager_ai.pros" :key="pro"
                                                style="font-size: 0.7rem; padding: 2px 8px; background: rgba(99,102,241,0.1); color: var(--primary); border-radius: 12px;">
                                                {{ pro }}
                                            </span>
                                        </div>
                                        <div
                                            style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.5rem;">
                                            <div>
                                                <div style="font-size: 0.8rem; color: var(--text-muted);">从业年限
                                                </div>
                                                <div style="font-weight: 600;">{{ fundManager.tenure }}</div>
                                            </div>
                                            <div>
                                                <div style="font-size: 0.8rem; color: var(--text-muted);">管理规模
                                                </div>
                                                <div style="font-weight: 600;">{{ fundManager.scale }}</div>
                                            </div>
                                        </div>

                                        <!-- Manager Career Timeline -->
                                        <div style="margin-top: 1.5rem;">
                                            <div
                                                style="font-size: 0.85rem; font-weight: 700; margin-bottom: 0.75rem; color: var(--primary);">
                                                职业生涯轨迹</div>
                                            <div class="manager-timeline"
                                                style="border-left: 2px dashed rgba(255,255,255,0.1); padding-left: 1rem; margin-left: 5px;">
                                                <div v-for="(item, idx) in fundManager.career || [{period: '2021-至今', desc: '现任该基金经理'}, {period: '2018-2021', desc: 'XX基金公司高级研究员'}]"
                                                    :key="idx" style="position: relative; margin-bottom: 1rem;">
                                                    <div
                                                        style="position: absolute; left: -1.4rem; top: 0.2rem; width: 0.6rem; height: 0.6rem; background: var(--primary); border-radius: 50%;">
                                                    </div>
                                                    <div style="font-size: 0.75rem; color: var(--text-muted);">
                                                        {{ item.period }}</div>
                                                    <div style="font-size: 0.85rem;">{{ item.desc }}</div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div v-else style="color: var(--text-muted); text-align: center; padding: 1rem;">
                                        暂无经理信息</div>
                                </div>

                                <!-- Actions -->
                                <div class="glass-card" style="text-align: center;">
                                    <button class="pro-btn" style="width: 100%; margin-bottom: 1rem;"
                                        @click="$emit('buy-fund', fundDetail.code, fundDetail.name)">
                                        💰 买入/定投
                                    </button>
                                    <button class="pro-btn" style="width: 100%; background: rgba(255,255,255,0.1);"
                                        @click="$emit('add-to-watchlist', fundDetail.code, fundDetail.name)">
                                        ⭐加入自选
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Tab Content: Holdings -->
                    <div v-if="activeFundTab==='holdings'">
                        <div class="glass-card">
                            <h3 class="section-title" style="font-size: 1.1rem; margin-bottom: 1rem;">前十大重仓股
                            </h3>
                            <div v-if="fundDetail.metrics?.top_holdings && fundDetail.metrics.top_holdings.length"
                                class="item-list">
                                <div v-for="stock in fundDetail.metrics.top_holdings" :key="stock.code"
                                    style="padding: 1rem; background: rgba(255,255,255,0.03); border-radius: 12px; display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <div style="font-weight: 600;">{{ stock.name }}</div>
                                        <div style="font-size: 0.8rem; color: var(--text-muted);">{{ stock.code
                                            }}</div>
                                    </div>
                                    <div style="font-weight: 700;">{{ stock.ratio }}</div>
                                </div>
                            </div>
                            <div v-else style="color: var(--text-muted); padding: 2rem; text-align: center;">
                                暂无持仓数据</div>
                        </div>
                    </div>

                    <!-- Tab Content: News -->
                    <div v-if="activeFundTab==='news'">
                        <div class="glass-card">
                            <h3 class="section-title" style="font-size: 1.1rem; margin-bottom: 1rem;">公告与资讯</h3>
                            <div v-if="fundNews.length" class="news-list">
                                <div v-for="(item, idx) in fundNews" :key="idx" class="news-item">
                                    <div style="font-weight: 600; font-size: 1.05rem; margin-bottom: 0.5rem;">
                                        <span
                                            style="font-size: 0.8rem; padding: 2px 6px; background: rgba(99,102,241,0.2); color: var(--primary); border-radius: 4px; margin-right: 0.5rem;">
                                            {{ item.type || '资讯' }}
                                        </span>
                                        {{ item.title }}
                                    </div>
                                    <div
                                        style="font-size: 0.9rem; color: rgba(255,255,255,0.7); line-height: 1.5; margin-bottom: 0.5rem;">
                                        {{ item.summary }}
                                    </div>
                                    <div class="news-meta">
                                        <span>{{ item.date }}</span>
                                        <span>{{ item.source }}</span>
                                    </div>
                                </div>
                            </div>
                            <div v-else style="color: var(--text-muted); padding: 2rem; text-align: center;">
                                暂无相关资讯</div>
                        </div>
                    </div>
                </div>
            </div>
        </transition>
    `,
    methods: {
        getTermKey(label) {
            const map = {
                '收益历': 'alpha',
                '抗跌力': 'max_drawdown',
                '性价比': 'sharpe',
                '波动率': 'volatility',
                '贝塔': 'beta',
                '阿尔法': 'alpha',
                '夏普比率': 'sharpe',
                '最大回撤': 'max_drawdown'
            };
            return map[label] || 'alpha';
        }
    }
};
