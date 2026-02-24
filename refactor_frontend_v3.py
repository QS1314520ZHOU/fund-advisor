
import os
import re

def refactor_index_html():
    path = r'd:\fund-advisor\frontend\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    skip = False
    
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
                ></recommend-view>\n"""

    found_start = False
    found_end = False

    for line in lines:
        if '<template v-if="mode === \'recommend\'">' in line:
            found_start = True
            skip = True
            new_lines.append(recommend_view_tag)
            continue
        
        if skip and '</template>' in line:
            # Check if this is the end of the recommend template
            # It should be shortly after the market news section
            # We skip until we see the template end
            skip = False
            found_end = True
            continue
            
        if not skip:
            new_lines.append(line)
    
    if found_start and found_end:
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print("Successfully refactored index.html")
    else:
        print(f"Error: Could not find templates in index.html. Start: {found_start}, End: {found_end}")

def cleanup_app_js():
    path = r'd:\fund-advisor\frontend\js\app.js'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Double check if utils are already imported
    if "from './utils.js'" not in content:
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
        content = imports + content

    # Clean up duplicate functions if they exist inside setup()
    # Using non-greedy regex to match the body of the functions
    functions_to_remove = [
        r'function getScoreClass\(grade\) \{.*?\}',
        r'function getSentimentText\(val\) \{.*?\}',
        r'function getSentimentColor\(val\) \{.*?\}',
        r'function renderMarkdown\(text\) \{.*?\}'
    ]
    
    for func_re in functions_to_remove:
        content = re.sub(func_re, '', content, flags=re.DOTALL)

    # Ensure utility functions are returned from setup()
    # Find the setup() return block
    # This is complex because of nested braces. 
    # For now, let's just make sure they are available in scope.
    # Actually, as module globals they are available to setup() logic, 
    # but the template needs them. So they MUST be in the return { ... }
    
    # Let's find 'return {' and add them if missing
    if 'return {' in content:
        for val in ['getScoreClass', 'getSentimentText', 'getSentimentColor', 'getSectorIcon', 'renderMarkdown']:
            if val not in content.split('return {')[1]:
                content = content.replace('return {', f'return {{\n                    {val},')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully cleaned up app.js")

if __name__ == "__main__":
    refactor_index_html()
    cleanup_app_js()
