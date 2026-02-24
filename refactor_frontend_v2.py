
import os
import re

def refactor_index_html():
    path = r'd:\fund-advisor\frontend\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace Recommend template
    # Find <template v-if="mode === 'recommend'"> ... </template>
    # Note: There are nested tags, so we need a balanced or specific search.
    # In index.html, it's followed by <!-- ========== 基金频道 ========== -->
    
    start_marker = r'<template v-if="mode === \'recommend\'">'
    end_marker = r'</template>\s+<!-- ========== 基金频道 ========== -->'
    
    recommend_view_tag = """                <recommend-view
                    v-if="mode === 'recommend'"
                    :loading="loading"
                    :recommendations="recommendations"
                    v-model:rec-tab="recTab"
                    :predictions="predictions"
                    :market-news="marketNews"
                    :compare-list="compareList"
                    :render-markdown="renderMarkdown"
                    :get-sentiment-text="getSentimentText"
                    :get-score-class="getScoreClass"
                    @analyze-fund="analyzeFundByCode"
                    @toggle-compare="toggleCompare"
                    @search-query="window.appSearch($event)"
                ></recommend-view>"""

    new_content = re.sub(f'{re.escape(start_marker)}.*?{end_marker}', 
                        f'{recommend_view_tag}\n\n                <!-- ========== 基金频道 ========== -->', 
                        content, flags=re.DOTALL)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Refactored index.html")

def refactor_app_js():
    path = r'd:\fund-advisor\frontend\js\app.js'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add imports at the top
    imports = """import Sidebar from '../components/Sidebar.js';
import RecommendView from '../components/RecommendView.js';
import { 
    getScoreClass, 
    getSentimentText, 
    getSentimentColor, 
    getSectorIcon, 
    renderMarkdown 
} from './utils.js';

"""
    # Remove existing imports if any (like the one I added partially)
    content = re.sub(r'import Sidebar from .*?\n', '', content)
    content = re.sub(r'import RecommendView from .*?\n', '', content)
    
    content = imports + content

    # 2. Update components in createApp
    if 'components: {' not in content:
        content = content.replace('createApp({', 'createApp({\n    components: {\n        Sidebar,\n        RecommendView\n    },')
    else:
        # Update existing components block
        content = re.sub(r'components: \{.*?\}', 'components: {\n        Sidebar,\n        RecommendView\n    }', content, flags=re.DOTALL)

    # 3. Remove utility functions from setup() scope
    # These are: getScoreClass, getSentimentText, getSentimentColor, renderMarkdown, getSectorIcon (if present)
    
    functions_to_remove = [
        r'function getScoreClass\(grade\) \{.*?\}',
        r'function getSentimentText\(val\) \{.*?\}',
        r'function getSentimentColor\(val\) \{.*?\}',
        r'function renderMarkdown\(text\) \{.*?\}'
    ]
    
    for func_re in functions_to_remove:
        content = re.sub(func_re, '', content, flags=re.DOTALL)

    # 4. Make sure these functions are available in setup return or local scope
    # Since they are imported, they are in the file scope. 
    # But setup() needs to return them if they are used in the main template.
    # However, I passed them as props to RecommendView, so they are needed in setup() return or available locally.
    
    # Actually, RecommendView uses them, but index.html might still use some if I haven't refactored all parts.
    # Let's check if they are in return { ... }
    
    # Check return block
    # Note: app.js is large, finding the final return might be tricky with regex.
    # I'll just make sure they are defined as constants if needed.
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Refactored app.js")

if __name__ == "__main__":
    refactor_index_html()
    refactor_app_js()
