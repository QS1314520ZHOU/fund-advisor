
export function getScoreClass(grade) {
    if (!grade) return 'score-C';
    const f = grade.charAt(0);
    return f === 'A' ? 'score-A' : f === 'B' ? 'score-B' : f === 'C' ? 'score-C' : 'score-D';
}

export function getSentimentText(val) {
    if (val < 20) return '极度恐慌';
    if (val < 40) return '恐慌';
    if (val < 60) return '中性';
    if (val < 80) return '贪婪';
    return '极度贪婪';
}

export function getSentimentColor(val) {
    if (val < 40) return '#ef4444';
    if (val < 60) return '#f59e0b';
    return '#10b981';
}

export function getSectorIcon(sector) {
    const icons = {
        '电子': '💻', '科技': '🚀', '新能源': '🔋', '半导体': '💾',
        '白酒': '🍶', '消费': '🛒', '医疗': '🏥', '医药': '💊',
        '金融': '🏦', '银行': '🪙', '保险': '🛡️', '地产': '🏢',
        '军工': '🔫', '煤炭': '🪵', '钢铁': '⛓️', '有色': '⛏️',
        '农业': '🚜', '传媒': '📺', '教育': '📚', '环保': '♻️'
    };
    return icons[sector] || '📍';
}

export function renderMarkdown(text) {
    if (!text) return '';
    try {
        let html = text.trim();

        // 1. Structural Pre-processing
        const sections = [
            { key: '行情综述', icon: '🌏', class: '' },
            { key: 'AI 预判', icon: '🤖', class: 'highlight' },
            { key: '推荐关注', icon: '✅', class: 'recommend' },
            { key: '规避警告', icon: '⚠️', class: 'avoid' },
            { key: '策略建议', icon: '💡', class: '' }
        ];

        // Convert titles to markers
        sections.forEach(s => {
            const reg = new RegExp(`^### ${s.key}|${s.key}:?`, 'gim');
            html = html.replace(reg, `|MARKER|${s.key}|${s.icon}|`);
        });

        // Standard headers
        html = html
            .replace(/^### (.*$)/gim, '|MARKER|$1|🚀|')
            .replace(/^## (.*$)/gim, '|MARKER|$1|🌎|');

        // 2. Split and Wrap into Cards
        if (html.includes('|MARKER|')) {
            const parts = html.split('|MARKER|').filter(p => p.trim());
            let cards = [];

            for (let i = 0; i < parts.length; i += 3) {
                if (!parts[i + 1]) break; // Safety
                const title = parts[i];
                const icon = parts[i + 1];
                const content = parts[i + 2] || '';

                let cardClass = 'strategy-card';
                if (title.includes('推荐关注')) cardClass += ' recommend';
                if (title.includes('规避警告')) cardClass += ' avoid';
                if (title.includes('AI 预判')) cardClass += ' highlight';

                cards.push(`<div class="${cardClass}">
                    <div class="strategy-title">${icon} ${title}</div>
                    <div class="strategy-content">${content.trim()}</div>
                </div>`);
            }
            html = cards.join('');
        }

        // 3. Highlight Transformation
        html = html.replace(/\*\*(.*?)\*\*/gim, '<span class="highlight-gold">$1</span>');
        const highlights = ['降准', '加息', '宽松', '紧缩', '回升', '风险', '反弹', '利好'];
        highlights.forEach(h => {
            const reg = new RegExp(`(?<![">])(${h})(?![^<]*>)`, 'g');
            html = html.replace(reg, `<span class="highlight-gold">$1</span>`);
        });

        // 4. Entity Chips
        const entities = ['半导体', '新能源', '白酒', '人工智能', 'AI', '红利', '医疗', '消费', '科技', '电子', '军工', '地产', '金融', '光伏', '储能', '电池', '量化', '通胀'];
        entities.forEach(entity => {
            const reg = new RegExp(`(?<![">])(${entity})(?![^<]*>)`, 'g');
            html = html.replace(reg, `<span class="entity-link" onclick="window.appSearch('$1')">🏷️ $1</span>`);
        });

        // 5. Cleanup Line Breaks
        html = html
            .replace(/^\- (.*$)/gim, '<div style="display:flex;gap:0.5rem;margin-bottom:0.25rem;"><span style="color:var(--primary)">•</span><span>$1</span></div>')
            .replace(/\n\n/g, '<br/>')
            .replace(/\n/g, '<br/>');

        return `<div class="strategy-container">${html}</div>`;
    } catch (e) {
        console.error('Markdown error', e);
        return text;
    }
}
