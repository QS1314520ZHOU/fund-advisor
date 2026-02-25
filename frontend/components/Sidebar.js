
export default {
    name: 'Sidebar',
    props: ['mode', 'isDark', 'notifications', 'showNotifications'],
    emits: ['switch-mode', 'show-update-dialog', 'toggle-theme', 'toggle-notifications', 'mark-read'],
    template: `
        <aside class="sidebar">
            <div class="brand">
                <div class="brand-icon">💰</div>
                <div class="brand-name">FundAdvisor Pro</div>
            </div>

            <nav class="nav-menu">
                <button class="nav-item" :class="{active: mode === 'recommend'}" @click="$emit('switch-mode', 'recommend')">
                    🎯 智能推荐
                </button>
                <button class="nav-item" :class="{active: mode === 'channel'}" @click="$emit('switch-mode', 'channel')">
                    🏆 基金频道
                </button>
                <button class="nav-item" :class="{active: mode === 'gainers'}" @click="$emit('switch-mode', 'gainers')">
                    📈 涨幅榜单
                </button>
                <button class="nav-item" :class="{active: mode === 'search'}" @click="$emit('switch-mode', 'search')">
                    🔍 深度搜索
                </button>
                <button class="nav-item" :class="{active: mode === 'history'}" @click="$emit('switch-mode', 'history')">
                    🕒 推荐历史
                </button>
                <button class="nav-item" :class="{active: mode === 'portfolio'}" @click="$emit('switch-mode', 'portfolio')">
                    💼 资产持仓
                </button>
                <button class="nav-item" :class="{active: mode === 'watchlist'}" @click="$emit('switch-mode', 'watchlist')">
                    ⭐ 我的自选
                </button>
                <button class="nav-item" :class="{active: mode === 'macro'}"
                    @click="$emit('switch-mode', 'macro')">
                    🌐 宏观视野
                </button>
                <button class="nav-item" :class="{active: mode === 'dca'}" @click="$emit('switch-mode', 'dca')">
                    ⏳ 智能定投
                </button>
                <button class="nav-item" :class="{active: mode === 'tools'}" @click="$emit('switch-mode', 'tools')">
                    🛠️ 专业工具
                </button>
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
