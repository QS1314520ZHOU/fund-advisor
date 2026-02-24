
export default {
    name: 'AIChatPanel',
    props: ['showChat', 'chatMessages', 'chatInput', 'chatLoading', 'renderMarkdown', 'getScoreClass'],
    emits: ['update:showChat', 'update:chatInput', 'send-message', 'analyze-fund'],
    template: `
        <div>
            <!-- Floating AI Toggle -->
            <div class="floating-ai-btn" @click="$emit('update:showChat', !showChat)">
                <div class="ai-icon-inner">🤖</div>
                <div class="ai-dot"></div>
            </div>

            <!-- AI Chat Assistant (Phase 4) -->
            <div class="chat-panel" :class="{active: showChat}">
                <div class="chat-header">
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <div
                            style="background: white; border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; color: var(--primary);">
                            🤖</div>
                        <div style="font-weight: 700;">AI 私人管家</div>
                    </div>
                    <button @click="$emit('update:showChat', false)"
                        style="background: none; border: none; color: white; cursor: pointer; font-size: 1.2rem;">✕</button>
                </div>

                <div class="chat-messages" id="chatMessages">
                    <div v-for="(msg, idx) in chatMessages" :key="idx" class="message" :class="'message-' + msg.role">
                        <div v-html="renderMarkdown(msg.content)"></div>

                        <div v-if="msg.funds && msg.funds.length"
                            style="margin-top: 1rem; border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 1rem;">
                            <div v-for="f in msg.funds" :key="f.code" class="fund-mini-card"
                                @click="$emit('analyze-fund', f.code); $emit('update:showChat', false)">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div style="font-weight: 700;">{{ f.name }}</div>
                                    <div class="score-pill" :class="getScoreClass(f.grade)" style="font-size: 0.7rem;">{{
                                        f.grade }}</div>
                                </div>
                                <div
                                    style="display: flex; gap: 1rem; margin-top: 0.5rem; font-size: 0.75rem; color: var(--text-muted);">
                                    <span>收益: <b :class="f.return_1y >= 0 ? 'font-up' : 'font-down'">{{
                                            f.return_1y?.toFixed(2) }}%</b></span>
                                    <span>回撤: <b class="font-down">{{ f.max_drawdown?.toFixed(2) }}%</b></span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div v-if="chatLoading" class="message message-ai">
                        <div class="spinner-pro" style="margin-left: 0;"></div>
                    </div>
                </div>

                <div class="chat-input-area">
                    <div class="chat-input-container">
                        <input type="text" 
                            :value="chatInput" 
                            @input="$emit('update:chatInput', $event.target.value)" 
                            @keyup.enter="$emit('send-message')"
                            placeholder="试试说：找一只回撤低、收益高的科技基金..." class="chat-input">
                        <button @click="$emit('send-message')" :disabled="!chatInput || chatLoading"
                            style="background: none; border: none; color: var(--primary); cursor: pointer; padding: 0.5rem;">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
                                stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <line x1="22" y1="2" x2="11" y2="13"></line>
                                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `
};
