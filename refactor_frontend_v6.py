
import os
import re

def refactor_index_html():
    path = r'd:\\fund-advisor\\frontend\\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    skip = False
    
    sector_modal_tag = """                <!-- Sector Modal -->
                <sector-modal
                    v-model:show-sector-modal="showSectorModal"
                    :selected-sector="selectedSector"
                    :get-sector-icon="getSectorIcon"
                    :sector-detail="sectorDetail"
                    :loading-sector-detail="loadingSectorDetail"
                    :render-markdown="renderMarkdown"
                    @analyze-fund="analyzeFundByCode"
                    @search-by-theme="searchByTheme"
                ></sector-modal>\\n"""

    found_start = False
    found_end = False

    for line in lines:
        if '<!-- ========== Sector Deep Dive Modal ========== -->' in line:
            found_start = True
            skip = True
            new_lines.append(sector_modal_tag)
            continue
        
        if skip and '</div>' in line and '</div>' in lines[lines.index(line)+1] and 'fund-advisor' not in line: 
            # This logic is a bit brittle, let's use a better marker
            pass

    # Re-reading to use a more robust regex-based approach for the template block
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = re.compile(r'<!-- ========== Sector Deep Dive Modal ========== -->.*?<div v-if="showSectorModal".*?</div>\s+</div>\s+</div>', re.DOTALL)
    if pattern.search(content):
        content = pattern.sub(sector_modal_tag, content)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Successfully refactored index.html for SectorModal using regex")
    else:
        print("Error: Could not find Sector Modal block using regex")

def update_app_js():
    path = r'd:\\fund-advisor\\frontend\\js\\app.js'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add import
    if "import SectorModal from '../components/SectorModal.js';" not in content:
        content = content.replace("import GainersView from '../components/GainersView.js';", 
                                 "import GainersView from '../components/GainersView.js';\\nimport SectorModal from '../components/SectorModal.js';")

    # Update components
    if 'SectorModal' not in content:
        content = content.replace('GainersView', 'GainersView,\\n        SectorModal')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully updated app.js for SectorModal")

if __name__ == "__main__":
    refactor_index_html()
    update_app_js()
