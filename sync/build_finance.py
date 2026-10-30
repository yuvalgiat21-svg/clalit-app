"""Combine sheet months + Nipendo snapshot (+ optional bank summary) into the finance document.
usage: python3 build_finance.py months.json nipendo_snapshot.json [bank.json] > finance.json"""
import sys, json, datetime

def dmy(s):
    try: return datetime.datetime.strptime(s, '%d/%m/%Y').date()
    except Exception: return None

months = json.load(open(sys.argv[1], encoding='utf-8'))
nip = json.load(open(sys.argv[2], encoding='utf-8-sig')) if len(sys.argv) > 2 and sys.argv[2] != '-' else None
bank = json.load(open(sys.argv[3], encoding='utf-8-sig')) if len(sys.argv) > 3 else None
today = datetime.date.today()

inv_map = (nip or {}).get('invoices', {})
for m in months:
    for i in m['inv']:
        x = inv_map.get(i.get('n', ''))
        if x:
            i['s'] = x.get('status', ''); i['pay'] = x.get('pay', '')

nipendo = None
if nip:
    by = {}; exp = {}; att = []
    for num, x in inv_map.items():
        st = x.get('status', ''); tot = float(x.get('total') or 0)
        b = by.setdefault(st, {'count': 0, 'total': 0}); b['count'] += 1; b['total'] += tot
        pd = dmy(x.get('pay', ''))
        if st in ('אושרה', 'שולמה') and pd and pd >= today:
            e = exp.setdefault(x['pay'], {'date': x['pay'], 'total': 0, 'count': 0}); e['total'] += tot; e['count'] += 1
        tx = dmy(x.get('tx', ''))
        if st == 'נדחתה':
            att.append({'n': num, 'why': 'נדחתה – ' + (x.get('desc') or ''), 'total': tot, 'buyer': x.get('buyer', '')})
        elif st == 'ממתינה' and tx and (today - tx).days > 21:
            att.append({'n': num, 'why': 'ממתינה יותר מ-3 שבועות', 'total': tot, 'buyer': x.get('buyer', '')})
        elif st == 'אושרה' and not x.get('pay'):
            att.append({'n': num, 'why': 'אושרה בלי תאריך תשלום', 'total': tot, 'buyer': x.get('buyer', '')})
    for b in by.values(): b['total'] = round(b['total'])
    expected = sorted(exp.values(), key=lambda e: dmy(e['date']))
    for e in expected: e['total'] = round(e['total'])
    nipendo = {'asOf': nip.get('date', ''), 'byStatus': by, 'expected': expected, 'attention': att}

notes = []
for m in months:
    if m.get('rowsSum') is not None and m['rowsSum'] != m['total']:
        notes.append('בגיליון של %s שורת הסה"כ (%s ₪) שונה מסכום השורות (%s ₪) – כדאי לבדוק את נוסחת הסיכום.' % (m['label'], format(m['total'], ','), format(m['rowsSum'], ',')))

out = {'updated': datetime.datetime.now().strftime('%d.%m.%Y %H:%M'), 'months': months,
       'nipendo': nipendo, 'bank': bank, 'notes': notes, 'v': 2}
print(json.dumps(out, ensure_ascii=False))
