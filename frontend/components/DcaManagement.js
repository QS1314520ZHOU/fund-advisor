
export default {
    name: 'DcaManagement',
    props: ['plans', 'loading'],
    emits: ['update-plan-status', 'delete-plan', 'analyze-fund'],
    data() {
        return {
            showHistory: {}
        };
    },
    template: `
        <div class="glass-card dca-management">
            <div class="section-header">
                <h2 class="section-title">🕒 我的定投中心</h2>
                <button class="pro-btn" style="padding: 0.5rem 1rem; font-size: 0.8rem;" @click="$emit('switch-mode', 'recommend')">
                    + 新增计划 (前往搜索)
                </button>
            </div>

            <div v-if="loading" style="padding: 2rem; text-align: center;">
                <div class="spinner-pro"></div>
                <p style="color: var(--text-muted); margin-top: 1rem;">加载中...</p>
            </div>

            <div v-else-if="!plans || plans.length === 0" style="padding: 3rem; text-align: center; color: var(--text-muted);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">⏳</div>
                <p>您还没有任何定投计划</p>
                <p style="font-size: 0.85rem; margin-top: 0.5rem;">开启定投，用时间见证财富增长。</p>
            </div>

            <div v-else class="plans-list" style="display: flex; flex-direction: column; gap: 1rem;">
                <div v-for="plan in plans" :key="plan.id" class="glass-card plan-item" 
                     :style="{ borderLeft: '4px solid ' + (plan.is_active ? 'var(--success)' : 'var(--text-muted)') }">
                    <div class="plan-main">
                        <div class="plan-info" @click="$emit('analyze-fund', plan.fund_code)">
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <span class="plan-name">{{ plan.fund_name }}</span>
                                <span class="plan-code">{{ plan.fund_code }}</span>
                            </div>
                            <div class="plan-meta">
                                <span>频率: {{ getFreqText(plan) }}</span>
                                <span>金额: ¥{{ plan.base_amount }}</span>
                            </div>
                        </div>
                        
                        <div class="plan-actions">
                            <button class="action-btn" :title="plan.is_active ? '暂停' : '启动'" 
                                    @click="$emit('update-plan-status', plan.id, !plan.is_active)">
                                {{ plan.is_active ? '⏸️' : '▶️' }}
                            </button>
                            <button class="action-btn" @click="toggleHistory(plan.id)">
                                📜 记录
                            </button>
                        </div>
                    </div>

                    <!-- History Preview -->
                    <div v-if="showHistory[plan.id]" class="plan-history" style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.05);">
                        <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.5rem;">最近执行记录：</div>
                        <div v-if="!plan.records || plan.records.length === 0" style="font-size: 0.8rem; color: var(--text-muted);">
                            暂无执行记录
                        </div>
                        <div v-else class="records-mini-list">
                            <div v-for="rec in plan.records" :key="rec.id" class="record-mini-item">
                                <span>{{ rec.execute_date.split('T')[0] }}</span>
                                <span>¥{{ rec.amount }}</span>
                                <span v-if="rec.nav" style="opacity: 0.6;">(净值: {{ rec.nav }})</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,
    methods: {
        getFreqText(plan) {
            const freq = plan.frequency;
            if (freq === 'weekly') return `每周${['一', '二', '三', '四', '五', '六', '日'][plan.day_of_week]}`;
            if (freq === 'monthly') return `每月${plan.day_of_month}号`;
            return '每日';
        },
        toggleHistory(id) {
            this.showHistory[id] = !this.showHistory[id];
        }
    },
    style: `
        .plan-item {
            padding: 1rem;
            transition: all 0.3s ease;
        }
        .plan-main {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .plan-info {
            cursor: pointer;
            flex: 1;
        }
        .plan-name {
            font-weight: 700;
            color: var(--white);
        }
        .plan-code {
            font-size: 0.75rem;
            color: var(--text-muted);
            background: rgba(255,255,255,0.05);
            padding: 2px 6px;
            border-radius: 4px;
        }
        .plan-meta {
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-top: 0.5rem;
            display: flex;
            gap: 1.5rem;
        }
        .plan-actions {
            display: flex;
            gap: 0.5rem;
        }
        .action-btn {
            background: rgba(255,255,255,0.05);
            border: none;
            color: white;
            padding: 0.5rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: background 0.2s;
        }
        .action-btn:hover {
            background: rgba(255,255,255,0.1);
        }
        .record-mini-item {
            display: flex;
            gap: 1rem;
            font-size: 0.8rem;
            padding: 4px 0;
            color: #bdc3c7;
        }
    `
};
