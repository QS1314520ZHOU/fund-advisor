
export default {
    name: 'Sidebar',
    props: ['mode'],
    emits: ['switch-mode', 'show-update-dialog'],
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
                <button class="nav-item" :class="{active: mode === 'tools'}" @click="$emit('switch-mode', 'tools')">
                    🛠️ 专业工具
                </button>
            </nav>

            <div style="margin-top: auto; padding-top: 2rem;">
                <button class="nav-item" @click="$emit('show-update-dialog')">
                    🔄 同步云端快照
                </button>
            </div>
        </aside>
    `
};
