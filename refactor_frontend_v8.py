
import os
import re

def refactor_index_html():
    path = r'd:\\fund-advisor\\frontend\\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Search View
    search_view_tag = """                <search-view
                    v-if="mode === 'search'"
                    v-model:search-query="searchQuery"
                    :search-loading="searchLoading"
                    :scanner-tags="scannerTags"
                    :search-interpretation="searchInterpretation"
                    :search-results="searchResults"
                    :compare-list="compareList"
                    @handle-search="handleSearch"
                    @handle-deep-search="handleDeepSearch"
                    @analyze-fund="analyzeFundByCode"
                    @toggle-compare="toggleCompare"
                ></search-view>"""
    
    # Portfolio View
    portfolio_view_tag = """                <portfolio-view
                    v-if="mode === 'portfolio'"
                    :portfolio="portfolio"
                    :portfolio-summary="portfolioSummary"
                    :search-loading="searchLoading"
                    :backtest-loading="backtestLoading"
                    :backtest-result="backtestResult"
                    v-model:show-diagnosis="showDiagnosis"
                    :diagnosis-report="diagnosisReport"
                    :diagnose-pro-data="diagnoseProData"
                    :loading-diagnose-pro="loadingDiagnosePro"
                    :render-markdown="renderMarkdown"
                    @handle-portfolio-diagnose="handlePortfolioDiagnose"
                    @handle-export-image="handleExportImage"
                    @fetch-portfolio="fetchPortfolio"
                    @analyze-fund="analyzeFundByCode"
                    @sell-position="sellPosition"
                    @run-backtest="runBacktest"
                ></portfolio-view>"""

    # Watchlist View
    watchlist_view_tag = """                <watchlist-view
                    v-if="mode === 'watchlist'"
                    :watchlist-loading="watchlistLoading"
                    :watchlist="watchlist"
                    :generate-sparkline="generateSparkline"
                    @fetch-watchlist="fetchWatchlist"
                    @analyze-fund="analyzeFundByCode"
                    @remove-from-watchlist="removeFromWatchlist"
                    @switch-mode="mode = $event"
                ></watchlist-view>"""

    # Macro View
    macro_view_tag = """                <macro-view
                    v-if="mode === 'macro'"
                    :macro-data="macroData"
                    @fetch-macro-data="fetchMacroData"
                ></macro-view>"""

    # Tools View
    tools_view_tag = """                <tools-view
                    v-if="mode === 'tools'"
                    :fee-calculator="feeCalculator"
                    @calculate-fee="calculateFee"
                ></tools-view>"""

    # Replace Search
    content = re.sub(r'<template v-if="mode === \'search\'">.*?</template>', search_view_tag, content, flags=re.DOTALL)
    # Replace Portfolio
    content = re.sub(r'<template v-if="mode === \'portfolio\'">.*?</template>', portfolio_view_tag, content, flags=re.DOTALL)
    # Replace Watchlist
    content = re.sub(r'<template v-if="mode === \'watchlist\'">.*?</template>', watchlist_view_tag, content, flags=re.DOTALL)
    # Replace Macro
    content = re.sub(r'<template v-if="mode === \'macro\'">.*?</template>', macro_view_tag, content, flags=re.DOTALL)
    # Replace Tools
    content = re.sub(r'<template v-if="mode === \'tools\'">.*?</template>', tools_view_tag, content, flags=re.DOTALL)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully refactored index.html for multiple views")

def update_app_js():
    path = r'd:\\fund-advisor\\frontend\\js\\app.js'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add imports
    imports = [
        "import SearchView from '../components/SearchView.js';",
        "import PortfolioView from '../components/PortfolioView.js';",
        "import WatchlistView from '../components/WatchlistView.js';",
        "import MacroView from '../components/MacroView.js';",
        "import ToolsView from '../components/ToolsView.js';"
    ]
    
    last_import = "import FundDetailModal from '../components/FundDetailModal.js';"
    for imp in imports:
        if imp not in content:
            content = content.replace(last_import, last_import + "\\n" + imp)
            last_import = imp

    # Update components
    components = ["SearchView", "PortfolioView", "WatchlistView", "MacroView", "ToolsView"]
    for comp in components:
        if comp not in content:
            content = content.replace('FundDetailModal', 'FundDetailModal,\\n        ' + comp)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully updated app.js for multiple views")

if __name__ == "__main__":
    refactor_index_html()
    update_app_js()
