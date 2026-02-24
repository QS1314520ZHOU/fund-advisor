
export default {
    name: 'FilterDrawer',
    props: ['showFilterDrawer', 'activeFilters'],
    emits: ['update:showFilterDrawer', 'update:activeFilters', 'apply-filters'],
    template: `
        <div class="filter-drawer" :class="{active: showFilterDrawer}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2.5rem;">
                <h3 style="margin: 0; font-size: 1.25rem;">🔍 高级筛选</h3>
                <button @click="$emit('update:showFilterDrawer', false)"
                    style="background: none; border: none; color: white; font-size: 1.5rem; cursor: pointer;">✕</button>
            </div>

            <div class="filter-group">
                <label class="filter-label">资产规模</label>
                <div class="filter-options">
                    <div class="filter-chip" :class="{active: activeFilters.scale === 'all'}"
                        @click="activeFilters.scale = 'all'">全部</div>
                    <div class="filter-chip" :class="{active: activeFilters.scale === '50'}"
                        @click="activeFilters.scale = '50'">50亿+</div>
                    <div class="filter-chip" :class="{active: activeFilters.scale === '100'}"
                        @click="activeFilters.scale = '100'">100亿+</div>
                </div>
            </div>

            <div class="filter-group">
                <label class="filter-label">基金经理年资</label>
                <div class="filter-options">
                    <div class="filter-chip" :class="{active: activeFilters.tenure === 'all'}"
                        @click="activeFilters.tenure = 'all'">全部</div>
                    <div class="filter-chip" :class="{active: activeFilters.tenure === '3'}"
                        @click="activeFilters.tenure = '3'">3年以上</div>
                    <div class="filter-chip" :class="{active: activeFilters.tenure === '5'}"
                        @click="activeFilters.tenure = '5'">5年以上</div>
                </div>
            </div>

            <div style="position: absolute; bottom: 2rem; left: 2rem; right: 2rem; display: flex; gap: 1rem;">
                <button class="pro-btn" style="flex: 1; padding: 1rem;" @click="$emit('apply-filters')">应用筛选</button>
                <button class="pro-btn" style="background: rgba(255,255,255,0.05); padding: 1rem;"
                    @click="$emit('update:activeFilters', {scale:'all', tenure:'all', type:'all'})">重置</button>
            </div>
        </div>
    `
};
