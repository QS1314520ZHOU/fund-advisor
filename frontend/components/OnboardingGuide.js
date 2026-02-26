
export default {
    name: 'OnboardingGuide',
    emits: ['onboarding-complete'],
    data() {
        return {
            step: 1,
            experience: '',
            riskLevel: 'moderate',
            loading: false
        };
    },
    template: `
        <div class="onboarding-overlay">
            <div class="onboarding-card glass-card">
                <!-- Step indicator -->
                <div class="onboarding-steps">
                    <div v-for="s in 3" :key="s" class="step-dot" :class="{active: step >= s}"></div>
                </div>

                <!-- Step 1: Experience -->
                <div v-if="step === 1" class="onboarding-content">
                    <div class="onboarding-emoji">👋</div>
                    <h2 class="onboarding-title">欢迎来到 FundAdvisor Pro</h2>
                    <p class="onboarding-desc">先回答一个简单的问题，帮我们更好地为你服务</p>
                    <h3 class="onboarding-question">你买过基金吗？</h3>
                    <div class="onboarding-options">
                        <button class="option-btn" :class="{selected: experience === 'beginner'}" @click="experience = 'beginner'">
                            <div class="option-icon">🌱</div>
                            <div class="option-label">完全没买过</div>
                            <div class="option-desc">我是理财小白</div>
                        </button>
                        <button class="option-btn" :class="{selected: experience === 'intermediate'}" @click="experience = 'intermediate'">
                            <div class="option-icon">🌿</div>
                            <div class="option-label">买过一些</div>
                            <div class="option-desc">了解基本概念</div>
                        </button>
                        <button class="option-btn" :class="{selected: experience === 'advanced'}" @click="experience = 'advanced'">
                            <div class="option-icon">🌳</div>
                            <div class="option-label">经验丰富</div>
                            <div class="option-desc">熟悉各类投资工具</div>
                        </button>
                    </div>
                    <button class="pro-btn onboarding-next" :disabled="!experience" @click="step = 2">
                        下一步 →
                    </button>
                </div>

                <!-- Step 2: Risk -->
                <div v-if="step === 2" class="onboarding-content">
                    <div class="onboarding-emoji">🎯</div>
                    <h2 class="onboarding-title">你的投资偏好</h2>
                    <p class="onboarding-desc">这会影响我们给你推荐的基金类型</p>
                    <h3 class="onboarding-question">遇到亏损你会怎么做？</h3>
                    <div class="onboarding-options">
                        <button class="option-btn" :class="{selected: riskLevel === 'conservative'}" @click="riskLevel = 'conservative'">
                            <div class="option-icon">🛡️</div>
                            <div class="option-label">保守型</div>
                            <div class="option-desc">亏5%就坐立不安</div>
                        </button>
                        <button class="option-btn" :class="{selected: riskLevel === 'moderate'}" @click="riskLevel = 'moderate'">
                            <div class="option-icon">⚖️</div>
                            <div class="option-label">稳健型</div>
                            <div class="option-desc">能接受20%以内的波动</div>
                        </button>
                        <button class="option-btn" :class="{selected: riskLevel === 'aggressive'}" @click="riskLevel = 'aggressive'">
                            <div class="option-icon">🚀</div>
                            <div class="option-label">进取型</div>
                            <div class="option-desc">高风险高回报我能扛</div>
                        </button>
                    </div>
                    <div style="display: flex; gap: 0.75rem;">
                        <button class="pro-btn" style="background: rgba(255,255,255,0.1); flex: 1;" @click="step = 1">← 上一步</button>
                        <button class="pro-btn onboarding-next" style="flex: 2;" @click="step = 3">下一步 →</button>
                    </div>
                </div>

                <!-- Step 3: Welcome -->
                <div v-if="step === 3" class="onboarding-content">
                    <div class="onboarding-emoji">🎉</div>
                    <h2 class="onboarding-title">一切就绪！</h2>
                    <p class="onboarding-desc">
                        {{ experience === 'beginner' ? '我们为你精简了界面，只展示最核心的功能。随着你逐渐熟悉，更多高级工具会逐步解锁。' : 
                           experience === 'intermediate' ? '你可以看到大部分功能，部分高级工具可以稍后探索。' :
                           '所有功能已全部开放，尽情探索吧！' }}
                    </p>
                    <div class="welcome-features">
                        <div class="feature-tag">📊 仪表盘</div>
                        <div class="feature-tag">🎯 智能推荐</div>
                        <div class="feature-tag" v-if="experience !== 'beginner'">💼 资产持仓</div>
                        <div class="feature-tag">⏳ 智能定投</div>
                        <div class="feature-tag">🛠️ 工具箱</div>
                        <div class="feature-tag" v-if="experience === 'advanced'">🌐 宏观视野</div>
                    </div>
                    <button class="pro-btn onboarding-next" style="background: linear-gradient(135deg, #22c55e, #10b981);" @click="finishOnboarding" :disabled="loading">
                        <span v-if="loading" class="spinner-pro" style="width:16px;height:16px;"></span>
                        <span v-else>开始我的投资之旅 🚀</span>
                    </button>
                </div>
            </div>
        </div>
    `,
    methods: {
        async finishOnboarding() {
            this.loading = true;
            try {
                await fetch('/api/v1/user/onboarding', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        experience_level: this.experience,
                        risk_level: this.riskLevel,
                        budget: 10000
                    })
                });
            } catch (e) {
                console.warn('Onboarding save failed:', e);
            }
            localStorage.setItem('fa_onboarding_complete', '1');
            localStorage.setItem('fa_experience_level', this.experience);
            this.$emit('onboarding-complete', { experience: this.experience, risk: this.riskLevel });
            this.loading = false;
        }
    },
    style: `
        .onboarding-overlay {
            position: fixed; inset: 0; z-index: 10000;
            background: rgba(0,0,0,0.85); backdrop-filter: blur(20px);
            display: flex; align-items: center; justify-content: center;
            animation: fadeIn 0.5s ease;
        }
        .onboarding-card {
            max-width: 520px; width: 92%; padding: 2.5rem;
            border-radius: 24px; border: 1px solid rgba(255,255,255,0.1);
            background: rgba(15,15,30,0.95);
        }
        .onboarding-steps {
            display: flex; gap: 0.5rem; justify-content: center; margin-bottom: 2rem;
        }
        .step-dot {
            width: 40px; height: 4px; border-radius: 2px;
            background: rgba(255,255,255,0.1); transition: all 0.3s;
        }
        .step-dot.active { background: var(--primary); }
        .onboarding-content { text-align: center; }
        .onboarding-emoji { font-size: 3rem; margin-bottom: 1rem; }
        .onboarding-title { font-size: 1.5rem; font-weight: 800; margin-bottom: 0.75rem; color: white; }
        .onboarding-desc { color: var(--text-muted); font-size: 0.9rem; margin-bottom: 2rem; line-height: 1.6; }
        .onboarding-question { font-size: 1.1rem; font-weight: 600; color: white; margin-bottom: 1.5rem; }
        .onboarding-options { display: flex; gap: 0.75rem; margin-bottom: 2rem; }
        .option-btn {
            flex: 1; padding: 1.25rem 0.75rem; border-radius: 16px; cursor: pointer; transition: all 0.3s;
            background: rgba(255,255,255,0.03); border: 2px solid rgba(255,255,255,0.08);
            display: flex; flex-direction: column; align-items: center; gap: 0.5rem;
        }
        .option-btn:hover { border-color: rgba(99,102,241,0.3); background: rgba(99,102,241,0.05); }
        .option-btn.selected { border-color: var(--primary); background: rgba(99,102,241,0.1); }
        .option-icon { font-size: 1.75rem; }
        .option-label { font-size: 0.9rem; font-weight: 700; color: white; }
        .option-desc { font-size: 0.7rem; color: var(--text-muted); }
        .onboarding-next { width: 100%; padding: 0.9rem; font-size: 1rem; }
        .welcome-features { display: flex; flex-wrap: wrap; gap: 0.5rem; justify-content: center; margin-bottom: 2rem; }
        .feature-tag {
            padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.8rem;
            background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.2); color: var(--primary);
        }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    `
};
