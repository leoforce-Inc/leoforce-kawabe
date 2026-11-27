#!/usr/bin/env python3
"""東京版LP（index.html）から、関東全域向けの kanto.html を作る。

東京都の補助金は東京だけの制度で、他県は対象外や時期限定が多い。
そのため関東版では補助金を訴求せず、工事費込みの総額・無料点検・メーカー保証で見せる。
デザイン・CSS・JSは東京版と同じ（WordPress では /denkaeru/kanto/ が同じ assets/lp/denkaeru.css|js を読む）。

使い方: python3 build_kanto.py   → kanto.html
WordPress 用の本文は: python3 build_wp.py --form-id 1484 --page kanto
"""
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
html = (HERE / 'index.html').read_text(encoding='utf-8')

FROG = '<svg aria-hidden="true"><use href="#frog"/></svg>'

# (置き換え前, 置き換え後)。どれも東京版にちょうど1回だけ出てくること
REPLACE = [
    ('<meta name="description" content="デンカエルのパワコン交換。東京都内の戸建て専門、全メーカー対応。工事費込みの総額表示、写真3枚で当日見積もり、止まる前の無料点検も受付。東京都の補助金（最大10万円/台）の申請代行。">',
     '<meta name="description" content="デンカエルのパワコン交換。関東全域（東京・神奈川・埼玉・千葉・茨城・栃木・群馬）の戸建てに対応、全メーカー対応。工事費・撤去処分費込みの総額表示、写真3枚で当日見積もり、止まる前の無料点検も受付。">'),
    ('<title>太陽光のパワコン交換｜デンカエル</title>',
     '<title>太陽光のパワコン交換｜関東全域対応｜デンカエル</title>'),
    ('<div class="ribbon"><div class="in">令和8年度 東京都のパワコン交換補助金 受付中｜最大10万円／台（予算に達し次第終了）　<a href="#subsidy">詳しく</a></div></div>',
     '<div class="ribbon"><div class="in">東京・神奈川・埼玉・千葉・茨城・栃木・群馬の戸建てに対応しています</div></div>'),
    ('<span>東京都内の戸建て住宅 専門</span>', '<span>関東全域の戸建て住宅に対応</span>'),
    ('写真3枚を送るだけで、補助金を引いた「総額」をその日のうちにお知らせします。',
     '写真3枚を送るだけで、工事費・処分費込みの「総額」をその日のうちにお知らせします。'),
    ('<span class="ml">補助金申請</span><b>代行0円</b>', '<span class="ml">写真見積もり</span><b>当日回答</b>'),
    ('<div class="row"><span class="was">総額 <span class="num">308,000</span>円</span><span class="was">→ 都の補助金で 実質</span></div>\n'
     '        <span class="now">208,000<small>円〜</small></span>\n'
     f'        <div class="help">{FROG}補助金の申請は、まるごとおまかせください。</div>',
     '<div class="row"><span class="was">工事費・撤去処分費 込みの総額</span></div>\n'
     '        <span class="now">308,000<small>円〜</small></span>\n'
     f'        <div class="help">{FROG}写真見積もり・点検は無料です。</div>'),
    ('<li>交換時期の目安と、補助金の見込みのご案内</li>', '<li>交換時期の目安のご案内</li>'),
    ('本体・工事・撤去処分まで込み。補助金を引いた後の金額も書面でお渡しします。',
     '本体・工事・撤去処分まで込みの金額を、書面でお渡しします。'),
    ('<span class="was">総額 <span class="num">308,000</span>円</span><span class="now">補助金で 実質 <span class="num">208,000</span>円〜</span>',
     '<span class="was">本体・工事・撤去処分 込み</span><span class="now">総額 <span class="num">308,000</span>円〜</span>'),
    ('<span class="was">総額 <span class="num">495,000</span>円</span><span class="now">補助金で 実質 <span class="num">395,000</span>円〜</span>',
     '<span class="was">本体・工事・撤去処分 込み</span><span class="now">総額 <span class="num">495,000</span>円〜</span>'),
    ('<br>※補助金は東京都の要件を満たす場合に交付されます。交付は工事後の申請手続きを経てからになります。', ''),
    ('発電の状態と、交換が必要になる時期の目安、補助金の見込みをお伝えします。',
     '発電の状態と、交換が必要になる時期の目安をお伝えします。'),
    ('<details><summary>補助金は必ずもらえますか？</summary><div class="a">東京都の要件を満たす場合に交付されます。現地確認の際に対象になるかを確認し、見積書に補助金の見込み額を記載します。予算の上限に達すると受付が終了することがあります。</div></details>',
     '<details><summary>補助金は使えますか？</summary><div class="a">お住まいの自治体や時期によって、使える補助金がある場合とない場合があります。現地確認の際に確認し、使える場合は申請の手続きもお手伝いします。</div></details>'),
]
# 丸ごと外すブロック（正規表現、1回だけ）
REMOVE = [
    r'\n    <div class="sim" id="sim">.*?\n    </div>\n  </div>\n</section>',   # 補助金のかんたん計算（</section> は残す）
    r'<section class="band white" id="subsidy">.*?</section>\n',              # 東京都の補助金のセクション
]

for old, new in REPLACE:
    n = html.count(old)
    if n != 1:
        raise SystemExit(f'{n}回見つかりました（1回のはず）: {old[:60]}')
    html = html.replace(old, new)

html, n = re.subn(REMOVE[0], '\n  </div>\n</section>', html, count=1, flags=re.S)
assert n == 1, '計算ブロックが見つかりません'
html, n = re.subn(REMOVE[1], '', html, count=1, flags=re.S)
assert n == 1, '補助金セクションが見つかりません'

body = html[html.find('<body>'):html.find('<script>')]
left = [w for w in ('補助金で', '都の補助金', '東京都の補助金', '#subsidy', 'id="sim"', '208,000', '395,000', '都内') if w in body]
if left:
    raise SystemExit('東京向けの表記が残っています: ' + ', '.join(left))

(HERE / 'kanto.html').write_text(html, encoding='utf-8')
print(f'kanto.html ({len(html):,} 文字)')
