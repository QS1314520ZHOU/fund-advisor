
export default {
    name: 'ToolsView',
    props: ['feeCalculator', 'portfolioBuilder'],
    emits: ['calculate-fee', 'build-portfolio', 'analyze-fund'],
    data() {
        return {
            // Recovery Calculator
            recovery: { costPrice: '', currentNav: '', fundCode: '', loading: false, result: null },
            // What-If Simulator
            whatIf: { code: '', amount: 10000, startDate: '2024-01-01', loading: false, result: null }
        };
    },
    template: `
        <div class="glass-card">
            <h2 class="section-title">🛠️ 专业量化工具</h2>

            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1.5rem; margin-top: 1.5rem;">
                <!-- Fee Ninja -->
                <div class="glass-card">
                    <h3 class="section-title" style="font-size: 1.1rem;">🥷 费率精算师</h3>
                    <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 2rem;">
                        计算不同持仓周期下费用对资产的侵蚀</p>

                    <div style="display: flex; flex-direction: column; gap: 1.2rem; margin-bottom: 2rem;">
                        <div>
                            <label style="display: block; font-size: 0.8rem; margin-bottom: 0.5rem;">模拟本金 (¥)</label>
                            <input type="number" v-model="feeCalculator.amount" class="pro-input">
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                            <div>
                                <label style="display: block; font-size: 0.8rem; margin-bottom: 0.5rem;">持仓年限</label>
                                <input type="number" v-model="feeCalculator.years" class="pro-input">
                            </div>
                            <div>
                                <label style="display: block; font-size: 0.8rem; margin-bottom: 0.5rem;">年综费率 (%)</label>
                                <input type="number" v-model="feeCalculator.rate" step="0.1" class="pro-input">
                            </div>
                        </div>
                    </div>
                    <button class="pro-btn" style="width: 100%; padding: 0.8rem;" @click="$emit('calculate-fee')"
                        :disabled="feeCalculator.loading">
                        <span v-if="feeCalculator.loading" class="spinner-pro"></span>
                        <span v-else>立即试算</span>
                    </button>
                    <div v-if="feeCalculator.result" style="margin-top: 1.5rem; padding: 1rem; background: rgba(244, 63, 94, 0.05); border-radius: 12px; border: 1px dashed rgba(244, 63, 94, 0.3);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color: var(--text-muted); font-size: 0.85rem;">预估总费用</span>
                            <span class="text-down" style="font-size: 1.2rem; font-weight: 800;">¥{{ feeCalculator.result.fee_loss }}</span>
                        </div>
                    </div>
                </div>

                <!-- One-click Portfolio Builder -->
                <div class="glass-card">
                    <h3 class="section-title" style="font-size: 1.1rem;">⚡ 一键建仓方案</h3>
                    <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 2rem;">
                        基于您的风险等级，智能分配资产比例</p>

                    <div style="display: flex; flex-direction: column; gap: 1.2rem; margin-bottom: 2rem;">
                        <div>
                            <label style="display: block; font-size: 0.8rem; margin-bottom: 0.5rem;">计划投入 (¥)</label>
                            <input type="number" v-model="portfolioBuilder.amount" class="pro-input" placeholder="输入金额...">
                        </div>
                        <div>
                            <label style="display: block; font-size: 0.8rem; margin-bottom: 0.5rem;">风险偏好</label>
                            <div style="display: flex; gap: 0.5rem;">
                                <button v-for="lvl in ['conservative', 'moderate', 'aggressive']" :key="lvl"
                                    class="pro-btn" style="padding: 0.5rem; flex: 1; font-size: 0.75rem;"
                                    :style="{ background: portfolioBuilder.risk_level === lvl ? 'var(--primary)' : 'rgba(255,255,255,0.05)', color: portfolioBuilder.risk_level === lvl ? 'white' : 'var(--text-muted)' }"
                                    @click="portfolioBuilder.risk_level = lvl">
                                    {{ lvl === 'conservative' ? '保守型' : (lvl === 'moderate' ? '稳健型' : '激进型') }}
                                </button>
                            </div>
                        </div>
                    </div>
                    <button class="pro-btn" style="width: 100%; padding: 0.8rem; background: var(--success);"
                        @click="$emit('build-portfolio')" :disabled="portfolioBuilder.loading">
                        <span v-if="portfolioBuilder.loading" class="spinner-pro"></span>
                        <span v-else>生成方案</span>
                    </button>
                    <div v-if="portfolioBuilder.result" style="margin-top: 1.5rem;">
                        <div style="font-size: 0.85rem; font-weight: 700; margin-bottom: 0.75rem; color: var(--primary);">📋 推荐组合</div>
                        <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                            <div v-for="item in portfolioBuilder.result.portfolio" :key="item.code"
                                class="action-item-card" style="padding: 0.75rem; cursor: pointer;" @click="$emit('analyze-fund', item.code)">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;">
                                    <div style="font-size: 0.85rem; font-weight: 600;">{{ item.name }}</div>
                                    <div style="font-size: 0.75rem; color: var(--primary);">{{ item.ratio * 100 }}%</div>
                                </div>
                                <div style="font-size: 0.7rem; color: var(--text-muted);">{{ item.code }} | ¥{{ item.amount }}</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Recovery Calculator (Feature 5) -->
                <div class="glass-card">
                    <h3 class="section-title" style="font-size: 1.1rem;">🩹 回本计算器</h3>
                    <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 2rem;">
                        输入成本与现价，预测三种情景下的回本时间</p>

                    <div style="display: flex; flex-direction: column; gap: 1.2rem; margin-bottom: 2rem;">
                        <div>
                            <label style="display: block; font-size: 0.8rem; margin-bottom: 0.5rem;">成本净值 (¥)</label>
                            <input type="number" v-model="recovery.costPrice" step="0.001" class="pro-input" placeholder="如 1.520">
                        </div>
                        <div>
                            <label style="display: block; font-size: 0.8rem; margin-bottom: 0.5rem;">当前净值 (¥)</label>
                            <input type="number" v-model="recovery.currentNav" step="0.001" class="pro-input" placeholder="如 1.350">
                        </div>
                    </div>
                    <button class="pro-btn" style="width: 100%; padding: 0.8rem; background: linear-gradient(135deg, #f43f5e, #e11d48);"
                        @click="calcRecovery" :disabled="recovery.loading || !recovery.costPrice || !recovery.currentNav">
                        <span v-if="recovery.loading" class="spinner-pro"></span>
                        <span v-else>计算回本时间</span>
                    </button>
                    <div v-if="recovery.result" style="margin-top: 1.5rem;">
                        <div v-if="recovery.result.already_recovered" style="padding: 1rem; background: rgba(34,197,94,0.08); border-radius: 12px; text-align: center;">
                            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🎉</div>
                            <div style="font-weight: 700; color: #22c55e;">{{ recovery.result.message }}</div>
                        </div>
                        <template v-else>
                            <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.75rem;">
                                距回本还需涨 <span style="color: #f43f5e; font-weight: 700;">{{ recovery.result.gap_pct }}%</span>
                            </div>
                            <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                                <div v-for="s in recovery.result.scenarios" :key="s.name"
                                    style="display: flex; justify-content: space-between; padding: 0.6rem 0.8rem; background: rgba(255,255,255,0.03); border-radius: 8px; font-size: 0.85rem;">
                                    <span>{{ s.name }}</span>
                                    <span style="font-weight: 700; color: white;">≈ {{ s.days }} 交易日 ({{ s.months }}月)</span>
                                </div>
                            </div>
                            <!-- Mini curve -->
                            <div v-if="recovery.result.scenarios?.length" style="margin-top: 1rem;">
                                <svg :viewBox="'0 0 240 80'" style="width: 100%; height: 80px;">
                                    <line x1="0" y1="15" x2="240" y2="15" stroke="rgba(244,63,94,0.3)" stroke-width="1" stroke-dasharray="3"/>
                                    <text x="242" y="18" fill="rgba(244,63,94,0.6)" font-size="7">成本线</text>
                                    <polyline v-for="(s, si) in recovery.result.scenarios" :key="'c'+si"
                                        :points="getCurvePoints(s.curve, recovery.result.cost_price)"
                                        fill="none" :stroke="['#3b82f6','#22c55e','#f59e0b'][si]" stroke-width="1.5"/>
                                </svg>
                            </div>
                        </template>
                    </div>
                </div>
            </div>

            <!-- What-If Simulator (Feature 9) -->
            <div class="glass-card" style="margin-top: 1.5rem;">
                <h3 class="section-title" style="font-size: 1.1rem;">⏳ "如果当初" 历史模拟器</h3>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1.5rem;">
                    如果当初投了某只基金，现在值多少？与余额宝对比</p>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr auto; gap: 1rem; align-items: end;">
                    <div>
                        <label style="display: block; font-size: 0.8rem; margin-bottom: 0.5rem;">基金代码</label>
                        <input type="text" v-model="whatIf.code" class="pro-input" placeholder="如 000001">
                    </div>
                    <div>
                        <label style="display: block; font-size: 0.8rem; margin-bottom: 0.5rem;">投入金额 (¥)</label>
                        <input type="number" v-model="whatIf.amount" class="pro-input">
                    </div>
                    <div>
                        <label style="display: block; font-size: 0.8rem; margin-bottom: 0.5rem;">起始日期</label>
                        <input type="date" v-model="whatIf.startDate" class="pro-input">
                    </div>
                    <button class="pro-btn" style="padding: 0.65rem 1.5rem;" @click="runWhatIf" :disabled="whatIf.loading || !whatIf.code">
                        <span v-if="whatIf.loading" class="spinner-pro" style="width:16px;height:16px;"></span>
                        <span v-else>模拟 →</span>
                    </button>
                </div>

                <div v-if="whatIf.result" style="margin-top: 2rem;">
                    <div style="font-size: 0.9rem; font-weight: 700; margin-bottom: 1rem;">
                        如果 {{ whatIf.result.start_date }} 投入 ¥{{ whatIf.result.amount.toLocaleString() }} 到 
                        <span style="color: var(--primary);">{{ whatIf.result.fund_name }}</span>：
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem;">
                        <div class="data-card">
                            <div class="data-number" :class="whatIf.result.profit >= 0 ? 'font-up' : 'font-down'">
                                ¥{{ whatIf.result.current_value.toLocaleString() }}
                            </div>
                            <div class="data-label">当前价值</div>
                        </div>
                        <div class="data-card">
                            <div class="data-number" :class="whatIf.result.profit_rate >= 0 ? 'font-up' : 'font-down'">
                                {{ whatIf.result.profit_rate >= 0 ? '+' : '' }}{{ whatIf.result.profit_rate }}%
                            </div>
                            <div class="data-label">总收益率</div>
                        </div>
                        <div class="data-card">
                            <div class="data-number">{{ whatIf.result.holding_days }} 天</div>
                            <div class="data-label">持有时长</div>
                        </div>
                        <div class="data-card">
                            <div class="data-number" style="font-size: 0.9rem;" :class="whatIf.result.profit > whatIf.result.money_market_profit ? 'font-up' : 'font-down'">
                                {{ whatIf.result.profit > whatIf.result.money_market_profit ? '跑赢' : '跑输' }}余额宝
                            </div>
                            <div class="data-label">vs 余额宝 ¥{{ whatIf.result.money_market_value?.toLocaleString() }}</div>
                        </div>
                    </div>
                    <!-- Chart -->
                    <div v-if="whatIf.result.chart?.length" style="height: 160px; background: rgba(255,255,255,0.02); border-radius: 12px; padding: 0.5rem; overflow: hidden;">
                        <svg :viewBox="'0 0 600 140'" style="width: 100%; height: 100%;" preserveAspectRatio="none">
                            <polyline :points="getWhatIfLine(whatIf.result.chart, 'fund_value')"
                                fill="none" stroke="var(--primary)" stroke-width="2"/>
                            <polyline :points="getWhatIfLine(whatIf.result.chart, 'money_market')"
                                fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4"/>
                            <!-- Legend -->
                            <line x1="20" y1="8" x2="40" y2="8" stroke="var(--primary)" stroke-width="2"/>
                            <text x="44" y="11" fill="rgba(255,255,255,0.6)" font-size="9">基金</text>
                            <line x1="90" y1="8" x2="110" y2="8" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4"/>
                            <text x="114" y="11" fill="rgba(255,255,255,0.6)" font-size="9">余额宝</text>
                        </svg>
                    </div>
                </div>
            </div>
        </div>
    `,
    methods: {
        async calcRecovery() {
            this.recovery.loading = true;
            try {
                const res = await fetch('/api/v1/tools/recovery-calculator', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ cost_price: parseFloat(this.recovery.costPrice), current_nav: parseFloat(this.recovery.currentNav), fund_code: this.recovery.fundCode })
                });
                const data = await res.json();
                if (data.success) this.recovery.result = data.data;
                else alert(data.error);
            } catch (e) { console.error(e); }
            this.recovery.loading = false;
        },
        async runWhatIf() {
            this.whatIf.loading = true;
            try {
                const res = await fetch(`/api/v1/tools/what-if?code=${this.whatIf.code}&amount=${this.whatIf.amount}&start_date=${this.whatIf.startDate}`);
                const data = await res.json();
                if (data.success) this.whatIf.result = data.data;
                else alert(data.error || '模拟失败');
            } catch (e) { console.error(e); }
            this.whatIf.loading = false;
        },
        getCurvePoints(curve, costPrice) {
            if (!curve?.length) return '';
            const maxMonth = Math.max(...curve.map(c => c.month), 1);
            return curve.map(c => {
                const x = (c.month / maxMonth) * 220 + 10;
                const ratio = c.nav / costPrice;
                const y = 75 - (ratio - 0.85) / 0.3 * 60;
                return `${x},${Math.max(5, Math.min(75, y))}`;
            }).join(' ');
        },
        getWhatIfLine(chart, key) {
            if (!chart?.length) return '';
            const values = chart.map(c => c[key] || 0);
            const min = Math.min(...values) * 0.98;
            const max = Math.max(...values) * 1.02;
            const range = max - min || 1;
            return chart.map((c, i) => {
                const x = (i / (chart.length - 1)) * 580 + 10;
                const y = 130 - ((c[key] - min) / range * 110) + 10;
                return `${x},${y}`;
            }).join(' ');
        }
    }
};
