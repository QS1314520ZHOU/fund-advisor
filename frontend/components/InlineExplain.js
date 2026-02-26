
export default {
    name: 'InlineExplain',
    props: {
        metric: { type: String, required: true },
        value: { type: Number, default: null }
    },
    setup(props) {
        const { computed } = Vue;

        const explanations = {
            'max_drawdown': {
                name: '最大回撤',
                thresholds: [
                    { max: -20, text: '波动很大，需要较强的心理承受力', level: 'danger' },
                    { max: -10, text: '中等波动，正常范围', level: 'warn' },
                    { max: 0, text: '波动较小，相对稳健', level: 'safe' }
                ],
                explain: (v) => `历史上最多从高点跌了 ${Math.abs(v).toFixed(1)}%`
            },
            'current_drawdown': {
                name: '当前回撤',
                thresholds: [
                    { max: -15, text: '正在经历较大回调', level: 'danger' },
                    { max: -5, text: '有一定回调，可关注', level: 'warn' },
                    { max: 0, text: '接近历史高位', level: 'safe' }
                ],
                explain: (v) => `距离近期高点已跌了 ${Math.abs(v).toFixed(1)}%`
            },
            'sharpe': {
                name: '夏普比率',
                thresholds: [
                    { max: 0.5, text: '性价比偏低', level: 'danger' },
                    { max: 1, text: '性价比尚可', level: 'warn' },
                    { max: 999, text: '性价比优秀', level: 'safe' }
                ],
                explain: (v) => `每承担1份风险换回 ${v.toFixed(2)} 份回报`
            },
            'alpha': {
                name: '超额收益',
                thresholds: [
                    { max: 0, text: '跑输大盘', level: 'danger' },
                    { max: 5, text: '略微跑赢', level: 'warn' },
                    { max: 999, text: '显著跑赢', level: 'safe' }
                ],
                explain: (v) => `比大盘${v >= 0 ? '多赚' : '少赚'}了 ${Math.abs(v).toFixed(1)}%`
            },
            'beta': {
                name: '波动敏感度',
                thresholds: [
                    { max: 0.8, text: '比大盘更抗跌', level: 'safe' },
                    { max: 1.2, text: '和大盘差不多', level: 'warn' },
                    { max: 999, text: '比大盘波动更大', level: 'danger' }
                ],
                explain: (v) => `大盘涨1%时它约涨 ${v.toFixed(2)}%`
            },
            'volatility': {
                name: '波动率',
                thresholds: [
                    { max: 15, text: '波动平稳，适合稳健投资者', level: 'safe' },
                    { max: 25, text: '中等波动', level: 'warn' },
                    { max: 999, text: '波动较大，价格上蹿下跳', level: 'danger' }
                ],
                explain: (v) => `年化波动幅度约 ${v.toFixed(1)}%`
            },
            'annual_return': {
                name: '年化收益',
                thresholds: [
                    { max: 0, text: '目前亏损中', level: 'danger' },
                    { max: 10, text: '收益温和', level: 'warn' },
                    { max: 999, text: '收益出色', level: 'safe' }
                ],
                explain: (v) => `按年计算的综合收益率约 ${v.toFixed(1)}%`
            },
            'return_1y': {
                name: '近1年涨幅',
                thresholds: [
                    { max: 0, text: '近一年亏钱了', level: 'danger' },
                    { max: 15, text: '涨幅温和', level: 'warn' },
                    { max: 999, text: '近一年涨得不错', level: 'safe' }
                ],
                explain: (v) => `过去一年${v >= 0 ? '涨' : '跌'}了 ${Math.abs(v).toFixed(1)}%`
            },
            'win_rate': {
                name: '胜率',
                thresholds: [
                    { max: 45, text: '赚钱概率偏低', level: 'danger' },
                    { max: 55, text: '接近一半概率赚钱', level: 'warn' },
                    { max: 999, text: '大多数时候在赚钱', level: 'safe' }
                ],
                explain: (v) => `历史上 ${v.toFixed(0)}% 的月份是赚钱的`
            },
            'profit_loss_ratio': {
                name: '盈亏比',
                thresholds: [
                    { max: 1, text: '赚的时候赚得少', level: 'danger' },
                    { max: 1.5, text: '盈亏基本对等', level: 'warn' },
                    { max: 999, text: '赚的时候赚得多', level: 'safe' }
                ],
                explain: (v) => `平均每次盈利是亏损的 ${v.toFixed(1)} 倍`
            },
            'score': {
                name: '综合评分',
                thresholds: [
                    { max: 40, text: '评分偏低，谨慎考虑', level: 'danger' },
                    { max: 70, text: '中等水平', level: 'warn' },
                    { max: 999, text: '综合表现优秀', level: 'safe' }
                ],
                explain: (v) => `系统打分 ${v.toFixed(0)} 分（满分100）`
            }
        };

        const info = computed(() => {
            const config = explanations[props.metric];
            if (!config || props.value === null || props.value === undefined) return null;

            const v = props.value;
            let description = config.explain(v);
            let level = 'warn';

            for (const t of config.thresholds) {
                if (v <= t.max) {
                    description += '，' + t.text;
                    level = t.level;
                    break;
                }
            }

            return { description, level };
        });

        return { info };
    },
    template: `
        <span v-if="info" class="inline-explain" :class="'explain-' + info.level" :title="info.description">
            <span class="explain-icon">?</span>
            <span class="explain-text">{{ info.description }}</span>
        </span>
    `,
    style: `
        .inline-explain {
            display: inline-flex; align-items: center; gap: 0.3rem;
            font-size: 0.7rem; line-height: 1.3; margin-left: 0.4rem;
            cursor: help; max-width: 240px;
        }
        .explain-icon {
            width: 14px; height: 14px; border-radius: 50%; font-size: 0.55rem; font-weight: 700;
            display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0;
            background: rgba(255,255,255,0.08); color: var(--text-muted);
        }
        .explain-text { color: var(--text-muted); }
        .explain-safe .explain-text { color: rgba(34,197,94,0.8); }
        .explain-warn .explain-text { color: rgba(251,191,36,0.8); }
        .explain-danger .explain-text { color: rgba(244,63,94,0.8); }
    `
};
