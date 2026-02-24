import Sidebar from '../components/Sidebar.js';
import RecommendView from '../components/RecommendView.js';
import ChannelView from '../components/ChannelView.js';
import GainersView from '../components/GainersView.js';
import SearchView from '../components/SearchView.js';
import PortfolioView from '../components/PortfolioView.js';
import WatchlistView from '../components/WatchlistView.js';
import MacroView from '../components/MacroView.js';
import ToolsView from '../components/ToolsView.js';
import SectorModal from '../components/SectorModal.js';
import FundDetailModal from '../components/FundDetailModal.js';
import PKModal from '../components/PKModal.js';
import FilterDrawer from '../components/FilterDrawer.js';
import AIChatPanel from '../components/AIChatPanel.js';
import {
    getScoreClass,
    getSentimentText,
    getSentimentColor,
    getSectorIcon,
    renderMarkdown
} from './utils.js';


const { createApp, ref, computed, onMounted } = Vue;

// ... (rest of the code) ...

createApp({
    components: {
        Sidebar,
        RecommendView,
        ChannelView,
        GainersView,
        SearchView,
        PortfolioView,
        WatchlistView,
        MacroView,
        ToolsView,
        SectorModal,
        FundDetailModal,
        PKModal,
        FilterDrawer,
        AIChatPanel
    },
    setup() {
        // 状态
        const mode = ref('recommend');
        const loading = ref(false);
        const errorMsg = ref('');

        // 推荐页
        const recommendations = ref(null);
        const recommendAiSummary = ref('');
        const predictions = ref([]); // New for V4
        const recTab = ref('top10');
        const recTabs = [
            { key: 'top10', label: '🏆 TOP10' },
            { key: 'high_alpha', label: '📈 高Alpha' },
            { key: 'long_term', label: '💎 长线' },
            { key: 'short_term', label: '⚡ 短线' },
            { key: 'low_beta', label: '🛡️ 防守' }
        ];

        // 搜索页
        const searchQuery = ref('');
        const searchResults = ref([]);
        const searchInterpretation = ref('');
        const searchLoading = ref(false);
        const fundDetail = ref(null);
        const fullFundList = ref([]); // Store static list for local filter
        const scannerTags = [
            { icon: '🦸', label: '抗跌英雄', query: '近1年回撤小于5%且收益为正' },
            { icon: '🏆', label: '高性价比', query: '夏普比率大于1.5' },
            { icon: '🚀', label: '进攻尖兵', query: '近1年收益大于20%的科技或新能源' },
            { icon: '🛡️', label: '稳健红利', query: '低风险且分红高的价值基金' }
        ];
        let searchTimer = null;

        // 涨幅榜
        const topGainers = ref([]);
        const gainerPeriod = ref('1w');
        const gainerLoading = ref(false);
        const gainerPeriods = [
            { value: 'yesterday', label: '昨日' },
            { value: 'today_estimate', label: '今日估算' },
            { value: '1w', label: '1周' },
            { value: '1m', label: '1月' },
            { value: '3m', label: '3月' },
            { value: '6m', label: '6月' }, // Added
            { value: '1y', label: '1年' }, // Added
            { value: '2y', label: '2年' }, // Added
            { value: '3y', label: '3年' }, // Added
            { value: '5y', label: '5年' }  // Added
        ];

        // 持仓
        const portfolio = ref([]);
        const portfolioSummary = ref(null);

        // 自选
        const watchlist = ref([]);
        const watchlistLoading = ref(false);

        // 诊断
        const showDiagnosis = ref(false);
        const diagnosisReport = ref('');

        // V4 Edge States
        const showRadar = ref(false);
        const defaultRadar = { '收益力': 75, '抗跌力': 82, '性价比': 68, '经理能力': 85, '公司实力': 90 };
        const showDca = ref(false);
        const dcaResults = ref(null);

        // PK Comparison
        const compareList = ref([]);
        const showPk = ref(false);
        const compareData = ref(null);
        const loadingCompare = ref(false);

        // Professional Features State
        const macroData = ref(null);
        const backtestResult = ref(null);
        const backtestLoading = ref(false);
        const diagnoseProData = ref(null);
        const loadingDiagnosePro = ref(false);

        // Phase 4: AI Chat
        const showChat = ref(false);
        const chatInput = ref('');
        const chatMessages = ref([
            { role: 'ai', content: '您好！我是您的 AI 私人管家。您可以直接告诉我您的投资偏好，我会为您在全球范围筛选最合适的基金。' }
        ]);
        const chatLoading = ref(false);

        const feeCalculator = ref({
            amount: 100000,
            years: 1,
            rate: 1.5,
            result: null,
            loading: false
        });

        const showFilterDrawer = ref(false);
        const activeFilters = ref({
            scale: 'all',
            tenure: 'all',
            type: 'all'
        });

        const wikiTerms = {
            'Alpha': 'Alpha 是超额收益，即基金收益率与基准收益率之差。正 Alpha 表示基金超越了市场。',
            'Sharpe': '夏普比率衡量每单位风险带来的超额收益。通常大于 1 被认为是优秀的收益风险比。',
            'Sortino': '索提诺比率与夏普比率类似，但它只考虑下行风险（下跌波幅），对稳健型投资者更有参考价值。',
            'MaxDrawdown': '最大回撤指在选定周期内收益率从最高点到最低点的最大跌幅，是衡量抗跌能力的核心指标。',
            'Beta': 'Beta 衡量基金对市场波动的敏感度。Beta = 1 表示与市场同步；Beta > 1 表示波动大于市场。'
        };

        function toggleCompare(fund) {
            const idx = compareList.value.findIndex(f => f.code === fund.code);
            if (idx > -1) {
                compareList.value.splice(idx, 1);
            } else {
                if (compareList.value.length < 3) {
                    compareList.value.push(fund);
                } else {
                    showError('最多支持3只基金进行PK');
                }
            }
        }

        async function fetchComparisonMatrix() {
            if (compareList.value.length < 2) return;
            loadingCompare.value = true;
            showPk.value = true;
            compareData.value = null;
            try {
                const res = await fetch(`${API_BASE}/v1/compare`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ codes: compareList.value.map(f => f.code) })
                });
                const data = await res.json();
                if (data.status === 'success') {
                    compareData.value = data;
                }
            } catch (e) {
                showError('对比加载失败');
            } finally {
                loadingCompare.value = false;
            }
        }

        const crashLibrary = [
            { date: '2015-06-12', label: '5178 顶部', color: '#ef4444' },
            { date: '2015-08-24', label: '股灾2.0', color: '#ef4444' },
            { date: '2018-01-29', label: '贸易战回调', color: '#ef4444' },
            { date: '2020-02-03', label: '疫情底', color: '#10b981' },
            { date: '2022-04-26', label: '估值底', color: '#10b981' },
            { date: '2024-02-05', label: '雪球重锤', color: '#ef4444' }
        ];

        const chartPath = computed(() => {
            if (!fundDetail.value?.history_nav?.length) return '';
            const data = fundDetail.value.history_nav;
            const width = 800;
            const height = 200;
            const padding = 20;

            const navs = data.map(d => parseFloat(d.nav)).filter(v => !isNaN(v));
            const max = Math.max(...navs);
            const min = Math.min(...navs);
            const range = max - min || 1;

            return data.map((d, i) => {
                const x = (i / (data.length - 1)) * (width - 2 * padding) + padding;
                const y = height - ((parseFloat(d.nav) - min) / range * (height - 2 * padding) + padding);
                return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
            }).join(' ');
        });

        const crashMarkers = computed(() => {
            if (!fundDetail.value?.history_nav?.length) return [];
            const data = fundDetail.value.history_nav;
            const width = 800;
            const height = 200;
            const padding = 20;

            const navs = data.map(d => parseFloat(d.nav)).filter(v => !isNaN(v));
            const max = Math.max(...navs);
            const min = Math.min(...navs);
            const range = max - min || 1;

            return crashLibrary.filter(c => {
                const dateStr = c.date;
                return data.some(d => d.date && d.date.startsWith(dateStr.substring(0, 7)));
            }).map(c => {
                const idx = data.findIndex(d => d.date && d.date.startsWith(c.date.substring(0, 7)));
                const x = (idx / (data.length - 1)) * (width - 2 * padding) + padding;
                const y = height - ((parseFloat(data[idx].nav) - min) / range * (height - 2 * padding) + padding);
                return {
                    renderMarkdown,
                    getScoreClass, ...c, x, y
                };
            });
        });

        // 同步弹窗
        const showUpdateDialog = ref(false);
        const adminToken = ref('');
        const updating = ref(false);
        const updateMessage = ref('');
        const updateSuccess = ref(false);

        // Fund Channel Data
        const marketHotspots = ref({ hotspots: [], news_count: 0 });
        const hotSectors = ref([]);
        const rankingListData = ref([]);
        const rankTab = ref('score');
        const loadingRankings = ref(false);
        const loadingHotspots = ref(false);
        const loadingSectors = ref(false);

        // Phase 2: Sector Deep Dive
        const showSectorModal = ref(false);
        const selectedSector = ref('');
        const sectorDetail = ref(null);
        const loadingSectorDetail = ref(false);

        // 计算属性
        const currentList = computed(() => {
            if (!recommendations.value?.recommendations) return [];
            return recommendations.value.recommendations[recTab.value] || [];
        });

        // 方法
        function showError(msg) {
            errorMsg.value = msg;
            setTimeout(() => { errorMsg.value = ''; }, 3000);
        }



        // New Helpers for V4
        const getSentimentText = (val) => {
            if (val < 20) return '极度恐慌';
            if (val < 40) return '恐慌';
            if (val < 60) return '中性';
            if (val < 80) return '贪婪';
            return '极度贪婪';
        };

        const getSentimentColor = (val) => {
            if (val < 40) return '#ef4444';
            if (val < 60) return '#f59e0b';
            return '#10b981';
        };

        const dynamicGreeting = computed(() => {
            const sentiment = recommendations.value?.market_sentiment || 50;
            if (sentiment < 30) return "☕ 市场波动较大，建议喝茶读书，减少盯盘。";
            if (sentiment > 70) return "⚖️ 市场情绪过热，请警惕风险，切勿盲目追高。";
            return "👋 欢迎回来，今天也为您挑选了最值得关注的机会。";
        });

        function renderAIContent(text) {
            if (!text) return '';
            try {
                const html = typeof marked !== 'undefined' ? marked.parse(text) : text.replace(/\n/g, '<br>');
                return typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize(html) : html;
            } catch (e) {
                return text.replace(/\n/g, '<br>');
            }
        }

        const activeFundTab = Vue.ref('brief');
        const fundNews = Vue.ref([]);
        const marketNews = Vue.ref([]);
        const fundManager = Vue.ref(null);
        const fundRanks = Vue.ref([]);

        function renderMarkdown(text) {
            if (!text) return '';
            try {
                // ... (custom markdown rendering logic) ...
                let html = typeof marked !== 'undefined' ? marked.parse(text) : text.replace(/\n/g, '<br>');
                // 1. Semantic Tagging
                const sections = [
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

        function switchMode(newMode) {
            mode.value = newMode;
            if (newMode === 'recommend') fetchRecommendations();
            if (newMode === 'channel') {
                fetchMarketHotspots();
                fetchHotSectors();
                fetchRankings(rankTab.value || 'score');
            }
            if (newMode === 'gainers') fetchTopGainers();
            if (newMode === 'portfolio') fetchPortfolio();
            if (newMode === 'watchlist') {
                fetchWatchlist();
                startWatchlistTimer();
            } else {
                stopWatchlistTimer();
            }
        }

        async function openSectorDetail(sectorName) {
            selectedSector.value = sectorName;
            loadingSectorDetail.value = true;
            showSectorModal.value = true;
            sectorDetail.value = null;

            try {
                const res = await fetch(`${API_BASE}/v1/sectors/${sectorName}/analyze`);
                const data = await res.json();
                if (data.status === 'success') {
                    sectorDetail.value = data.data;
                } else {
                    errorMsg.value = '分析板块失败: ' + (data.message || '未知错误');
                }
            } catch (e) {
                errorMsg.value = '无法连接分析服务: ' + e.message;
            } finally {
                loadingSectorDetail.value = false;
            }
        }

        function closeFundDetail() {
            fundDetail.value = null;
            showRadar.value = false;
            showDca.value = false;
            document.body.style.overflow = '';
        }

        // Deleted Stock/Crypto logic

        // ========== PORTFOLIO ==========
        async function fetchRecommendations() {
            loading.value = true;
            try {
                const res = await fetch(`${API_BASE}/recommend`);
                const data = await res.json();
                recommendations.value = data;
                recommendAiSummary.value = data.ai_summary || '';
                // Fetch predictions as well
                fetchPredictions();
            } catch (e) {
                showError('获取推荐失败: ' + e.message);
            } finally {
                loading.value = false;
            }
        }

        async function fetchPredictions() {
            try {
                const res = await fetch(`${API_BASE}/predict_tomorrow`);
                const data = await res.json();
                if (data.success) {
                    predictions.value = data.results || [];
                }
            } catch (e) {
                console.error('Fetch predictions failed', e);
            }
        }

        function onSearchInput() {
            clearTimeout(searchTimer);
            if (searchQuery.value.trim().length >= 2) {
                searchTimer = setTimeout(() => doSearch(), 300);
            } else {
                searchResults.value = [];
            }
        }

        async function fetchFullList() {
            if (fullFundList.value.length) return;
            try {
                const res = await fetch(`${STORAGE_BASE}/fund_list.json`);
                fullFundList.value = await res.json();
            } catch (e) {
                console.error('Failed to load fund list', e);
            }
        }

        async function handleSearch() {
            const query = searchQuery.value.trim();
            searchInterpretation.value = ''; // Clear previous deep search info
            if (!query) return;

            // Simple keyword match first
            await fetchFullList();
            const filtered = fullFundList.value.filter(f =>
                f.name.includes(query) || f.code.includes(query)
            );

            if (filtered.length > 0) {
                searchResults.value = filtered;
            } else {
                // Fallback to Server Search if local search yields nothing
                searchLoading.value = true;
                try {
                    const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}`);
                    const data = await res.json();
                    // Transform server results to match local structure if needed
                    searchResults.value = (data.results || []).map(r => ({
                        code: r.code,
                        name: r.name,
                        themes: r.themes || [],
                        return_1y: r.return_1y, // Keep return_1y from server
                        score: r.score
                    }));
                } catch (e) {
                    console.error('Server search failed', e);
                } finally {
                    searchLoading.value = false;
                }
            }
        }

        async function handleDeepSearch() {
            const query = searchQuery.value.trim();
            if (!query) return;

            searchLoading.value = true;
            try {
                // 1. Ask AI for semantic filters
                const res = await fetch(`${API_BASE}/search/deep?q=${encodeURIComponent(query)}`);
                const data = await res.json();

                if (!data.success) throw new Error(data.error);
                const filters = data.filters;
                searchInterpretation.value = data.interpretation || '';

                // 2. Load list & Filter locally
                await fetchFullList();
                let results = [...fullFundList.value];

                // Apply Filters (themes, return_1y, max_drawdown)
                if (filters.themes && filters.themes.length) {
                    results = results.filter(f =>
                        filters.themes.some(t => (f.themes || []).includes(t) || f.name.includes(t))
                    );
                }
                if (filters.return_1y) {
                    const { op, val } = filters.return_1y;
                    results = results.filter(f => op === '>' ? f.return_1y > val : f.return_1y < val);
                }
                if (filters.max_drawdown_1y) {
                    const { op, val } = filters.max_drawdown_1y;
                    results = results.filter(f => op === '>' ? (f.max_drawdown_1y || 0) > val : (f.max_drawdown_1y || 0) < val);
                }
                if (filters.sharpe_1y) {
                    const { op, val } = filters.sharpe_1y;
                    results = results.filter(f => op === '>' ? (f.sharpe_1y || 0) > val : (f.sharpe_1y || 0) < val);
                }

                searchResults.value = results.slice(0, 50); // Limit results
            } catch (e) {
                showError('深度搜索失败: ' + e.message);
            } finally {
                searchLoading.value = false;
            }
        }

        function doSearch() {
            handleSearch();
        }

        async function analyzeFundByCode(code) {
            searchLoading.value = true;
            fundDetail.value = null;
            activeFundTab.value = 'brief';

            try {
                // 1. Try Static JSON fetch
                const res = await fetch(`${STORAGE_BASE}/details/${code}.json`);
                if (res.ok) {
                    const data = await res.json();
                    fundDetail.value = data;
                    fundManager.value = data.metrics?.manager || null;
                    fundRanks.value = data.metrics?.ranks || [];
                } else {
                    // 2. Fallback to API if static fails
                    console.warn(`Static data for ${code} not found, falling back to API...`);
                    const apiRes = await fetch(`${API_BASE}/analyze/${code}`);
                    const apiData = await apiRes.json();

                    // Advanced Map API data to V4 detail format
                    const m = apiData.metrics || {};
                    fundDetail.value = {
                        code: apiData.code,
                        name: apiData.name,
                        score: m.score || '--',
                        grade: m.grade || 'C',
                        nav_date: m.nav_date || '',
                        metrics: {
                            ...m,
                            nav: m.latest_nav,
                            change_percent: m.return_1d
                        },
                        chart_data: apiData.chart_data || [],
                        history_nav: apiData.chart_data || [],
                        holdings: apiData.holdings || [],
                        events: apiData.events || [],
                        ai_analysis: apiData.ai_analysis || '',
                        ai_v4_analysis: apiData.ai_v4_analysis || null
                    };
                    fundManager.value = apiData.manager || null;
                    fundRanks.value = apiData.ranks || [];
                }

                // Common follow-up actions
                fetchFundNews(code);
                fetchStructuredAnalysis(code);
                document.body.style.overflow = 'hidden';

            } catch (e) {
                showError('详情加载失败: ' + e.message);
            } finally {
                searchLoading.value = false;
            }
        }

        async function fetchStructuredAnalysis(code) {
            try {
                const res = await fetch(`${API_BASE}/analyze/${code}/v4`);
                const ana = await res.json();
                if (fundDetail.value && fundDetail.value.code === code) {
                    fundDetail.value.v4_analysis = ana;
                }
            } catch (e) {
                console.error('Fetch structured analysis failed', e);
            }
        }

        async function fetchFundNews(code) {
            try {
                const res = await fetch(`${API_BASE}/news/fund/${code}`);
                const data = await res.json();
                if (data.success) {
                    fundNews.value = data.news || [];
                    // If there is AI analysis for news, we could append it or show in News tab
                }
            } catch (e) {
                console.error('Fetch news failed', e);
            }
        }

        async function fetchMarketNews() {
            try {
                const res = await fetch(`${API_BASE}/news/market`);
                const data = await res.json();
                if (data.success) {
                    marketNews.value = data.news || [];
                }
            } catch (e) {
                console.error('Fetch market news failed', e);
            }
        }

        function runDcaSimulation() {
            if (!fundDetail.value?.history_nav?.length) return;

            const history = fundDetail.value.history_nav;
            const amount = 1000; // Weekly 1000
            let totalInvested = 0;
            let totalShares = 0;

            // Simplified: Buy every 5 data points (roughly weekly if daily data)
            for (let i = 0; i < history.length; i += 5) {
                const nav = parseFloat(history[i].nav);
                if (isNaN(nav) || nav <= 0) continue;
                totalShares += amount / nav;
                totalInvested += amount;
            }

            const latestNav = parseFloat(history[history.length - 1].nav);
            const currentValue = totalShares * latestNav;
            const profit = currentValue - totalInvested;
            const yieldRate = (profit / totalInvested) * 100;

            dcaResults.value = {
                totalInvested,
                currentValue,
                profit,
                yield: yieldRate.toFixed(2),
                count: Math.floor(history.length / 5)
            };
        }

        const calculateTotalFee = (amount, years, rate) => {
            // Simple annual compounding fee drag
            return amount * (1 - Math.pow(1 - rate / 100, years));
        };

        // Export search to window for entity links
        window.appSearch = (query) => {
            searchQuery.value = query;
            mode.value = 'search';
            handleSearch();
        };

        async function fetchTopGainers() {
            gainerLoading.value = true;
            try {
                const res = await fetch(`${API_BASE}/top-gainers?period=${gainerPeriod.value}&limit=20`);
                const data = await res.json();
                if (data.success) {
                    topGainers.value = data.data.funds || [];
                }
            } catch (e) {
                console.error(e);
            } finally {
                gainerLoading.value = false;
            }
        }

        async function fetchPortfolio() {
            try {
                const positions = await LocalDB.getAll('portfolio');
                portfolio.value = positions;
                // Local Calculation
                const total_cost = positions.reduce((sum, p) => sum + (p.shares * (p.cost_price || 1)), 0);
                portfolioSummary.value = {
                    total_positions: positions.length,
                    total_cost: total_cost
                };
            } catch (e) {
                console.error(e);
            }
        }

        async function buyFund(code, name) {
            const input = prompt(`请输入买入份额\n基金: ${name || code}`, '1000');
            if (!input) return;
            const shares = parseFloat(input);
            if (isNaN(shares) || shares <= 0) {
                showError('请输入有效份额');
                return;
            }

            try {
                // For static version, we use 1.0 as cost_price if not available
                const cost_price = 1.0;
                await LocalDB.put('portfolio', {
                    fund_code: code,
                    fund_name: name,
                    shares,
                    cost_price,
                    buy_date: new Date().toISOString(),
                    status: 'holding'
                });
                showError('✅ 已记入本地持仓');
                fetchPortfolio();
            } catch (e) {
                showError('保存失败');
            }
        }

        async function sellPosition(positionId) {
            if (!confirm('确定要移除此持仓吗？')) return;
            try {
                await LocalDB.delete('portfolio', positionId);
                showError('✅ 已从本地移除');
                fetchPortfolio();
            } catch (e) {
                showError('操作失败');
            }
        }

        async function fetchWatchlist() {
            watchlistLoading.value = true;
            try {
                const res = await fetch(`${API_BASE}/watchlist/realtime`);
                const data = await res.json();
                if (data.success) {
                    watchlist.value = data.data;
                }
            } catch (e) {
                console.error('Fetch watchlist failed', e);
            } finally {
                watchlistLoading.value = false;
            }
        }

        async function addToWatchlist(code, name) {
            try {
                const res = await fetch(`${API_BASE}/watchlist/add`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code, name })
                });
                const data = await res.json();
                if (data.success) {
                    showError('✅ 已加入自选');
                    fetchWatchlist();
                } else {
                    showError('添加失败: ' + (data.error || ''));
                }
            } catch (e) {
                showError('网络错误');
            }
        }

        let watchlistTimer = null;
        function startWatchlistTimer() {
            stopWatchlistTimer();
            watchlistTimer = setInterval(() => {
                if (mode.value === 'watchlist' && !watchlistLoading.value) {
                    fetchWatchlistSilent();
                }
            }, 30000); // 30 seconds refresh
        }

        function stopWatchlistTimer() {
            if (watchlistTimer) {
                clearInterval(watchlistTimer);
                watchlistTimer = null;
            }
        }

        async function fetchWatchlistSilent() {
            try {
                const res = await fetch(`${API_BASE}/watchlist/realtime`);
                const data = await res.json();
                if (data.success) {
                    watchlist.value = data.data;
                }
            } catch (e) { }
        }

        function generateSparkline(data) {
            if (!data || data.length < 2) return '';
            const width = 400;
            const height = 30;
            const points = data.map(d => d.growth);
            const min = Math.min(...points);
            const max = Math.max(...points);
            const range = max - min || 1;

            return data.map((d, i) => {
                const x = (i / (data.length - 1)) * 100 + '%';
                const y = height - ((d.growth - min) / range * height);
                return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
            }).join(' ');
        }

        async function handlePortfolioDiagnose() {
            if (!portfolio.value.length) return;
            showDiagnosis.value = true;
            diagnosisReport.value = '';
            searchLoading.value = true;
            try {
                const res = await fetch(`${API_BASE}/portfolio/diagnose`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(portfolio.value)
                });
                const data = await res.json();
                if (data.success) {
                    diagnosisReport.value = data.report;
                    // Trigger pro diagnosis as well
                    runDiagnosePro();
                } else {
                    showError('诊断失败: ' + data.error);
                    showDiagnosis.value = false;
                }
            } catch (e) {
                showError('请求失败');
                showDiagnosis.value = false;
            } finally {
                searchLoading.value = false;
            }
        }

        async function runDiagnosePro() {
            loadingDiagnosePro.value = true;
            try {
                const res = await fetch(`${API_BASE}/v1/diagnose/pro`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        funds: portfolio.value.map(p => ({ code: p.fund_code, weight: 100 / portfolio.value.length }))
                    })
                });
                const data = await res.json();
                if (data.status === 'success') {
                    diagnoseProData.value = data.data;
                }
            } catch (e) {
                console.error('Pro diagnosis failed', e);
            } finally {
                loadingDiagnosePro.value = false;
            }
        }

        async function handleExportImage(elementId) {
            const el = document.getElementById(elementId);
            if (!el) return;

            try {
                const canvas = await html2canvas(el, {
                    backgroundColor: '#0f172a',
                    scale: 2,
                    useCORS: true
                });
                const link = document.createElement('a');
                link.download = `FundAdvisor_Report_${new Date().getTime()}.png`;
                link.href = canvas.toDataURL('image/png');
                link.click();
                showError('✅ 已生成分享图并尝试下载');
            } catch (e) {
                showError('生成分享图失败: ' + e.message);
            }
        }

        async function removeFromWatchlist(code) {
            if (!confirm('确定要移除吗？')) return;
            try {
                const res = await fetch(`${API_BASE}/watchlist/remove`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code })
                });
                const data = await res.json();
                if (data.success) {
                    watchlist.value = watchlist.value.filter(f => f.code !== code);
                }
            } catch (e) {
                showError('移除失败');
            }
        }

        async function triggerUpdate() {
            if (!adminToken.value.trim()) {
                updateMessage.value = '请输入 Token';
                updateSuccess.value = false;
                return;
            }

            updating.value = true;
            updateMessage.value = '';
            try {
                const res = await fetch(`${API_BASE}/admin/build-static`, {
                    method: 'POST',
                    headers: { 'X-Admin-Token': adminToken.value.trim() }
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    updateSuccess.value = true;
                    updateMessage.value = data.message || '静态数据构建已启动';
                    setTimeout(() => { showUpdateDialog.value = false; }, 2000);
                } else {
                    updateSuccess.value = false;
                    updateMessage.value = data.detail || data.error || '同步失败';
                }
            } catch (e) {
                updateSuccess.value = false;
                updateMessage.value = '请求失败: ' + e.message;
            } finally {
                updating.value = false;
            }
        }

        async function fetchMarketHotspots() {
            loadingHotspots.value = true;
            try {
                const res = await fetch(`${API_BASE}/v1/market/hotspots`);
                const data = await res.json();
                if (data.status === 'success') {
                    marketHotspots.value = data;
                }
            } catch (e) {
                console.error('Fetch hotspots failed', e);
            } finally {
                loadingHotspots.value = false;
            }
        }

        async function fetchHotSectors() {
            loadingSectors.value = true;
            try {
                const res = await fetch(`${API_BASE}/v1/sectors/hot`);
                const data = await res.json();
                if (data.status === 'success') {
                    hotSectors.value = data.data;
                }
            } catch (e) {
                console.error('Fetch sectors failed', e);
            } finally {
                loadingSectors.value = false;
            }
        }

        async function fetchRankings(tab = 'score') {
            rankTab.value = tab;
            loadingRankings.value = true;
            try {
                // Include filters in ranking fetch
                const queryParams = new URLSearchParams({
                    sort_by: tab,
                    limit: 20
                });
                if (activeFilters.value.scale !== 'all') queryParams.append('min_scale', activeFilters.value.scale);
                if (activeFilters.value.tenure !== 'all') queryParams.append('min_tenure', activeFilters.value.tenure);

                const res = await fetch(`${API_BASE}/v1/rankings?${queryParams.toString()}`);
                const data = await res.json();
                if (data.status === 'success') {
                    rankingListData.value = data.data;
                }
            } catch (e) {
                console.error('Fetch rankings failed', e);
            } finally {
                loadingRankings.value = false;
            }
        }

        async function applyFilters() {
            showFilterDrawer.value = false;
            fetchRankings(rankTab.value);
        }

        async function sendChatMessage() {
            if (!chatInput.value || chatLoading.value) return;

            const query = chatInput.value;
            chatMessages.value.push({ role: 'user', content: query });
            chatInput.value = '';
            chatLoading.value = true;

            try {
                const res = await fetch(`${API_BASE}/v1/ai/chat/query`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query, history: chatMessages.value.slice(-5) })
                });
                const data = await res.json();
                if (data.status === 'success') {
                    chatMessages.value.push({
                        role: 'ai',
                        content: data.interpretation,
                        funds: data.funds
                    });
                    // Auto scroll to bottom
                    setTimeout(() => {
                        const el = document.getElementById('chatMessages');
                        if (el) el.scrollTop = el.scrollHeight;
                    }, 50);
                } else {
                    chatMessages.value.push({ role: 'ai', content: '抱歉，我现在无法解析您的需求，请尝试换一种说法。' });
                }
            } catch (e) {
                chatMessages.value.push({ role: 'ai', content: '连接 AI 服务失败，请稍后重试。' });
            } finally {
                chatLoading.value = false;
            }
        }

        const getSectorIcon = (sector) => {
            const icons = {
                '大消费': '🛒', '白酒': '🍷', '食品饮料': '🍔', '家电': '📺', '美妆': '💄', '旅游酒店': '🏨', '农业养殖': '🐷',
                '医疗保健': '🏥', '医药': '💊', '生物制品': '🧬', '中药': '🌿', '医疗器械': '🩻',
                '科技创新': '🚀', '半导体': '💾', '电子': '📱', '人工智能': '🤖', '软件': '💻', '通信': '📡', '云计算': '☁️',
                '新能源': '⚡', '光伏': '☀️', '锂电池': '🔋', '风电': '🌬️', '电力': '🔌',
                '金融地产': '🏦', '银行': '🏛️', '非银金融': '💹', '房地产': '🏠', '券商': '📊',
                '高端制造': '🏭', '工业': '⚙️', '军工': '🛡️', '基建': '🏗️', '汽车': '🚗',
                '资源能源': '🛢️', '煤炭': '🪵', '有色金属': '💎', '钢铁': '⛓️', '石化': '⛽'
            };
            return icons[sector] || '🏷️';
        };

        // 生命周期
        onMounted(() => {
            fetchRecommendations();
            fetchMarketNews();
            // 初始化 Lucide 图标
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        });

        return {
            renderMarkdown,
            getScoreClass,
            mode, loading, errorMsg,
            recommendations, recTab, recTabs, currentList,
            searchQuery, searchResults, searchLoading, fundDetail,
            topGainers, gainerPeriod, gainerLoading, gainerPeriods,
            portfolio, portfolioSummary,
            watchlist, watchlistLoading,
            showUpdateDialog, adminToken, updating, updateMessage, updateSuccess,
            showError, getScoreClass, renderAIContent, switchMode,
            fetchRecommendations, onSearchInput, doSearch, analyzeFundByCode,
            fetchTopGainers, fetchPortfolio, buyFund, sellPosition,
            fetchWatchlist, addToWatchlist, removeFromWatchlist, triggerUpdate,

            // Deep Dive
            activeFundTab, fundNews, fundManager, fundRanks, closeFundDetail,
            marketNews,
            recommendAiSummary, renderMarkdown,
            fetchStructuredAnalysis,
            scannerTags, handleSearch, handleDeepSearch,
            showDiagnosis, diagnosisReport, handlePortfolioDiagnose,
            handleExportImage, generateSparkline,

            // Professional Features Methods
            macroData,
            fetchMacroData: async () => {
                try {
                    const res = await fetch(`${API_BASE}/macro/dashboard`);
                    macroData.value = (await res.json()).data;
                } catch (e) { console.error(e); }
            },
            backtestResult,
            backtestLoading,
            runBacktest: async (portfolioList) => {
                backtestLoading.value = true;
                try {
                    const res = await fetch(`${API_BASE}/portfolio/backtest`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(portfolioList)
                    });
                    backtestResult.value = await res.json();
                } catch (e) { showError('回测失败'); }
                finally { backtestLoading.value = false; }
            },
            feeCalculator,
            calculateFee: async () => {
                feeCalculator.value.loading = true;
                try {
                    const { amount, years, rate } = feeCalculator.value;
                    const res = await fetch(`${API_BASE}/fee/calculate?amount=${amount}&years=${years}&rate=${rate}`);
                    const data = await res.json();
                    if (data.success) feeCalculator.value.result = data;
                } catch (e) { showError('计算失败'); }
                finally { feeCalculator.value.loading = false; }
            },
            showWiki: (term) => {
                showError(`📖 ${term}: ${wikiTerms[term] || '暂无详细解释'}`);
            },

            // V4 additions
            predictions, getSentimentText, getSentimentColor, dynamicGreeting,
            showRadar, defaultRadar, showDca, dcaResults, runDcaSimulation, calculateTotalFee,
            chartPath, crashMarkers,
            compareList, showPk, toggleCompare,

            // Fund Channel Methods
            marketHotspots, hotSectors, rankingListData, rankTab,
            loadingRankings, loadingHotspots, loadingSectors,
            fetchMarketHotspots, fetchHotSectors, fetchRankings,
            getSectorIcon, openSectorDetail,
            showSectorModal, selectedSector, sectorDetail, loadingSectorDetail,

            // Phase 3 Additions
            compareData, loadingCompare, fetchComparisonMatrix,
            diagnoseProData, loadingDiagnosePro, runDiagnosePro,
            showFilterDrawer, activeFilters, applyFilters,

            // Phase 4 Additions
            showChat, chatInput, chatMessages, chatLoading, sendChatMessage
        };
    }
}).mount('#app');
