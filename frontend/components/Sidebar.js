
export default {
    name: 'Sidebar',
    props: ['mode', 'isDark', 'notifications', 'showNotifications', 'experienceLevel'],
    emits: ['switch-mode', 'show-update-dialog', 'toggle-theme', 'toggle-notifications', 'mark-read'],
    computed: {
        navItems() {
            const level = this.experienceLevel || 'advanced';
            const all = [
                { mode: 'dashboard', icon: '📊', label: '我的仪表盘', min: 'beginner' },
                { mode: 'recommend', icon: '🎯', label: '智能推荐', min: 'beginner' },
                { mode: 'dca', icon: '⏳', label: '智能定投', min: 'beginner' },
                { mode: 'tools', icon: '🛠️', label: '专业工具', min: 'beginner' },
                { mode: 'portfolio', icon: '💼', label: '资产持仓', min: 'intermediate' },
                { mode: 'watchlist', icon: '⭐', label: '我的自选', min: 'intermediate' },
                { mode: 'channel', icon: '🏆', label: '基金频道', min: 'intermediate' },
                { mode: 'search', icon: '🔍', label: '深度搜索', min: 'intermediate' },
                { mode: 'gainers', icon: '📈', label: '涨幅榜单', min: 'advanced' },
                { mode: 'history', icon: '🕒', label: '推荐历史', min: 'advanced' },
                { mode: 'macro', icon: '🌐', label: '宏观视野', min: 'advanced' },
                { mode: 'report', icon: '📋', label: '月度体检', min: 'intermediate' },
                { mode: 'behavior', icon: '🧠', label: '投资者画像', min: 'advanced' }
            ];
            const levelOrder = { beginner: 0, intermediate: 1, advanced: 2 };
            const userLevel = levelOrder[level] ?? 2;
            return all.map(item => ({
                ...item,
                visible: userLevel >= (levelOrder[item.min] ?? 0),
                locked: userLevel < (levelOrder[item.min] ?? 0)
            }));
        }
    },
    template: `
        <aside class="sidebar">
            <div class="brand">
                <div class="brand-icon">💰</div>
                <div class="brand-name">FundAdvisor Pro</div>
            </div>

            <nav class="nav-menu">
                <template v-for="item in navItems" :key="item.mode">
                    <button v-if="item.visible" class="nav-item" :class="{active: mode === item.mode}" @click="$emit('switch-mode', item.mode)">
                        {{ item.icon }} {{ item.label }}
                    </button>
                    <button v-else class="nav-item nav-locked" :title="'随着使用深度逐步解锁'" disabled>
                        🔒 {{ item.label }}
                    </button>
                </template>
            </nav>

            <div style="margin-top: auto; padding-top: 2rem; display: flex; flex-direction: column; gap: 0.5rem; position: relative;">
                <button class="nav-item" @click="$emit('toggle-notifications')" style="position: relative;">
                    🔔 消息通知
                    <span v-if="notifications?.length" class="notif-badge">{{ notifications.length }}</span>
                </button>
                
                <!-- Notifications Panel -->
                <div v-if="showNotifications" class="notif-panel glass-card">
                    <div class="notif-header">
                        <span>最新动态</span>
                        <button class="close-notif" @click="$emit('toggle-notifications')">✕</button>
                    </div>
                    <div class="notif-list">
                        <div v-for="notif in notifications" :key="notif.id" class="notif-item" :class="notif.type">
                            <div class="notif-title">{{ notif.title }}</div>
                            <div class="notif-content">{{ notif.content }}</div>
                            <div class="notif-footer">
                                <span>{{ notif.created_at.split(' ')[0] }}</span>
                                <button @click="$emit('mark-read', notif.id)">忽略</button>
                            </div>
                        </div>
                        <div v-if="!notifications?.length" style="padding: 2rem; text-align: center; color: var(--text-muted);">
                            暂无新通知
                        </div>
                    </div>
                </div>

                <button class="nav-item" @click="$emit('toggle-theme')">
                    {{ isDark ? '☀️ 明亮模式' : '🌙 暗色模式' }}
                </button>
                <button class="nav-item" @click="$emit('show-update-dialog')">
                    🔄 同步云端快照
                </button>
            </div>
        </aside>
    `
};
