"""Parse 'חשבוניות כללית.xlsx' into monthly invoice data for the Afik back-office.
usage: python3 parse_sheet.py sheet.xlsx > months.json"""
import sys, json, re, datetime, openpyxl

HEB = ['ינואר','פברואר','מרץ','אפריל','מאי','יוני','יולי','אוגוסט','ספטמבר','אוקטובר','נובמבר','דצמבר']
SHORT = ['ינו','פבר','מרץ','אפר','מאי','יוני','יולי','אוג','ספט','אוק','נוב','דצמ']

def month_of(ws, idx_hint):
    # title like "הכנסות כללית ספטמבר 2026" / "הכנסות כללית - נובמבר 25"
    for row in ws.iter_rows(min_row=1, max_row=4, values_only=True):
        for v in row:
            if isinstance(v, str) and 'הכנסות' in v:
                for i, m in enumerate(HEB):
                    if m in v:
                        y = re.search(r'(20\d\d|\b\d\d\b)', v.split(m, 1)[1])
                        if y:
                            yy = int(y.group(1)); yy = yy + 2000 if yy < 100 else yy
                            return yy, i + 1
    t = ws.title
    for i, m in enumerate(HEB):
        if t.startswith(m):
            y = re.search(r'\d+', t); yy = int(y.group()) + 2000
            return yy, i + 1
    return None

def colmap(header):
    m = {}
    for j, h in enumerate(header):
        if not isinstance(h, str): continue
        h = h.strip()
        if h == 'תאריך': m['d'] = j
        elif 'מרפאה' in h: m['c'] = j
        elif 'מבצע' in h: m['p'] = j
        elif 'חשבונית' in h: m['n'] = j
        elif 'הזמנת' in h: m['o'] = j
        elif 'הצעת' in h: m['q'] = j
        elif 'מה בוצע' in h: m['w'] = j
        elif 'לפני מע' in h: m['a'] = j
        elif h == 'הכנסות' and 'a' not in m: m['a'] = j
    return m

def fmt_date(v):
    if v is None: return ''
    if isinstance(v, datetime.datetime): return '%d.%d' % (v.day, v.month)
    if isinstance(v, float): return ('%g' % v)
    s = str(v).strip()
    s = re.sub(r'\.(\d\d|20\d\d)$', '', s) if s.count('.') == 2 else s
    return s

def num(v):
    if isinstance(v, (int, float)): return float(v)
    try: return float(str(v).replace(',', '').replace('₪', '').strip())
    except Exception: return None

def parse(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    months = {}
    for k, ws in enumerate(wb.worksheets):
        if ws.title.strip() == 'הכנסות': continue
        ym = month_of(ws, k)
        if not ym: continue
        rows = list(ws.iter_rows(min_row=1, max_row=min(ws.max_row, 400), values_only=True))
        hi = next((i for i, r in enumerate(rows) if any(isinstance(v, str) and v.strip() == 'תאריך' for v in r)), None)
        if hi is None: continue
        m = colmap(rows[hi])
        if 'a' not in m: continue
        inv = []; sheet_total = None
        for r in rows[hi + 1:]:
            if any(isinstance(v, str) and v.strip().startswith('סה') for v in r[:3]):
                t = num(r[m['a']]) if m['a'] < len(r) else None
                if t: sheet_total = round(t)
                continue
            a = num(r[m['a']]) if m['a'] < len(r) else None
            if not a: continue
            g = lambda key: (r[m[key]] if key in m and m[key] < len(r) else None)
            if isinstance(g('c'), str) and 'סה' in g('c'): continue
            if isinstance(g('d'), str) and 'סה' in g('d'): continue
            n = g('n')
            if not g('d') and not g('c') and not n:  # total row without label
                if sheet_total is None: sheet_total = round(a)
                continue
            inv.append({
                'd': fmt_date(g('d')), 'c': (g('c') or '').strip() if isinstance(g('c'), str) else (str(g('c')) if g('c') else ''),
                'p': (g('p') or '').strip() if isinstance(g('p'), str) else '',
                'n': str(int(n)) if isinstance(n, (int, float)) else (str(n).strip() if n else ''),
                'o': str(int(g('o'))) if isinstance(g('o'), (int, float)) else '',
                'w': (g('w') or '').strip() if isinstance(g('w'), str) else '',
                'a': round(a, 2)})
        if not inv: continue
        key = '%04d-%02d' % ym
        rows_sum = round(sum(x['a'] for x in inv))
        months[key] = {'key': key, 'label': SHORT[ym[1]-1] + ' ' + str(ym[0])[2:],
                       'total': sheet_total if sheet_total is not None else rows_sum,
                       'rowsSum': rows_sum, 'inv': inv}
    return [months[k] for k in sorted(months)]

if __name__ == '__main__':
    print(json.dumps(parse(sys.argv[1]), ensure_ascii=False))
