#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
养基宝 持仓数据抓取 + 分析汇总
使用已保存的 Token 调用 browser-plug-api 获取个人持仓、账户汇总、指数行情。

依赖: pip install requests
用法:
  python yjb_fetch.py          # 获取全部数据
  python yjb_fetch.py --json  # 另存为 JSON 文件
  python yjb_fetch.py --csv   # 导出持仓为 CSV
"""
import os, sys

# 养基宝 API 签名密钥（建议通过环境变量 YJB_SECRET 配置）
SECRET = os.environ.get('YJB_SECRET', 'YxmKSrQR4uoJ5lOoWIhcbd7SlUEh9OOc')

import requests, hashlib, time, json, csv
from datetime import datetime

BASE = 'http://browser-plug-api.yangjibao.com'
TOKEN_FILE = os.path.expanduser('~/.yjb_token.json')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_token():
    if not os.path.exists(TOKEN_FILE):
        print('未找到 Token，请先运行 yjb_login.py 扫码登录')
        sys.exit(1)
    with open(TOKEN_FILE, encoding='utf-8') as f:
        return json.load(f).get('token')


def make_headers(path, token):
    sign_path = path.split('?')[0]
    t = int(time.time())
    s = hashlib.md5(
        (sign_path + token + str(t) + SECRET).encode()
    ).hexdigest()
    return {'Request-Time': str(t), 'Request-Sign': s, 'Authorization': token}


def api_get(path, token):
    r = requests.get(BASE + path, headers=make_headers(path, token), timeout=15)
    if r.status_code != 200:
        raise Exception(f'HTTP {r.status_code}: {r.text[:100]}')
    d = r.json()
    if d.get('code') != 200:
        raise Exception(d.get('message', f'API error code={d.get("code")}'))
    return d.get('data', {})


def fmt_money(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def arrow(val):
    v = fmt_money(val)
    if v > 0:
        return '🟢'
    if v < 0:
        return '🔴'
    return '⚪'


def pct(money, earn):
    m, e = fmt_money(money), fmt_money(earn)
    if m - e <= 0:
        return '—'
    return f'{(e / (m - e) * 100):+.1f}%'


def main():
    import argparse
    parser = argparse.ArgumentParser(description='养基宝持仓数据抓取')
    parser.add_argument('--json', action='store_true', help='导出 JSON')
    parser.add_argument('--csv', action='store_true', help='导出 CSV')
    args = parser.parse_args()

    token = load_token()
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    sep = '=' * 60

    print(sep)
    print('  养基宝 个人持仓分析')
    print(f'  时间: {now}')
    print(sep)

    all_data = {}

    # === 1. 账户汇总 ===
    try:
        collect = api_get('/account_collect', token)
        acc_list = collect.get('account_data', [])
        all_data['account_collect'] = collect
        print('\n 账户汇总')
        for a in acc_list:
            title = a.get('title', '?')
            cost = fmt_money(a.get('hold_cost'))
            income = fmt_money(a.get('today_income'))
            rate = a.get('today_income_rate', '0')
            print(f'  {title}: 持仓成本 {cost:.2f}  {arrow(income)}今日 {income:+.2f} ({rate}%)')
    except Exception as e:
        print(f'  [跳过] 账户汇总: {e}')

    # === 2. 指数行情 ===
    try:
        print('\n 主要指数')
        idx = api_get('/index_data', token)
        items = idx if isinstance(idx, list) else idx.get('list', [])
        all_data['index_data'] = items
        for item in items[:12]:
            name = item.get('name') or item.get('show_name', '?')
            price = item.get('v') or item.get('price', '-')
            try:
                change = float(item.get('dir') or item.get('change') or 0)
            except (TypeError, ValueError):
                change = 0.0
            print(f'  {arrow(change)} {name}: {price}  {change:+.2f}%')
    except Exception as e:
        print(f'  [跳过] 指数行情: {e}')

    # === 3. 持仓明细 ===
    try:
        print('\n 持仓明细')
        accounts = api_get('/user_account', token).get('list', [])
        all_data['accounts'] = accounts

        grand_total = 0.0
        grand_earn = 0.0
        all_holdings = []

        for acc in accounts:
            aid = acc['id']
            atitle = acc['title']
            data = api_get(f'/fund_hold?account_id={aid}', token)
            items = data if isinstance(data, list) else data.get('list', [])
            all_holdings.append({'_account': atitle, 'items': items})

            if not items:
                print(f'\n  [{atitle}] (空)')
                continue

            # 优先按市值降序
            items_sorted = sorted(
                items,
                key=lambda x: fmt_money(x.get('money') or x.get('market_value')),
                reverse=True
            )

            acc_money = 0.0
            acc_earn = 0.0
            print(f'\n  [{atitle}] ({len(items)}只)')

            for item in items_sorted:
                name  = item.get('name') or item.get('short_name') or item.get('fund_name') or '?'
                code  = item.get('code', '?')
                money = fmt_money(item.get('money') or item.get('market_value'))
                earn  = fmt_money(item.get('earn') or item.get('hold_earn') or item.get('total_earn'))
                share = item.get('share') or item.get('hold_share') or '—'
                cost  = item.get('cost') or item.get('hold_cost') or '—'
                acc_money += money
                acc_earn  += earn

                print(f'    {arrow(earn)} {name}({code})')
                print(f'        市值 {money:.2f}  盈亏 {earn:+.2f} ({pct(money, earn)})  份额:{share}  成本:{cost}')

            print(f'    {"-" * 42}')
            print(f'    小计 {acc_money:.2f}  盈亏 {arrow(acc_earn)}{acc_earn:+.2f}')
            grand_total += acc_money
            grand_earn  += acc_earn

        all_data['all_holdings'] = all_holdings

        print(f'\n{sep}')
        if grand_total - grand_earn > 0:
            total_pct = grand_earn / (grand_total - grand_earn) * 100
            print(f'  总持仓 {grand_total:.2f}  总盈亏 {arrow(grand_earn)}{grand_earn:+.2f}  ({total_pct:+.1f}%)')
        else:
            print(f'  总持仓 {grand_total:.2f}')
        print(sep)

    except Exception as e:
        print(f'\n持仓获取失败: {e}')
        import traceback; traceback.print_exc()

    # === 导出 ===
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    if args.json:
        out_path = os.path.join(SCRIPT_DIR, f'yjb_data_{ts}.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2, default=str)
        print(f'\nJSON 已保存: {out_path}')

    if args.csv:
        out_path = os.path.join(SCRIPT_DIR, f'yjb_holdings_{ts}.csv')
        with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f)
            w.writerow(['账户', '基金名称', '代码', '市值', '盈亏', '盈亏率%', '份额', '成本单价'])
            for acc_h in all_holdings:
                at = acc_h['_account']
                for item in acc_h['items']:
                    money = fmt_money(item.get('money') or item.get('market_value'))
                    earn  = fmt_money(item.get('earn') or item.get('hold_earn') or 0)
                    w.writerow([
                        at,
                        item.get('name') or item.get('short_name') or '',
                        item.get('code', ''),
                        f'{money:.2f}', f'{earn:+.2f}',
                        pct(money, earn),
                        item.get('share') or item.get('hold_share') or '',
                        item.get('cost') or item.get('hold_cost') or '',
                    ])
        print(f'CSV 已保存: {out_path}')


if __name__ == '__main__':
    main()
