from pathlib import Path
import csv
import json
import re
import shutil
import subprocess
import zipfile

repo = Path('/tmp/echarts-examples')
out = Path('ECharts_365个简洁单图提示词')
if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)

categories = [
    'line','bar','pie','scatter','map','candlestick','radar','boxplot','heatmap','graph',
    'lines','tree','treemap','sunburst','parallel','sankey','funnel','gauge','pictorialBar',
    'themeRiver','calendar','matrix','chord','custom','dataset','dataZoom','graphic','rich',
    'globe','bar3D','scatter3D','surface','map3D','lines3D','line3D','scatterGL','linesGL',
    'flowGL','graphGL'
]
cn = {
    'line':'折线图','bar':'柱状图','pie':'饼图','scatter':'散点图','map':'地图','candlestick':'K线图',
    'radar':'雷达图','boxplot':'箱线图','heatmap':'热力图','graph':'关系图','lines':'路径图','tree':'树图',
    'treemap':'矩形树图','sunburst':'旭日图','parallel':'平行坐标图','sankey':'桑基图','funnel':'漏斗图',
    'gauge':'仪表盘','pictorialBar':'象形柱图','themeRiver':'主题河流图','calendar':'日历图','matrix':'矩阵图',
    'chord':'和弦图','custom':'自定义图','dataset':'数据集组件','dataZoom':'数据缩放','graphic':'图形组件',
    'rich':'富文本','globe':'三维地球','bar3D':'三维柱状图','scatter3D':'三维散点图','surface':'三维曲面图',
    'map3D':'三维地图','lines3D':'三维路径图','line3D':'三维折线图','scatterGL':'大规模散点图',
    'linesGL':'大规模路径图','flowGL':'流场图','graphGL':'大规模关系图'
}
official = set(categories)
black = {
    'lines-airline','scatter-world-population','geo3d','geo3d-with-different-height',
    'globe-country-carousel','globe-with-echarts-surface','map3d-alcohol-consumption',
    'map3d-wood-map','scattergl-weibo','heatmap-bmap','effectScatter-bmap','lines-bmap',
    'lines-bmap-bus','lines-bmap-effect','map-bin','global-wind-visualization',
    'global-wind-visualization-2'
}

registry = repo / 'src/data/chart-list-data.js'
node_script = r'''
const fs = require('fs');
const p = process.argv[1];
let code = fs.readFileSync(p, 'utf8');
code = code.replace(/\bexport\s+default\s+/, 'module.exports = ');
const moduleObj = {exports:{}};
new Function('module','exports',code)(moduleObj,moduleObj.exports);
process.stdout.write(JSON.stringify(moduleObj.exports));
'''
raw = subprocess.check_output(['node','-e',node_script,str(registry)], text=True)
core = json.loads(raw)

examples = {}
for item in core:
    eid = item.get('id')
    if not eid or item.get('noExplore') or eid in black:
        continue
    cats = [c for c in item.get('category',[]) if c in official]
    if not cats:
        continue
    examples[eid] = {
        'id': eid,
        'title': item.get('title') or item.get('titleCN') or eid,
        'titleCN': item.get('titleCN') or '',
        'categories': cats
    }

# ECharts-GL examples are not included in the core registry; read their metadata headers.
gl_root = repo / 'public/examples/ts/gl'
field_re = re.compile(r'^\s*([A-Za-z][A-Za-z0-9_]*)\s*:\s*(.*?)\s*$', re.M)
if gl_root.exists():
    for path in sorted(list(gl_root.rglob('*.js')) + list(gl_root.rglob('*.ts'))):
        text = path.read_text(encoding='utf-8', errors='replace')
        m = re.match(r'\s*/\*(.*?)\*/', text, re.S)
        if not m:
            continue
        meta = {k:v.strip().strip("'\"") for k,v in field_re.findall(m.group(1))}
        eid = path.stem
        cats = [x.strip() for x in re.split(r'[,\s]+', meta.get('category','')) if x.strip() in official]
        if not cats or eid in black or meta.get('noExplore','').lower() == 'true':
            continue
        examples[eid] = {
            'id': eid,
            'title': meta.get('title') or meta.get('titleCN') or eid,
            'titleCN': meta.get('titleCN') or '',
            'categories': cats
        }

def safe_name(s, maxlen=145):
    s = re.sub(r'[\\/:*?"<>|\x00-\x1f]', '_', str(s))
    s = re.sub(r'\s+', ' ', s).strip().strip('.')
    return (s[:maxlen] or 'unnamed')

records = []
combined = ['# ECharts 简洁单图提示词汇总', '']
for cat_index, cat in enumerate(categories, 1):
    folder_name = f'{cat_index:02d}_{cat}_{cn[cat]}'
    folder = out / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    members = sorted((e for e in examples.values() if cat in e['categories']), key=lambda x:x['id'])
    for e in members:
        dataset_file = safe_name(f"{e['id']}__{e['title']}") + '.xlsx'
        dataset_path = f'ECharts_39类全量纯净Excel数据集_一图一文件/{folder_name}/{dataset_file}'
        chart_name = e['titleCN'] or e['title']
        prompt = f'请使用技能 echarts-master，读取数据集“{dataset_path}”，生成“{chart_name}”图表。'
        prompt_file = safe_name(f"{e['id']}__{e['title']}__提示词") + '.md'
        (folder / prompt_file).write_text(prompt + '\n', encoding='utf-8')
        combined.extend([f"## {len(records)+1:03d}. {cat}｜{e['id']}｜{chart_name}", '', prompt, ''])
        records.append({
            '序号': len(records)+1,
            '分类': cat,
            '分类中文': cn[cat],
            '示例ID': e['id'],
            '图表名称': chart_name,
            '数据集': dataset_path,
            '提示词文件': f'{folder_name}/{prompt_file}',
            '提示词': prompt
        })

(out / '00_全部简洁提示词汇总.md').write_text('\n'.join(combined), encoding='utf-8')
with (out / '00_简洁提示词目录.csv').open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(records[0].keys()))
    w.writeheader()
    w.writerows(records)

counts = {c:sum(1 for r in records if r['分类']==c) for c in categories}
expected_counts = {
    'line':40,'bar':46,'pie':19,'scatter':30,'map':16,'candlestick':10,'radar':5,'boxplot':4,
    'heatmap':5,'graph':13,'lines':1,'tree':7,'treemap':7,'sunburst':7,'parallel':4,'sankey':7,
    'funnel':4,'gauge':12,'pictorialBar':8,'themeRiver':2,'calendar':9,'matrix':13,'chord':4,
    'custom':20,'dataset':9,'dataZoom':5,'graphic':5,'rich':3,'globe':8,'bar3D':12,'scatter3D':6,
    'surface':11,'map3D':2,'lines3D':4,'line3D':1,'scatterGL':1,'linesGL':1,'flowGL':1,'graphGL':3
}
mismatches = {c:{'actual':counts[c],'expected':expected_counts[c]} for c in categories if counts[c] != expected_counts[c]}
validation = {'unique_examples':len(examples),'prompt_files':len(records),'counts':counts,'mismatches':mismatches}
(out / 'VALIDATION.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
readme = [
    'ECharts 简洁单图提示词', '',
    '每个提示词只包含：使用技能 echarts-master、读取指定Excel数据集、生成指定图表。',
    f'唯一示例数：{len(examples)}',
    f'按分类归档提示词数：{len(records)}', '',
    '提示词格式：',
    '请使用技能 echarts-master，读取数据集“数据集路径”，生成“图表名称”图表。'
]
(out / 'README.txt').write_text('\n'.join(readme)+'\n',encoding='utf-8')

zip_path = Path('ECharts_365个简洁单图提示词.zip')
if zip_path.exists():
    zip_path.unlink()
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in out.rglob('*'):
        if p.is_file():
            z.write(p,p.relative_to(out.parent))
with zipfile.ZipFile(zip_path) as z:
    bad = z.testzip()
    if bad:
        raise SystemExit('Corrupted zip member: '+bad)
print(json.dumps(validation,ensure_ascii=False))
print(f'ZIP={zip_path} SIZE={zip_path.stat().st_size}')
