
export default {
    name: 'SearchView',
    props: ['searchQuery', 'searchLoading', 'scannerTags', 'searchInterpretation', 'searchResults', 'compareList'],
    emits: ['update:searchQuery', 'handle-search', 'handle-deep-search', 'analyze-fund', 'toggle-compare'],
    template: `
        <div class="glass-card">
            <div style="margin-bottom: 1.5rem; position: relative; display: flex; gap: 1rem;">
                <input class="pro-input" 
                    :value="searchQuery" 
                    @input="$emit('update:searchQuery', $event.target.value)" 
                    @keyup.enter="$emit('handle-search')"
                    placeholder="输入描述 (如: 长期分红高的医疗基金)..." style="flex: 1;">
                <button class="pro-btn" @click="$emit('handle-deep-search')" :disabled="searchLoading">
                    <span v-if="searchLoading" class="spinner-pro"></span>
                    <span v-else>🤖 深度搜索</span>
                </button>
            </div>

            <!-- Super Scanner Storefront -->
            <div
                style="display: flex; gap: 0.75rem; overflow-x: auto; padding-bottom: 1rem; margin-bottom: 1.5rem; scrollbar-width: none;">
                <div v-for="tag in scannerTags" :key="tag.label" class="score-pill"
                    style="cursor: pointer; white-space: nowrap; background: rgba(255,255,255,0.05); color: var(--text-muted); border: 1px solid var(--glass-border);"
                    @click="$emit('update:searchQuery', tag.query); $emit('handle-deep-search')">
                    {{ tag.icon }} {{ tag.label }}
                </div>
            </div>

            <div v-if="searchInterpretation"
                style="background: rgba(99,102,241,0.1); border-left: 3px solid var(--primary); padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 1.5rem; font-size: 0.9rem; color: var(--primary); line-height: 1.4;">
                🤖 <b>AI 解析：</b>{{ searchInterpretation }}
            </div>

            <div v-if="searchResults.length" class="item-list">
                <div v-for="item in searchResults" :key="item.code" class="fund-card"
                    @click="$emit('analyze-fund', item.code)">
                    <div class="fund-info-header">
                        <div style="flex: 1;">
                            <div class="fund-name">{{ item.name }}</div>
                            <div class="fund-code">{{ item.code }}</div>
                        </div>
                        <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 0.5rem;">
                            <div v-if="item.return_1y" style="text-align: right;">
                                <div :class="item.return_1y >= 0 ? 'font-up' : 'font-down'"
                                    style="font-weight: 700;">
                                    {{ item.return_1y >= 0 ? '+' : '' }}{{ item.return_1y }}%
                                </div>
                                <div style="font-size: 0.75rem; color: var(--text-muted);">近1年</div>
                            </div>
                            <div @click.stop="$emit('toggle-compare', item)" class="score-pill"
                                style="font-size: 0.65rem; padding: 2px 8px; cursor: pointer; border: 1px solid var(--primary);"
                                :style="{background: compareList.some(f => f.code === item.code) ? 'var(--primary)' : 'transparent', color: compareList.some(f => f.code === item.code) ? 'white' : 'var(--text-muted)'}">
                                PK
                            </div>
                        </div>
                    </div>
                    <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                        <span v-for="t in (item.themes || [])" :key="t" class="score-pill"
                            style="font-size: 0.7rem; padding: 2px 6px; background: rgba(255,255,255,0.05);">{{
                            t }}</span>
                    </div>
                </div>
            </div>

            <div v-else-if="!searchLoading" style="padding: 5rem; text-align: center; color: var(--text-muted);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
                <div v-if="searchInterpretation" style="margin-bottom: 1rem; color: #fbbf24;">
                    <p>AI 已为您筛选：{{ searchInterpretation }}</p>
                    <p style="font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.8;">(暂无匹配基金，请尝试放宽条件)</p>
                </div>
                <p v-else-if="searchQuery.trim().length >= 2">未找到匹配的基金，请尝试点击 <b>🤖 深度搜索</b></p>
                <p v-else>输入关键词或使用 <b>🤖 深度搜索</b> 寻找优质基金</p>
            </div>

            <div v-if="searchLoading" style="padding: 4rem; text-align: center;">
                <div class="spinner-pro" style="margin: 0 auto 1rem;"></div>
                <p style="color: var(--text-muted);">AI 正在穿透全市场数据...</p>
            </div>
        </div>
    `
};
