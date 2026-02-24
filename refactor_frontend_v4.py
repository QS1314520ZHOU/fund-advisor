
import os
import re

def refactor_index_html():
    path = r'd:\\fund-advisor\\frontend\\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    skip = False
    
    channel_view_tag = """                <channel-view
                    v-if="mode === 'channel'"
                    :market-hotspots="marketHotspots"
                    :rank-tab="rankTab"
                    :ranking-list-data="rankingListData"
                    :hot-sectors="hotSectors"
                    :loading-rankings="loadingRankings"
                    :loading-hotspots="loadingHotspots"
                    :loading-sectors="loadingSectors"
                    :get-sector-icon="getSectorIcon"
                    :get-score-class="getScoreClass"
                    @open-sector-detail="openSectorDetail"
                    @analyze-fund="analyzeFundByCode"
                    @fetch-rankings="fetchRankings"
                ></channel-view>\\n"""

    found_start = False
    found_end = False

    for line in lines:
        if '<template v-if="mode === \'channel\'">' in line:
            found_start = True
            skip = True
            new_lines.append(channel_view_tag)
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
        print("Successfully refactored index.html for ChannelView")
    else:
        print(f"Error: Could not find Channel template in index.html. Start: {found_start}, End: {found_end}")

def update_app_js():
    path = r'd:\\fund-advisor\\frontend\\js\\app.js'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add import
    if "import ChannelView from '../components/ChannelView.js';" not in content:
        content = content.replace("import RecommendView from '../components/RecommendView.js';", 
                                 "import RecommendView from '../components/RecommendView.js';\\nimport ChannelView from '../components/ChannelView.js';")

    # Update components
    if 'ChannelView' not in content.split('components: {')[1].split('}')[0]:
        content = content.replace('RecommendView', 'RecommendView,\\n        ChannelView')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully updated app.js for ChannelView")

if __name__ == "__main__":
    refactor_index_html()
    update_app_js()
