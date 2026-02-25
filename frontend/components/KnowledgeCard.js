export default {
    name: 'KnowledgeCard',
    props: ['term'],
    setup(props) {
        const knowledgeBase = {
            'alpha': {
                title: '阿尔法 (Alpha)',
                plain: '超额收益能力。',
                detail: '代表基金经理“能多赚多少”。如果市场涨了 10%，你的基金涨了 15%，那多出来的 5% 就是 Alpha。值越高，说明经理选股或择时能力越牛。'
            },
            'beta': {
                title: '贝塔 (Beta)',
                plain: '与市场的同步程度。',
                detail: '代表基金跟随大盘“波动有多大”。Beta=1 表示和大盘同步；Beta>1 说明比大盘更敏感（大盘涨它大涨，大盘跌它也大跌）；Beta<1 则更抗跌。'
            },
            'sharpe': {
                title: '夏普比率 (Sharpe Ratio)',
                plain: '性价比指标。',
                detail: '每多承担一分风险，能换回多少超额收益。夏普比率越高，说明这只基金即便波动大，赚得也值，是“性价比”极佳的表现。'
            },
            'max_drawdown': {
                title: '最大回撤 (Max Drawdown)',
                plain: '最糟糕的情况。',
                detail: '过去一段时间内，从最高点买入到跌到最低点时，亏损最严重的一次是多少。代表了你最坏可能承受多大的心理落差。'
            },
            'volatility': {
                title: '波动率 (Volatility)',
                plain: '上蹿下跳的程度。',
                detail: '描述净值涨跌波动的剧烈程度。波动率越大，你持有时心跳越快，适合心理承受能力强的投资者。'
            },
            'fees': {
                title: '费率刺客',
                plain: '隐形成本。',
                detail: '除了你看到的申购费，还有每日在净值中扣除的管理费和托管费。长期看，它们对总收益的影响非常惊人。'
            }
        };

        return {
            info: knowledgeBase[props.term] || knowledgeBase['alpha']
        };
    },
    template: `
        <div class="knowledge-card">
            <div class="k-header">
                <span class="k-title">{{ info.title }}</span>
                <span class="k-plain">{{ info.plain }}</span>
            </div>
            <div class="k-detail">{{ info.detail }}</div>
        </div>
    `
};
