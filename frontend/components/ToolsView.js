
export default {
    name: 'ToolsView',
    props: ['feeCalculator'],
    emits: ['calculate-fee'],
    template: `
        <div class="glass-card">
            <h2 class="section-title">🛠️ 专业量化工具</h2>

            <!-- Fee Ninja -->
            <div class="glass-card" style="margin-top: 1.5rem;">
                <h3 class="section-title" style="font-size: 1.1rem;">🥷 费率精算师 (Fee Ninja)</h3>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 2rem;">
                    计算不同持仓周期下，管理费与申购对资产的隐形侵蚀</p>

                <div
                    style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; margin-bottom: 2rem;">
                    <div>
                        <label style="display: block; font-size: 0.8rem; margin-bottom: 0.5rem;">模拟本金 (¥)</label>
                        <input type="number" v-model="feeCalculator.amount" class="pro-input">
                    </div>
                    <div>
                        <label style="display: block; font-size: 0.8rem; margin-bottom: 0.5rem;">持仓年限</label>
                        <input type="number" v-model="feeCalculator.years" class="pro-input">
                    </div>
                    <div>
                        <label style="display: block; font-size: 0.8rem; margin-bottom: 0.5rem;">年综费率 (%)</label>
                        <input type="number" v-model="feeCalculator.rate" step="0.1" class="pro-input">
                    </div>
                </div>

                <button class="pro-btn" style="width: 100%; padding: 1rem;" @click="$emit('calculate-fee')"
                    :disabled="feeCalculator.loading">
                    <span v-if="feeCalculator.loading" class="spinner-pro"></span>
                    <span v-else>立即试算</span>
                </button>

                <div v-if="feeCalculator.result"
                    style="margin-top: 2rem; padding: 1.5rem; background: rgba(244, 63, 94, 0.05); border-radius: 12px; border: 1px dashed rgba(244, 63, 94, 0.3);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: var(--text-muted);">总计费用损失</span>
                        <span class="text-down" style="font-size: 1.5rem; font-weight: 800;">-¥{{
                            feeCalculator.result.fee_loss }}</span>
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.9rem; text-align: right;">
                        相当于损失了初始本金的 <b>{{ (feeCalculator.result.fee_loss / feeCalculator.result.original_amount *
                            100).toFixed(2) }}%</b>
                    </div>
                </div>
            </div>

            <!-- Portfolio Optimizer (Coming Soon) -->
            <div class="glass-card" style="margin-top: 1.5rem; opacity: 0.6; pointer-events: none;">
                <h3 class="section-title" style="font-size: 1.1rem;">🧪 智能调仓专家 (Coming Soon)</h3>
                <p style="font-size: 0.85rem;">基于马科维茨有效前沿 (Markowitz Model) 的自动权重分配</p>
            </div>
        </div>
    `
};
