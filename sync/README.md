# Afik back-office data sync

The back-office lives at https://afik-yozmot.netlify.app/admin (Google sign-in, allow-listed accounts only).
Its revenue/cash-flow data is one Firestore document: `private/finance` (project atomichabits-df13b), readable only by the allow-listed accounts.

- `parse_sheet.py sheet.xlsx > months.json` — reads "חשבוניות כללית.xlsx" (Drive id 1hDMnl-OLhiLrDDRPAtUeBGtiv8OVrxM7), one tab per month.
- `build_finance.py months.json nipendo.json [bank.json] > finance.json` — merges Nipendo statuses and the optional bank summary.

nipendo.json shape: `{"date":"DD/MM/YYYY","invoices":{"<proforma no>":{"status","desc","total","pay","order","buyer","tx"}}}`
bank.json shape: `{"asOf","kpis":[{label,value,sub,tone}],"fixed":[{name,amount,note}],"insights":[...]}`

The document is written from the signed-in admin page in the owner's browser:
`await window._fbFns.setDoc(window._fbFns.doc(window._db,'private','finance'), DATA)`
