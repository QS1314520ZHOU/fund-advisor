
import os
import re

def refactor_index_html():
    path = r'd:\\fund-advisor\\frontend\\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    skip = False
    
    gainers_view_tag = """                <gainers-view
                    v-if="mode === 'gainers'"
                    :gainer-periods="gainerPeriods"
                    v-model:gainer-period="gainerPeriod"
                    :gainer-loading="gainerLoading"
                    :top-gainers="topGainers"
                    :compare-list="compareList"
                    @fetch-top-gainers="fetchTopGainers"
                    @analyze-fund="analyzeFundByCode"
                    @toggle-compare="toggleCompare"
                ></gainers-view>\\n"""

    found_start = False
    found_end = False

    for line in lines:
        if '<template v-if="mode === \'gainers\'">' in line:
            found_start = True
            skip = True
            new_lines.append(gainers_view_tag)
            continue
        
        if skip and '</template>' in line:
            skip = False
            found_end = True
            continue
            
        if not skip:
            new_lines.append(line)
    
    if found_start and found_end:
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print("Successfully refactored index.html for GainersView")
    else:
        print(f"Error: Could not find Gainers template in index.html. Start: {found_start}, End: {found_end}")

def update_app_js():
    path = r'd:\\fund-advisor\\frontend\\js\\app.js'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add import
    if "import GainersView from '../components/GainersView.js';" not in content:
        content = content.replace("import ChannelView from '../components/ChannelView.js';", 
                                 "import ChannelView from '../components/ChannelView.js';\\nimport GainersView from '../components/GainersView.js';")

    # Update components
    if 'GainersView' not in content.split('components: {')[1].split('}')[0]:
        content = content.replace('ChannelView', 'ChannelView,\\n        GainersView')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully updated app.js for GainersView")

if __name__ == "__main__":
    refactor_index_html()
    update_app_js()
