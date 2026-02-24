
import os
import re

def refactor_index_html():
    path = r'd:\\fund-advisor\\frontend\\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    fund_detail_modal_tag = """                <!-- Fund Detail Modal -->
                <fund-detail-modal
                    :fund-detail="fundDetail"
                    v-model:active-fund-tab="activeFundTab"
                    :get-score-class="getScoreClass"
                    v-model:show-radar="showRadar"
                    :default-radar="defaultRadar"
                    :render-ai-content="renderAIContent"
                    :chart-path="chartPath"
                    :crash-markers="crashMarkers"
                    :fund-ranks="fundRanks"
                    v-model:show-dca="showDca"
                    :dca-results="dcaResults"
                    :calculate-total-fee="calculateTotalFee"
                    :fund-manager="fundManager"
                    :fund-news="fundNews"
                    :render-markdown="renderMarkdown"
                    @close="closeFundDetail"
                    @run-dca-simulation="runDcaSimulation"
                    @buy-fund="buyFund"
                    @add-to-watchlist="addToWatchlist"
                    @analyze-fund="analyzeFundByCode"
                ></fund-detail-modal>\\n"""

    # Look for the Fund Deep Dive Overlay section
    pattern = re.compile(r'<!-- ========== Fund Deep Dive Overlay ========== -->.*?<transition name="fade">.*?<div v-if="fundDetail" class="deep-dive-overlay">.*?</transition>', re.DOTALL)
    
    if pattern.search(content):
        content = pattern.sub("<!-- ========== Fund Deep Dive Overlay ========== -->\\n" + fund_detail_modal_tag, content)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Successfully refactored index.html for FundDetailModal")
    else:
        print("Error: Could not find Fund Detail Modal block using regex")

def update_app_js():
    path = r'd:\\fund-advisor\\frontend\\js\\app.js'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add import
    if "import FundDetailModal from '../components/FundDetailModal.js';" not in content:
        content = content.replace("import SectorModal from '../components/SectorModal.js';", 
                                 "import SectorModal from '../components/SectorModal.js';\\nimport FundDetailModal from '../components/FundDetailModal.js';")

    # Update components
    if 'FundDetailModal' not in content:
        content = content.replace('SectorModal', 'SectorModal,\\n        FundDetailModal')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully updated app.js for FundDetailModal")

if __name__ == "__main__":
    refactor_index_html()
    update_app_js()
