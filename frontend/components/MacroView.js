
export default {
    name: 'MacroView',
    props: ['macroData'],
    emits: ['fetch-macro-data'],
    template: `
        <div class="glass-card">
            <div class="section-header">
                <h2 class="section-title">🌐 宏观视野</h2>
                <button class="pro-btn" @click="$emit('fetch-macro-data')">🔄 刷新</button>
            </div>

            <div v-if="!macroData" style="padding: 5rem; text-align: center;">
                <div class="spinner-pro" style="margin: 0 auto 1rem;"></div>
                <p style="color: var(--text-muted);">正在连接全球金融数据库...</p>
            </div>

            <div v-else class="strategy-container">
                <div class="stats-grid">
                    <div class="data-card">
                        <div class="data-label">10Y 国债收益率 (中)</div>
                        <div class="data-number" style="color: #6366f1;">{{ macroData.yield_curve.cn_10y }}%</div>
                    </div>
                    <div class="data-card">
                        <div class="data-label">10Y 国债收益率 (美)</div>
                        <div class="data-number" style="color: #f43f5e;">{{ macroData.yield_curve.us_10y }}%</div>
                    </div>
                    <div class="data-card">
                        <div class="data-label">中美利差</div>
                        <div class="data-number"
                            :style="{color: macroData.yield_curve.spread < 0 ? '#f43f5e' : '#10b981'}">
                            {{ macroData.yield_curve.spread }}%
                        </div>
                    </div>
                </div>

                <div class="glass-card"
                    style="background: rgba(99,102,241,0.05); border: 1px solid rgba(99,102,241,0.2);">
                    <h3 class="section-title" style="font-size: 1rem;">💵 汇率动向</h3>
                    <div style="display: flex; align-items: baseline; gap: 1rem; margin-top: 1rem;">
                        <div style="font-size: 2rem; font-weight: 800;">USD/CNY: {{ macroData.currency.usd_cny }}
                        </div>
                        <div style="color: var(--text-muted); font-size: 0.9rem;">实时中间价参考</div>
                    </div>
                </div>

                <div class="glass-card">
                    <h3 class="section-title" style="font-size: 1rem;">🧠 AI 宏观展望</h3>
                    <p style="font-size: 0.95rem; line-height: 1.8; color: var(--text-muted); margin-top: 1rem;">
                        当前中美利差维持在 <b>{{ macroData.yield_curve.spread }}%</b>，对权益类资产特别是高成长板块（科创板、港股）仍有一定估值压力。
                        USD/CNY 报 <b>{{ macroData.currency.usd_cny }}</b>，出口型企业汇兑损益可能增厚。建议关注具备对冲能力的红利资产。
                    </p>
                </div>
            </div>
        </div>
    `
};
