#!/usr/bin/env python3
"""静的LP（index.html）を、会社HP（WordPress）の固定ページ /denkaeru/ 用に分けて出力する。

出力
- wordpress/denkaeru-content.html   … 固定ページ「denkaeru」の本文（<!-- wp:html --> の中に本文HTMLだけ）
- wordpress/denkaeru-tokushoho.html … 子ページ /denkaeru/tokushoho/ の本文
- wordpress/denkaeru-cf7-form.txt   … Contact Form 7 のフォーム定義
- <会社HP>/src/lp/denkaeru.css|js   … デザインと動き（テーマが /denkaeru/ を開いたときだけ読み込む）
- <会社HP>/src/lp/denkaeru/img/     … 写真・ロゴ（テーマに同梱）

使い方: python3 build_wp.py --form-id <CF7のID>
関東版（/denkaeru/kanto/）の本文だけ: python3 build_kanto.py && python3 build_wp.py --form-id <CF7のID> --page kanto
サーバーのWAFが本文の <script / <style / /* を拒否するため、本文には入れない。
CSS/JS/画像を変えたら会社HPテーマのリリース（DEPLOYMENT.md）が必要。本文だけなら固定ページの更新でよい。
"""
import argparse
import pathlib
import re
import shutil
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / 'wordpress'
CORP = pathlib.Path('/Users/toshi/Desktop/AI REMOTO/CODEX/leoforce-corporate-redesign')
SLUG = 'denkaeru'
SITE = 'https://leoforce.co.jp'
IMG_URL = f'{SITE}/wp-content/themes/leoforce/assets/lp/{SLUG}/img/'
FONTS = ('@import url("https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@500;700;900'
         '&family=Noto+Sans+JP:wght@400;500;700&family=IBM+Plex+Mono:wght@500;600&display=swap");\n')

ap = argparse.ArgumentParser()
ap.add_argument('--form-id', required=True, help='Contact Form 7 のフォームID')
ap.add_argument('--page', choices=['tokyo', 'kanto'], default='tokyo',
                help='kanto: kanto.html から /denkaeru/kanto/ の本文だけを書き出す（CSS/JS/画像は東京版と共通）')
args = ap.parse_args()

html = (HERE / ('kanto.html' if args.page == 'kanto' else 'index.html')).read_text(encoding='utf-8')
css = re.search(r'<style>(.*?)</style>', html, re.S).group(1).strip()
js = re.search(r'<script>(.*?)</script>', html, re.S).group(1).strip()
body = re.search(r'<body>(.*?)<script>', html, re.S).group(1).strip()

# 本文：画像・リンク・フォームを WordPress 用に置き換える
body = re.sub(r'(src|srcset)="img/', rf'\1="{IMG_URL}', body)
body = body.replace('href="tokushoho.html"', f'href="{SITE}/{SLUG}/tokushoho/"')
body = body.replace('href="privacy.html"', f'href="{SITE}/privacy-policy/"')
body, n = re.subn(r'<form class="form" id="form".*?</form>',
                  f'<div id="form">[contact-form-7 id="{args.form_id}" html_class="form"]</div>', body, flags=re.S)
assert n == 1, 'フォームが見つかりません'
left = re.findall(r'(?:src|srcset|href)="((?:img/|[\w-]+\.html)[^"]*)"', body)
if left:
    raise SystemExit('ローカル参照が残っています: ' + ', '.join(sorted(set(left))))
if re.search(r'<script|<style|/\*', body, re.I):
    raise SystemExit('本文に <script / <style / /* が含まれています（WAFで保存できません）')

OUT.mkdir(exist_ok=True)
if args.page == 'kanto':
    out = OUT / f'{SLUG}-kanto-content.html'
    out.write_text('<!-- wp:html -->\n' + body + '\n<!-- /wp:html -->\n', encoding='utf-8')
    print(f'本文: {out} ({out.stat().st_size:,} bytes)')
    raise SystemExit(0)
(OUT / f'{SLUG}-content.html').write_text('<!-- wp:html -->\n' + body + '\n<!-- /wp:html -->\n', encoding='utf-8')

# 特商法：本文の <dl> だけを子ページへ
legal = (HERE / 'tokushoho.html').read_text(encoding='utf-8')
rows = re.findall(r'<dt>(.*?)</dt><dd>(.*?)</dd>', re.search(r'<dl>.*?</dl>', legal, re.S).group(0), re.S)
table = '\n'.join(f'<tr><th>{k}</th><td>{v}</td></tr>' for k, v in rows)
(OUT / f'{SLUG}-tokushoho.html').write_text('<!-- wp:html -->\n<figure class="wp-block-table"><table><tbody>\n' + table
    + '\n</tbody></table></figure>\n<p><a href="' + SITE + '/' + SLUG + '/">デンカエルのパワコン交換へ戻る</a></p>\n<!-- /wp:html -->\n', encoding='utf-8')

# Contact Form 7 のフォーム定義（見た目は index.html の .form と同じクラスを使う）
makers = re.search(r'<select id="f-maker" name="maker">(.*?)</select>', html, re.S).group(1)
makers = ' '.join(f'"{m}"' for m in re.findall(r'<option>(.*?)</option>', makers))
states = ' '.join(f'"{t}"' for t in re.findall(r'name="s" value="[^"]+">([^<]+)</label>', html))
note_ph = re.search(r'<textarea id="f-note" name="note" placeholder="([^"]+)"', html).group(1)
cf7 = f'''<h3>フォームでのご相談（無料）</h3>
<div class="two"><label>お名前<span class="req">必須</span>[text* your-name autocomplete:name]</label><label>電話番号<span class="req">必須</span>[tel* tel autocomplete:tel]</label></div>
<div class="two"><label>郵便番号<span class="req">必須</span>[text* zip autocomplete:postal-code placeholder "例 1770041"]</label><label>パワコンのメーカー[select maker {makers}]</label></div>
<fieldset><legend>いまの状態（いくつでも）</legend><div class="chips2">[checkbox state use_label_element {states}]</div></fieldset>
<label>ご相談内容（任意）[textarea note placeholder "{note_ph}"]</label>
[hidden lf-source]
<p class="agree">送信すると、<a href="{SITE}/privacy-policy/">個人情報の取り扱い</a>に同意したものとみなします。営業目的のお電話を繰り返すことはありません。</p>
[submit class:btn class:btn-tel "この内容で相談する（無料）"]'''
(OUT / f'{SLUG}-cf7-form.txt').write_text(cf7 + '\n', encoding='utf-8')

# テーマ側：CSS・JS・画像
dst = CORP / 'src' / 'lp'
(dst / f'{SLUG}.css').write_text(FONTS + css + '\n', encoding='utf-8')
(dst / f'{SLUG}.js').write_text(js + '\n', encoding='utf-8')
img_dst = dst / SLUG / 'img'
if img_dst.exists():
    shutil.rmtree(img_dst)
(img_dst / 'logos').mkdir(parents=True)
for p in (HERE / 'img').rglob('*'):
    if not p.is_file():
        continue
    out = img_dst / p.relative_to(HERE / 'img')
    if p.suffix.lower() == '.jpg':
        # テーマZIPを軽くするため、JPEGは画質80で書き出す（解像度はそのまま）
        subprocess.run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', '80', str(p), '--out', str(out)],
                       check=True, capture_output=True)
    else:
        shutil.copy2(p, out)

size = sum(p.stat().st_size for p in img_dst.rglob('*') if p.is_file())
print(f'本文: {OUT / (SLUG + "-content.html")} ({(OUT / (SLUG + "-content.html")).stat().st_size:,} bytes)')
print(f'テーマ: {dst / (SLUG + ".css")} / {SLUG}.js / {SLUG}/img ({size / 1e6:.1f} MB)')
