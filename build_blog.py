#!/usr/bin/env python3
"""Gera artigos do Decap CMS em HTML estático no deploy Netlify, sem dependências externas."""
from pathlib import Path
from html import escape
from datetime import datetime
import json, re, shutil, unicodedata

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'_site'
SITE='https://niseconsultoria.com.br'

def slugify(s):
    s=''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')

def parse_frontmatter(text):
    if not text.startswith('---'):
        return {},text
    match=re.match(r'^---\s*\n(.*?)\n---\s*\n?',text,re.S)
    if not match:
        return {},text
    data={}
    for line in match.group(1).splitlines():
        m=re.match(r'^([A-Za-z_][\w-]*):\s*(.*)$',line)
        if m:
            val=m.group(2).strip()
            if len(val)>=2 and val[0]==val[-1] and val[0] in '\'"':
                val=val[1:-1]
            data[m.group(1)]=val
    return data,text[match.end():]

def inline(s):
    s=escape(s)
    s=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',lambda m:'<a href="'+escape(m.group(2),quote=True)+'" rel="noopener noreferrer">'+m.group(1)+'</a>',s)
    s=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',s)
    s=re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)',r'<em>\1</em>',s)
    return s

def markdown_html(source):
    lines=source.splitlines(); parts=[]; paragraph=[]; listing=False
    def flush():
        nonlocal paragraph
        if paragraph: parts.append('<p>'+inline(' '.join(paragraph))+'</p>');paragraph=[]
    for line in lines:
        line=line.strip()
        if not line:
            flush()
            if listing:parts.append('</ul>');listing=False
            continue
        if line.startswith('#') and re.match(r'^#{1,6}\s+',line):
            flush()
            if listing:parts.append('</ul>');listing=False
            n=len(line)-len(line.lstrip('#'))
            parts.append(f'<h{n}>{inline(line[n:].strip())}</h{n}>')
        elif re.match(r'^[-*] ',line):
            flush()
            if not listing:parts.append('<ul>');listing=True
            parts.append('<li>'+inline(line[2:])+'</li>')
        else:
            if listing:parts.append('</ul>');listing=False
            paragraph.append(line)
    flush()
    if listing:parts.append('</ul>')
    return '\n'.join(parts)

def fmtdate(value):
    try:return datetime.fromisoformat(value.replace('Z','+00:00')).strftime('%d/%m/%Y')
    except ValueError:return value[:10]

def valid_image(value):
    value=value.strip()
    if value.startswith('/assets/') and not any(c in value for c in '<>"\''):
        return value
    return ''

if OUT.exists():shutil.rmtree(OUT)
OUT.mkdir()
for path in ROOT.iterdir():
    if path.name in {'.git','_site','node_modules','build_blog.py','.github'}:continue
    if path.is_dir():shutil.copytree(path,OUT/path.name,ignore=shutil.ignore_patterns('.DS_Store'))
    elif path.is_file():shutil.copy2(path,OUT/path.name)

posts=[]
for file in sorted((ROOT/'content'/'artigos').glob('*.md')) if (ROOT/'content'/'artigos').exists() else []:
    data,body=parse_frontmatter(file.read_text(encoding='utf-8-sig'))
    title=data.get('title','').strip()
    if not title:continue
    slug=slugify(file.stem) or slugify(title)
    if not slug:continue
    posts.append(dict(slug=slug,title=title,description=data.get('description',''),category=data.get('category','Boletins'),author=data.get('author','Nise Consultoria'),date=data.get('date',''),image=valid_image(data.get('image','')),body=body))
posts.sort(key=lambda p:p['date'],reverse=True)

for p in posts:
    title=escape(p['title']); desc=escape(p['description']); category=escape(p['category']); author=escape(p['author']); date=fmtdate(p['date']); slug=p['slug']
    canonical=f'{SITE}/blog/{slug}/'
    hero=f'<img class="cms-hero" src="{escape(p["image"],quote=True)}" alt="Imagem de destaque: {title}" loading="lazy">' if p['image'] else ''
    ld=json.dumps({'@context':'https://schema.org','@type':'Article','headline':p['title'],'description':p['description'],'author':{'@type':'Organization' if p['author']=='Nise Consultoria' else 'Person','name':p['author']},'publisher':{'@type':'Organization','name':'Nise Consultoria'},'datePublished':p['date'][:10],'mainEntityOfPage':canonical},ensure_ascii=False).replace('</','<\\/')
    page=f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} | Nise Consultoria</title><meta name="description" content="{desc}"><link rel="canonical" href="{canonical}"><link rel="stylesheet" href="../../blog.css"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@500;600&display=swap" rel="stylesheet"><style>.cms-hero{{width:100%;max-height:440px;object-fit:cover;margin:20px 0 32px}}.cms-content{{line-height:1.85;overflow-wrap:anywhere}}.cms-content img{{max-width:100%;height:auto}}.cms-content h2,.cms-content h3{{margin-top:32px}}</style><script type="application/ld+json">{ld}</script></head><body class="blog-body"><header class="blog-nav"><a href="../../index.html"><img src="../../assets/logo.jpg" alt="Nise Consultoria"></a><nav class="blog-nav-links"><a href="../../index.html">Início</a><a href="../index.html">Blog</a><a class="gold-btn" href="https://wa.me/5563999361650">Falar com a Nise ↗</a></nav></header><main class="blog-wrap"><a class="blog-back" href="../index.html">← Todos os conteúdos</a><div class="article-layout"><article class="article-main"><div class="blog-eyebrow" style="margin-top:35px">{category}</div><h1>{title}</h1><p class="intro">{desc}</p><p class="blog-meta">Por {author} · {escape(date)}</p>{hero}<div class="cms-content">{markdown_html(p['body'])}</div><a class="blog-cta" href="https://wa.me/5563999361650">Falar com a Nise Consultoria ↗</a></article><aside class="article-aside"><div class="blog-eyebrow">Nise Consultoria</div><h2>Informação para decidir melhor.</h2><p>Atendimento contábil e tributário em Palmas/TO e on-line.</p><a href="https://wa.me/5563999361650">Solicitar atendimento ↗</a></aside></div></main><footer class="blog-footer">Nise Consultoria · Palmas/TO · <a href="../index.html">Voltar ao Blog</a></footer></body></html>'''
    folder=OUT/'blog'/slug
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'index.html').write_text(page,encoding='utf-8')

blog_file=OUT/'blog'/'index.html'
html=blog_file.read_text(encoding='utf-8')
# Os artigos novos aparecem antes dos exemplos sem destruir a estrutura editorial existente.
cards=[]
for p in posts:
    cat=slugify(p['category']); keys=' '.join([cat,'boletins' if 'bolet' in cat else '', 'reforma' if 'reforma' in cat else '', 'simples' if 'simples' in cat else '', 'gestao' if 'gestao' in cat else '', 'contabilidade' if 'contabil' in cat else '']).strip()
    title=escape(p['title']); desc=escape(p['description']); author=escape(p['author']); date=escape(fmtdate(p['date']))
    pic=f'<div class="pic cms-card-pic"><img src="..{escape(p["image"],quote=True)}" alt="{title}" loading="lazy"></div>' if p['image'] else ''
    cards.append(f'<article class="ecard" data-cat="{escape(keys,quote=True)}" data-search="{escape(p["title"]+" "+p["description"]+" "+p["category"],quote=True)}">{pic}<div class="body"><span class="tag">{escape(p["category"])}</span><h3>{title}</h3><p>{desc}</p><div class="meta">{author} · {date}</div><a href="{p["slug"]}/index.html">Ler artigo →</a></div></article>')
needle='<div class="cards" id="cards">'
if needle not in html:raise RuntimeError('Não foi possível localizar #cards no blog/index.html')
# Reforço visual apenas para imagens enviadas pelo CMS: preserva a arte inteira,
# sem cortar textos ou elementos importantes, mantendo todos os cards com a mesma altura.
cms_style='''<style id="cms-card-image-fix">
.cms-card-pic{height:255px;background:#f3efe6;display:flex;align-items:center;justify-content:center;overflow:hidden}
.cms-card-pic img{width:100%;height:100%;object-fit:contain;object-position:center;display:block}
@media(max-width:700px){.cms-card-pic{height:auto;aspect-ratio:16/9}}
.cms-article-title{font-size:clamp(2.5rem,4.2vw,4.5rem);line-height:1.05;letter-spacing:-0.02em}
.cms-article-description{font-size:1.35rem;line-height:1.5;max-width:900px;white-space:normal;overflow:visible;text-overflow:clip}
@media(max-width:700px){.cms-article-title{font-size:2.5rem}.cms-article-description{font-size:1.1rem}}
</style>'''
if 'cms-card-image-fix' not in html:
    html=html.replace('</head>',cms_style+'\n</head>',1)

# `posts` já está ordenado por data em ordem decrescente. Como o bloco é inserido
# imediatamente após #cards, o conteúdo mais recente do CMS aparece primeiro.
html=html.replace(needle,needle+'\n'+'\n'.join(cards),1)
blog_file.write_text(html,encoding='utf-8')

sitemap=OUT/'sitemap.xml'
if sitemap.exists():
    original=sitemap.read_text(encoding='utf-8')
    entries=''.join(f'<url><loc>{SITE}/blog/{p["slug"]}/</loc></url>' for p in posts)
    sitemap.write_text(original.replace('</urlset>',entries+'</urlset>'),encoding='utf-8')
print(f'Build concluído: {len(posts)} artigo(s) do Decap CMS gerados em _site/blog/.')
