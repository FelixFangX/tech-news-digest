#!/usr/bin/env python3
"""Targeted repair for 2026-05-11 failures"""
import os, yaml, re, json, time, requests
from pathlib import Path

os.chdir(Path(__file__).parent.parent)

with open(os.path.expanduser('~/.hermes/config.yaml')) as f:
    config = yaml.safe_load(f)
for p in config.get('custom_providers', []):
    if p.get('name') == 'dee-seek':
        API_KEY = p['api_key']
        BASE_URL = p['base_url']
        MODEL = p['model']
        break

filepath = 'daily/2026-05-11.md'
with open(filepath) as f:
    content = f.read()

positions = [(m.start(), m.end()) for m in re.finditer('（深度分析生成失败）', content)]
print(f'Found {len(positions)} failures')

fixed = 0
for pos, endpos in reversed(positions):
    section_start = content.rfind('\n### ', 0, pos)
    if section_start == -1:
        section_start = content.rfind('\n## ', 0, pos)
    title_line_start = section_start + 5
    title_line_end = content.find('\n', title_line_start)
    title = content[title_line_start:title_line_end].strip()
    
    abs_match = re.search(r'- \*\*摘要\*\*: (.+?)(?:\n|$)', content[section_start:pos])
    abstract = abs_match.group(1)[:300] if abs_match else 'N/A'
    
    prompt = f"""[0] Title: {title[:200]} | Abstract: {abstract[:200]}

Output one JSON:
{{"id": 0, "title_zh": "Chinese title", "deep_analysis": "Deep analysis (max 80 chars)", "application_scenarios": ["scene1", "scene2"]}}"""
    
    try:
        resp = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'},
            json={'model': MODEL, 'messages': [
                {'role': 'system', 'content': 'Output only valid JSON. No markdown, no explanation.'},
                {'role': 'user', 'content': prompt}
            ], 'max_tokens': 4096, 'temperature': 0.7},
            timeout=60
        )
        raw = resp.json()['choices'][0]['message'].get('content', '').strip()
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        parsed = json.loads(raw)
        
        da = parsed.get('deep_analysis', '')
        scenes = ' · '.join(parsed.get('application_scenarios', [])[:4])
        
        failure_line = content.find('（深度分析生成失败）', max(0, pos-10))
        line_end = content.find('\n', failure_line)
        new_line = f'- **🔍 深度分析**: {da}'
        if scenes:
            new_line += f'\n- **🎯 落地场景**: {scenes}'
        
        content = content[:failure_line] + new_line + content[line_end:]
        fixed += 1
        print(f'  OK: {title[:60]}')
    except Exception as e:
        print(f'  FAIL: {title[:50]} -> {e}')
    
    time.sleep(1)

with open(filepath, 'w') as f:
    f.write(content)

remaining = len(re.findall('（深度分析生成失败）', content))
print(f'\nDone: {fixed}/{len(positions)} fixed, {remaining} remaining')
