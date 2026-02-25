
export default {
    name: 'ToolsView',
    props: ['feeCalculator', 'portfolioBuilder'],
    emits: ['calculate-fee', 'build-portfolio', 'analyze-fund'],
    template: `
        <div class="glass-card">
            <h2 class="section-title">🛠️ 专业量化工具</h2>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-top: 1.5rem;">
                <!-- Fee Ninja -->
                <div class="glass-card">
                    <h3 class="section-title" style="font-size: 1.1rem;">🥷 费率精算师 (Fee Ninja)</h3>
                    <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 2rem;">
                        计算不同持仓周期下，管理费与申购对资产的隐形侵蚀</p>

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

                    <div v-if="feeCalculator.result"
                        style="margin-top: 1.5rem; padding: 1rem; background: rgba(244, 63, 94, 0.05); border-radius: 12px; border: 1px dashed rgba(244, 63, 94, 0.3);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color: var(--text-muted); font-size: 0.85rem;">预估总费用</span>
                            <span class="text-down" style="font-size: 1.2rem; font-weight: 800;">¥{{
                                feeCalculator.result.fee_loss }}</span>
                        </div>
                    </div>
                </div>

                <!-- One-click Portfolio Builder -->
                <div class="glass-card">
                    <h3 class="section-title" style="font-size: 1.1rem;">⚡ 一键建仓方案</h3>
                    <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 2rem;">
                        基于您的风险等级，智能分配资产比例并精选优质基金</p>

                    <div style="display: flex; flex-direction: column; gap: 1.2rem; margin-bottom: 2rem;">
                        <div>
                            <label style="display: block; font-size: 0.8rem; margin-bottom: 0.5rem;">计划投入金额 (¥)</label>
                            <input type="number" v-model="portfolioBuilder.amount" class="pro-input" placeholder="输入金额...">
                        </div>
                        <div>
                            <label style="display: block; font-size: 0.8rem; margin-bottom: 0.5rem;">风险偏好</label>
                            <div style="display: flex; gap: 0.5rem;">
                                <button v-for="lvl in ['conservative', 'moderate', 'aggressive']" 
                                    :key="lvl"
                                    class="pro-btn" 
                                    style="padding: 0.5rem; flex: 1; font-size: 0.75rem;"
                                    :style="{ 
                                        background: portfolioBuilder.risk_level === lvl ? 'var(--primary)' : 'rgba(255,255,255,0.05)',
                                        color: portfolioBuilder.risk_level === lvl ? 'white' : 'var(--text-muted)'
                                    }"
                                    @click="portfolioBuilder.risk_level = lvl">
                                    {{ lvl === 'conservative' ? '保守型' : (lvl === 'moderate' ? '稳健型' : '激进型') }}
                                </button>
                            </div>
                        </div>
                    </div>

                    <button class="pro-btn" style="width: 100%; padding: 0.8rem; background: var(--success);" 
                        @click="$emit('build-portfolio')"
                        :disabled="portfolioBuilder.loading">
                        <span v-if="portfolioBuilder.loading" class="spinner-pro"></span>
                        <span v-else>生成方案</span>
                    </button>
                    
                    <div v-if="portfolioBuilder.result" style="margin-top: 1.5rem;">
                        <div style="font-size: 0.85rem; font-weight: 700; margin-bottom: 0.75rem; color: var(--primary);">📋 推荐组合明细</div>
                        <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                            <div v-for="item in portfolioBuilder.result.portfolio" :key="item.code" 
                                class="action-item-card" style="padding: 0.75rem;" @click="$emit('analyze-fund', item.code)">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;">
                                    <div style="font-size: 0.85rem; font-weight: 600;">{{ item.name }}</div>
                                    <div style="font-size: 0.75rem; color: var(--primary);">{{ item.ratio * 100 }}%</div>
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.7rem; color: var(--text-muted);">
                                    <div>{{ item.code }} | {{ item.category }}</div>
                                    <div>建议: ¥{{ item.amount }}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};
