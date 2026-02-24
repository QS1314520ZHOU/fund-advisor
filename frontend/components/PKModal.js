
export default {
    name: 'PKModal',
    props: ['showPk', 'loadingCompare', 'compareData', 'getScoreClass'],
    emits: ['update:showPk', 'toggle-compare', 'fetch-comparison-matrix'],
    template: `
        <div class="deep-dive-overlay"
            style="z-index: 1500; display: flex; align-items: center; justify-content: center;" v-if="showPk"
            @click="$emit('update:showPk', false)">
            <div class="pk-modal" style="width: 900px; max-width: 95vw;" @click.stop>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
                    <h2 style="margin: 0;">📊 基金强强对决 (Pro)</h2>
                    <button class="close-btn" @click="$emit('update:showPk', false)"
                        style="position: static; padding: 0.5rem;">✕</button>
                </div>

                <div v-if="loadingCompare" style="padding: 4rem; text-align: center;">
                    <div class="spinner-pro" style="margin: 0 auto;"></div>
                    <p style="margin-top: 1rem; color: var(--text-muted);">正在计算持仓重合度与核心指标...</p>
                </div>

                <div v-else-if="compareData" style="overflow-y: auto; max-height: 70vh;">
                    <!-- Similarity Alert -->
                    <div v-if="compareData.similarity && compareData.similarity.overlap_ratio > 30"
                        class="similarity-alert">
                        <span>⚠️</span>
                        <div>
                            <strong>高度持仓重合 ({{ compareData.similarity.overlap_ratio }}%)</strong>
                            <p style="font-size: 0.8rem; opacity: 0.8;">选定基金底层资产非常接近，分散投资效果有限。</p>
                        </div>
                    </div>

                    <div class="pk-matrix-3">
                        <div class="pk-cell pk-header-cell">基本信息</div>
                        <div v-for="f in compareData.data" :key="f.code" class="pk-cell"
                            style="flex-direction: column;">
                            <div style="font-weight: 700;">{{ f.name }}</div>
                            <div style="font-size: 0.75rem; color: var(--text-muted);">{{ f.code }}</div>
                        </div>

                        <div class="pk-cell pk-header-cell">AI 评分</div>
                        <div v-for="f in compareData.data" :key="f.code" class="pk-cell">
                            <div class="score-pill" :class="getScoreClass(f.grade)">{{ f.score || '-' }}</div>
                        </div>

                        <div class="pk-cell pk-header-cell">近1年收益</div>
                        <div v-for="f in compareData.data" :key="f.code" class="pk-cell"
                            :class="f.return_1y >= 0 ? 'font-up' : 'font-down'">
                            {{ f.return_1y ? f.return_1y.toFixed(2) + '%' : '-' }}
                        </div>

                        <div class="pk-cell pk-header-cell">夏普比率</div>
                        <div v-for="f in compareData.data" :key="f.code" class="pk-cell">
                            {{ f.sharpe || '-' }}
                        </div>

                        <div class="pk-cell pk-header-cell">最大回撤</div>
                        <div v-for="f in compareData.data" :key="f.code" class="pk-cell font-down">
                            {{ f.max_drawdown ? f.max_drawdown.toFixed(2) + '%' : '-' }}
                        </div>

                        <div class="pk-cell pk-header-cell">基金经理</div>
                        <div v-for="f in compareData.data" :key="f.code" class="pk-cell" style="font-size: 0.9rem;">
                            {{ f.manager_info?.name || '未知' }}
                        </div>
                    </div>

                    <div
                        style="margin-top: 2rem; padding: 1.5rem; background: rgba(99, 102, 241, 0.1); border-radius: 16px;">
                        <div style="font-weight: 700; margin-bottom: 0.5rem;">🤖 AI 深度对比建议</div>
                        <div style="font-size: 0.9rem; line-height: 1.6; color: var(--text-main);">
                            基于多维数据分析，基金 <strong>{{ compareData.data[0].name }}</strong> 表现出更强的防御属性，适合当前震荡行情。
                            <strong>{{ compareData.data[1].name }}</strong> 在反弹行情中弹性更大。建议根据个人风险承受能力进行分配。
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};
