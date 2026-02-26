
export default {
    name: 'BehaviorProfile',
    props: ['profileData', 'loading'],
    template: `
        <div class="glass-card behavior-profile">
            <h2 class="section-title">🧠 投资者画像</h2>
            
            <div v-if="loading" style="padding: 3rem; text-align: center;">
                <div class="spinner-pro"></div>
            </div>

            <div v-else-if="profileData">
                <!-- Radar Chart SVG -->
                <div class="radar-container">
                    <svg viewBox="0 0 300 280" class="radar-svg">
                        <!-- Background pentagons -->
                        <polygon v-for="level in [1, 2, 3, 4, 5]" :key="'bg-'+level"
                            :points="getPolygonPoints(150, 130, level/5 * 100)"
                            fill="none" :stroke="'rgba(255,255,255,' + (level * 0.02) + ')'" stroke-width="1"/>
                        
                        <!-- Axis lines -->
                        <line v-for="(d, i) in profileData.dimensions" :key="'axis-'+i"
                            x1="150" y1="130"
                            :x2="getPoint(150, 130, 100, i).x" :y2="getPoint(150, 130, 100, i).y"
                            stroke="rgba(255,255,255,0.05)" stroke-width="1"/>
                        
                        <!-- Data polygon -->
                        <polygon :points="dataPoints" 
                            fill="rgba(99,102,241,0.15)" stroke="var(--primary)" stroke-width="2.5"
                            stroke-linejoin="round"/>
                        
                        <!-- Data points -->
                        <circle v-for="(d, i) in profileData.dimensions" :key="'pt-'+i"
                            :cx="getPoint(150, 130, d.value/5*100, i).x"
                            :cy="getPoint(150, 130, d.value/5*100, i).y"
                            r="4" fill="var(--primary)" stroke="white" stroke-width="1.5"/>
                        
                        <!-- Labels -->
                        <text v-for="(d, i) in profileData.dimensions" :key="'label-'+i"
                            :x="getPoint(150, 130, 118, i).x"
                            :y="getPoint(150, 130, 118, i).y"
                            text-anchor="middle" dominant-baseline="middle"
                            fill="rgba(255,255,255,0.7)" font-size="11" font-weight="600">
                            {{ d.name }} {{ d.value }}
                        </text>
                    </svg>
                </div>

                <!-- Profile Summary -->
                <div class="profile-summary glass-card" style="margin-top: 1.5rem;">
                    <div class="profile-type">{{ profileData.profile_type }}</div>
                    <div class="profile-score">综合评分: <span style="color: var(--primary); font-weight: 800;">{{ profileData.avg_score }}</span> / 5</div>
                    <div class="profile-advice">{{ profileData.advice }}</div>
                </div>

                <!-- Dimension details -->
                <div class="dimension-list" style="margin-top: 1rem;">
                    <div v-for="d in profileData.dimensions" :key="d.name" class="dimension-item">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 0.85rem;">{{ d.name }}</span>
                            <span style="font-size: 0.85rem; font-weight: 700; color: var(--primary);">{{ d.value }}/{{ d.max }}</span>
                        </div>
                        <div class="dim-bar">
                            <div class="dim-fill" :style="{width: (d.value / d.max * 100) + '%'}"></div>
                        </div>
                        <div style="font-size: 0.7rem; color: var(--text-muted);">{{ d.description }}</div>
                    </div>
                </div>
            </div>
        </div>
    `,
    computed: {
        dataPoints() {
            if (!this.profileData?.dimensions) return '';
            return this.profileData.dimensions.map((d, i) => {
                const p = this.getPoint(150, 130, d.value / 5 * 100, i);
                return `${p.x},${p.y}`;
            }).join(' ');
        }
    },
    methods: {
        getPoint(cx, cy, r, index) {
            const total = 5;
            const angle = (Math.PI * 2 * index / total) - Math.PI / 2;
            return {
                x: Math.round(cx + r * Math.cos(angle)),
                y: Math.round(cy + r * Math.sin(angle))
            };
        },
        getPolygonPoints(cx, cy, r) {
            return Array.from({ length: 5 }, (_, i) => {
                const p = this.getPoint(cx, cy, r, i);
                return `${p.x},${p.y}`;
            }).join(' ');
        }
    },
    style: `
        .behavior-profile { text-align: left; }
        .radar-container { display: flex; justify-content: center; margin-top: 1rem; }
        .radar-svg { width: 100%; max-width: 320px; }
        .profile-summary { text-align: center; padding: 1.5rem; }
        .profile-type { font-size: 1.25rem; font-weight: 800; color: var(--primary); margin-bottom: 0.5rem; }
        .profile-score { font-size: 0.9rem; color: var(--text-muted); margin-bottom: 0.75rem; }
        .profile-advice { font-size: 0.85rem; color: rgba(255,255,255,0.7); line-height: 1.6; }
        .dimension-list { display: flex; flex-direction: column; gap: 0.75rem; }
        .dimension-item { padding: 0.5rem 0; }
        .dim-bar { height: 4px; background: rgba(255,255,255,0.05); border-radius: 2px; margin: 0.4rem 0; }
        .dim-fill { height: 100%; background: var(--primary); border-radius: 2px; transition: width 0.6s ease; }
    `
};
