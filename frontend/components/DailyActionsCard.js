
export default {
    name: 'DailyActionsCard',
    props: ['actions', 'loading'],
    emits: ['analyze-fund'],
    template: `
        <div class="glass-card daily-actions-card" style="margin-bottom: 2rem; position: relative; overflow: hidden;">
            <!-- Background Decoration -->
            <div style="position: absolute; top: -20px; right: -20px; font-size: 8rem; opacity: 0.03; font-weight: 900; pointer-events: none;">
                DAILY
            </div>
            
            <div class="section-header" style="margin-bottom: 1.5rem;">
                <div>
                    <h2 class="section-title" style="margin: 0; display: flex; align-items: center; gap: 0.5rem;">
                        📅 每日操作清单
                    </h2>
                    <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.25rem;">
                        {{ actions?.summary || '通过 AI 综合评分与回撤分析生成的交易指引' }}
                    </p>
                </div>
                <div v-if="actions?.snapshot_date" class="score-pill" style="font-size: 0.75rem; background: rgba(255,255,255,0.05);">
                    {{ actions.snapshot_date }}
                </div>
            </div>

            <div v-if="loading" style="padding: 2rem; text-align: center;">
                <div class="spinner-pro" style="margin: 0 auto 1rem;"></div>
                <p style="color: var(--text-muted);">正在生成今日操作建议...</p>
            </div>

            <div v-else-if="!actions || (!actions.buys?.length && !actions.holds?.length && !actions.sells?.length)" 
                 style="padding: 2rem; text-align: center; color: var(--text-muted);">
                今日暂无特定操作建议，请继续关注。
            </div>

            <div v-else class="actions-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;">
                <!-- BUY ACTIONS -->
                <div v-if="actions.buys?.length" class="action-group">
                    <div class="action-group-header" style="color: var(--success); display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; font-weight: 700;">
                        <span style="font-size: 1.2rem;">🟢</span> 建议买入 / 补仓
                    </div>
                    <div class="action-items" style="display: flex; flex-direction: column; gap: 0.75rem;">
                        <div v-for="item in actions.buys" :key="item.code" class="action-item-card" @click="$emit('analyze-fund', item.code)">
                            <div class="action-item-main">
                                <div class="item-info">
                                    <div class="item-name">{{ item.name }}</div>
                                    <div class="item-code">{{ item.code }}</div>
                                </div>
                                <div class="item-tag" :class="'level-' + item.level">{{ item.level === 'strong' ? '强烈推荐' : '分批介入' }}</div>
                            </div>
                            <div class="item-reason">{{ item.reason }}</div>
                            <div class="item-metrics">
                                <span class="metric-chip">评分: {{ item.score }}</span>
                                <span class="metric-chip">回撤: {{ item.metrics.current_drawdown }}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- HOLD ACTIONS -->
                <div v-if="actions.holds?.length" class="action-group">
                    <div class="action-group-header" style="color: var(--primary); display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; font-weight: 700;">
                        <span style="font-size: 1.2rem;">🔵</span> 建议继续持有
                    </div>
                    <div class="action-items" style="display: flex; flex-direction: column; gap: 0.75rem;">
                        <div v-for="item in actions.holds" :key="item.code" class="action-item-card" @click="$emit('analyze-fund', item.code)">
                            <div class="action-item-main">
                                <div class="item-info">
                                    <div class="item-name">{{ item.name }}</div>
                                    <div class="item-code">{{ item.code }}</div>
                                </div>
                                <div class="item-tag level-normal">稳健持有</div>
                            </div>
                            <div class="item-reason">{{ item.reason }}</div>
                        </div>
                    </div>
                </div>

                <!-- SELL ACTIONS -->
                <div v-if="actions.sells?.length" class="action-group">
                    <div class="action-group-header" style="color: var(--error); display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; font-weight: 700;">
                        <span style="font-size: 1.2rem;">🔴</span> 建议止盈 / 避险
                    </div>
                    <div class="action-items" style="display: flex; flex-direction: column; gap: 0.75rem;">
                        <div v-for="item in actions.sells" :key="item.code" class="action-item-card danger" @click="$emit('analyze-fund', item.code)">
                            <div class="action-item-main">
                                <div class="item-info">
                                    <div class="item-name">{{ item.name }}</div>
                                    <div class="item-code">{{ item.code }}</div>
                                </div>
                                <div class="item-tag level-strong">风险预警</div>
                            </div>
                            <div class="item-reason">{{ item.reason }}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,
    style: `
        .action-item-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 1rem;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .action-item-card:hover {
            background: rgba(255, 255, 255, 0.08);
            transform: translateY(-2px);
            border-color: var(--primary);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        .action-item-main {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.5rem;
        }
        .item-name {
            font-weight: 600;
            font-size: 0.95rem;
            color: #ecf0f1;
        }
        .item-code {
            font-size: 0.75rem;
            color: var(--text-muted);
        }
        .item-tag {
            font-size: 0.65rem;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 700;
        }
        .level-strong {
            background: rgba(231, 76, 60, 0.2);
            color: #ff6b6b;
        }
        .level-normal {
            background: rgba(52, 152, 219, 0.2);
            color: #3498db;
        }
        .item-reason {
            font-size: 0.85rem;
            color: #bdc3c7;
            line-height: 1.4;
            margin-bottom: 0.75rem;
        }
        .item-metrics {
            display: flex;
            gap: 0.5rem;
        }
        .metric-chip {
            font-size: 0.7rem;
            background: rgba(255,255,255,0.05);
            padding: 2px 8px;
            border-radius: 99px;
            color: var(--text-muted);
        }
        .action-item-card.danger:hover {
            border-color: #ff6b6b;
        }
    `
};
