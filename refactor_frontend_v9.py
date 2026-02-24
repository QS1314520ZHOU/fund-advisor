
import os
import re

def refactor_index_html():
    path = r'd:\\fund-advisor\\frontend\\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # PK Modal Tag
    pk_modal_tag = """                <pk-modal
                    v-model:show-pk="showPk"
                    :loading-compare="loadingCompare"
                    :compare-data="compareData"
                    :get-score-class="getScoreClass"
                ></pk-modal>"""
    
    # Filter Drawer Tag
    filter_drawer_tag = """                <filter-drawer
                    v-model:show-filter-drawer="showFilterDrawer"
                    v-model:active-filters="activeFilters"
                    @apply-filters="applyFilters"
                ></filter-drawer>"""

    # AIChatPanel Tag
    ai_chat_panel_tag = """                <ai-chat-panel
                    v-model:show-chat="showChat"
                    :chat-messages="chatMessages"
                    v-model:chat-input="chatInput"
                    :chat-loading="chatLoading"
                    :render-markdown="renderMarkdown"
                    :get-score-class="getScoreClass"
                    @send-message="sendChatMessage"
                    @analyze-fund="analyzeFundByCode"
                ></ai-chat-panel>"""

    # Replace PK Modal
    content = re.sub(r'<!-- PK Modal -->.*?<div class="deep-dive-overlay".*?v-if="showPk".*?</div>\s+</div>\s+</div>', pk_modal_tag, content, flags=re.DOTALL)
    
    # Replace Filter Drawer
    content = re.sub(r'<!-- Filter Drawer -->.*?<div class="filter-drawer".*?</div>\s+</div>', filter_drawer_tag, content, flags=re.DOTALL)
    
    # Replace AI Chat Panel
    content = re.sub(r'<!-- Floating AI Toggle -->.*?<!-- AI Chat Assistant \(Phase 4\) -->.*?<div class="chat-panel".*?</div>\s+</div>\s+</div>', ai_chat_panel_tag, content, flags=re.DOTALL)

    # Simplified regex for the targets in the current file state
    # Actually, the file state after v8 is quite different. 
    # Let's use more specific patterns based on the last view_file output.

    # PK Modal
    content = re.sub(r'<div class="deep-dive-overlay".*?v-if="showPk".*?</div>\s+</div>\s+</div>', pk_modal_tag, content, flags=re.DOTALL)
    # Filter Drawer
    content = re.sub(r'<div class="filter-drawer".*?</div>\s+</div>', filter_drawer_tag, content, flags=re.DOTALL)
    # AI Chat Panel
    content = re.sub(r'<!-- Floating AI Toggle -->.*?<div class="chat-panel".*?</div>\s+</div>\s+</div>', ai_chat_panel_tag, content, flags=re.DOTALL)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully refactored index.html for final system components")

def update_app_js():
    path = r'd:\\fund-advisor\\frontend\\js\\app.js'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add imports
    imports = [
        "import PKModal from '../components/PKModal.js';",
        "import FilterDrawer from '../components/FilterDrawer.js';",
        "import AIChatPanel from '../components/AIChatPanel.js';"
    ]
    
    last_import = "import ToolsView from '../components/ToolsView.js';"
    for imp in imports:
        if imp not in content:
            content = content.replace(last_import, last_import + "\\n" + imp)
            last_import = imp

    # Update components
    components = ["PKModal", "FilterDrawer", "AIChatPanel"]
    for comp in components:
        if comp not in content:
            content = content.replace('ToolsView', 'ToolsView,\\n        ' + comp)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully updated app.js for final system components")

if __name__ == "__main__":
    refactor_index_html()
    update_app_js()
