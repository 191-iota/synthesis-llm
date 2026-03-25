import json
import html as h
from datetime import datetime

def render(topic_reports, output_path="index.html"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    js_data = json.dumps(topic_reports, ensure_ascii=False)

    page = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Strategic Briefing</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Sora:wght@300;400;600;800&display=swap');

*, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }

:root {
  --bg: #07090e;
  --surface: #0d1119;
  --surface-2: #141924;
  --border: #1c2235;
  --border-hi: #2a3350;
  --text: #8890a8;
  --text-mid: #5c6380;
  --text-bright: #d0d5e4;
  --text-white: #eef0f7;
  --accent: #3b82f6;
  --accent-soft: rgba(59,130,246,0.08);
  --crit: #ef4444;
  --crit-soft: rgba(239,68,68,0.07);
  --crit-med: rgba(239,68,68,0.18);
  --warn: #eab308;
  --warn-soft: rgba(234,179,8,0.07);
  --warn-med: rgba(234,179,8,0.18);
  --good: #10b981;
  --good-soft: rgba(16,185,129,0.07);
  --info: #818cf8;
  --info-soft: rgba(129,140,248,0.07);
}

html { background: var(--bg); }
body {
  font-family: 'Sora', sans-serif;
  color: var(--text);
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}

/* ===== LAYOUT ===== */
.shell {
  max-width: 900px;
  margin: 0 auto;
  padding: 2.5rem 1.5rem 6rem;
}

/* ===== HEADER ===== */
.hdr { margin-bottom: 2rem; }
.hdr h1 {
  font-weight: 800; font-size: 1.5rem;
  color: var(--text-white);
  letter-spacing: -0.04em;
}
.hdr-sub {
  font-family: 'DM Mono', monospace;
  font-size: 0.62rem; color: var(--text-mid);
  margin-top: 0.35rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

/* ===== TOPIC PILLS ===== */
.topics { display: flex; gap: 0.35rem; margin-bottom: 2rem; flex-wrap: wrap; }
.tpill {
  font-family: 'Sora'; font-weight: 600; font-size: 0.75rem;
  padding: 0.4rem 1rem; border-radius: 99px;
  border: 1px solid var(--border);
  background: var(--surface); color: var(--text);
  cursor: pointer; transition: all 0.2s;
}
.tpill:hover { border-color: var(--accent); }
.tpill.on { background: var(--accent-soft); border-color: var(--accent); color: var(--accent); }

/* ===== RISK BANNER ===== */
.risk {
  padding: 1rem 1.3rem;
  border-radius: 12px;
  border-left: 3px solid;
  margin-bottom: 2.5rem;
  font-size: 0.9rem;
  line-height: 1.65;
  color: var(--text-bright);
}
.risk.critical { background: var(--crit-soft); border-color: var(--crit); }
.risk.warning { background: var(--warn-soft); border-color: var(--warn); }
.risk.on_track { background: var(--good-soft); border-color: var(--good); }
.risk.unknown { background: var(--accent-soft); border-color: var(--accent); }
.risk-label {
  font-family: 'DM Mono', monospace;
  font-size: 0.58rem; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.1em;
  margin-bottom: 0.35rem;
  display: flex; align-items: center; gap: 0.45rem;
}
.risk-label .dot {
  width: 7px; height: 7px; border-radius: 50%;
}
.risk.critical .dot { background: var(--crit); }
.risk.warning .dot { background: var(--warn); }
.risk.on_track .dot { background: var(--good); }
.risk.unknown .dot { background: var(--accent); }
.risk.critical .risk-label { color: #fca5a5; }
.risk.warning .risk-label { color: #fcd34d; }
.risk.on_track .risk-label { color: #6ee7b7; }
.risk.unknown .risk-label { color: #93c5fd; }

/* ===== NEXT ACTION (hero) ===== */
.next-action {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.9rem 1.8rem;
  margin-bottom: 3rem;
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,0.15);
}
.next-action::before {
  content: '';
  position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: var(--na-color, var(--crit));
}
.na-eyebrow {
  font-family: 'DM Mono', monospace;
  font-size: 0.58rem; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.12em;
  color: var(--crit);
  margin-bottom: 0.6rem;
}
.na-title {
  font-weight: 700; font-size: 1.2rem;
  color: var(--text-white);
  line-height: 1.4;
  margin-bottom: 0.55rem;
}
.na-detail {
  font-size: 0.88rem; color: var(--text);
  line-height: 1.65;
}
.na-date {
  font-family: 'DM Mono', monospace;
  font-size: 0.68rem; color: var(--text-mid);
  margin-top: 0.6rem;
}

/* ===== SECTION HEADERS ===== */
.sec-hdr {
  font-family: 'DM Mono', monospace;
  font-size: 0.85rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--text-bright);
  margin-bottom: 1.2rem;
  padding-bottom: 0.6rem;
  border-bottom: 1px solid var(--border);
}

/* ===== VERTICAL TIMELINE ===== */
.timeline {
  position: relative;
  margin-bottom: 3.5rem;
  padding-left: 80px;
}

/* The vertical track */
.timeline::before {
  content: '';
  position: absolute;
  left: 68px; top: 0; bottom: 0;
  width: 2px;
  background: var(--border);
}

/* TODAY line */
.tl-today {
  position: relative;
  padding: 0.6rem 0;
  margin-bottom: 0.2rem;
}
.tl-today::before {
  content: '';
  position: absolute;
  left: -81px; right: 0;
  top: 50%;
  height: 1px;
  background: linear-gradient(90deg, var(--accent), rgba(59,130,246,0.1));
}
.tl-today-label {
  font-family: 'DM Mono', monospace;
  font-size: 0.6rem; font-weight: 500;
  color: var(--accent);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  background: var(--bg);
  padding: 0.15rem 0.5rem;
  position: relative;
  display: inline-block;
}
.tl-today-dot {
  position: absolute;
  left: -17px; top: 50%;
  transform: translate(-50%, -50%);
  width: 10px; height: 10px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 10px rgba(59,130,246,0.3);
}

/* Timeline item */
.tl-item {
  position: relative;
  padding: 0.15rem 0 1.2rem 0;
}

/* The dot on the track */
.tl-dot {
  position: absolute;
  left: -16px; top: 8px;
  transform: translateX(-50%);
  width: 8px; height: 8px;
  border-radius: 50%;
  border: 2px solid var(--bg);
  z-index: 2;
}
.tl-dot.high { background: var(--crit); box-shadow: 0 0 8px var(--crit-med); }
.tl-dot.medium { background: var(--warn); box-shadow: 0 0 8px var(--warn-med); }
.tl-dot.low { background: var(--good); }
.tl-dot.info { background: var(--info); }

/* Date label (to the left of the track) */
.tl-date {
  position: absolute;
  right: calc(100% + 22px);
  top: 4px;
  width: 70px;
  text-align: right;
  font-family: 'DM Mono', monospace;
  font-size: 0.62rem;
  color: var(--text-mid);
  line-height: 1.3;
  white-space: nowrap;
}
.tl-date .tl-rel {
  display: block;
  font-size: 0.55rem;
  margin-top: 0.1rem;
}
.tl-date .tl-rel.done { color: var(--good); }
.tl-date .tl-rel.behind { color: var(--crit); }
.tl-date .tl-rel.soon { color: var(--warn); }

/* Item card on the timeline */
.tl-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1rem 1.2rem;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
  box-shadow: 0 1px 6px rgba(0,0,0,0.14);
}
.tl-card:hover {
  border-color: var(--border-hi);
  background: var(--surface-2);
  box-shadow: 0 2px 10px rgba(0,0,0,0.22);
}
.tl-card-title {
  font-weight: 600; font-size: 0.9rem;
  color: var(--text-bright);
  line-height: 1.4;
}
.tl-card-badges {
  display: flex; gap: 0.4rem; margin-top: 0.4rem;
  flex-wrap: wrap; align-items: center;
}
.badge {
  font-family: 'DM Mono', monospace;
  font-size: 0.58rem; font-weight: 500;
  padding: 0.2rem 0.5rem; border-radius: 4px;
  text-transform: uppercase; letter-spacing: 0.04em;
}
.badge.done { background: rgba(16,185,129,0.07); color: var(--good); }
.badge.behind { background: var(--crit-soft); color: var(--crit); }
.badge.due_soon { background: var(--warn-soft); color: var(--warn); }
.badge.upcoming { background: var(--accent-soft); color: var(--accent); }
.badge.ongoing { background: var(--info-soft); color: var(--info); }
.badge.no_date { background: rgba(92,99,128,0.12); color: var(--text-mid); }
.badge.cat { background: rgba(92,99,128,0.08); color: var(--text-mid); }
.badge.wt { background: var(--info-soft); color: var(--info); }
.badge.dep {
  background: var(--accent-soft); color: var(--accent);
  display: inline-flex; align-items: center; gap: 0.2rem;
}

/* Expandable detail */
.tl-expand {
  max-height: 0; overflow: hidden;
  transition: max-height 0.3s ease;
}
.tl-card.open .tl-expand { max-height: 400px; }
.tl-detail {
  padding-top: 0.8rem; margin-top: 0.8rem;
  border-top: 1px solid var(--border);
  font-size: 0.82rem; line-height: 1.65;
}
.td-row { margin-bottom: 0.3rem; color: var(--text-bright); }
.td-label {
  font-family: 'DM Mono', monospace;
  font-size: 0.55rem; color: var(--text-mid);
  text-transform: uppercase; letter-spacing: 0.06em;
  display: block; margin-bottom: 0.1rem;
}
.td-quote {
  font-style: italic; color: var(--text);
  padding-left: 0.6rem; border-left: 2px solid var(--border);
}

/* Completed items - muted */
.tl-item.is-done .tl-card {
  opacity: 0.5;
  border-style: dashed;
}
.tl-item.is-done .tl-card:hover { opacity: 0.75; }
.tl-item.is-done .tl-dot {
  background: var(--good) !important;
  box-shadow: none !important;
}

/* Behind items - subtle alert */
.tl-zone-behind {
  position: relative;
  padding-bottom: 0.5rem;
}
.tl-zone-behind::after {
  content: '';
  position: absolute;
  left: -82px; right: -10px;
  top: 0; bottom: 0;
  background: linear-gradient(180deg, rgba(239,68,68,0.03), rgba(239,68,68,0.01));
  border-radius: 8px;
  pointer-events: none;
  z-index: -1;
}

/* ===== NO-DATE ITEMS ===== */
.nd-section { margin-bottom: 3.5rem; }
.nd-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 0.65rem;
}
.nd-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1rem 1.2rem;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-shadow: 0 1px 6px rgba(0,0,0,0.14);
}
.nd-card:hover { border-color: var(--border-hi); box-shadow: 0 2px 10px rgba(0,0,0,0.22); }
.nd-card-title {
  font-weight: 600; font-size: 0.86rem;
  color: var(--text-bright); line-height: 1.4;
  margin-bottom: 0.3rem;
}
.nd-card-detail {
  font-size: 0.8rem; color: var(--text);
  line-height: 1.6;
  max-height: 0; overflow: hidden;
  transition: max-height 0.3s;
}
.nd-card.open .nd-card-detail { max-height: 300px; padding-top: 0.5rem; border-top: 1px solid var(--border); margin-top: 0.5rem; }

/* ===== GAME PLAN ===== */
.plan { margin-bottom: 3.5rem; }
.plan-step {
  display: flex; gap: 1rem;
  padding: 0.9rem 0;
  border-bottom: 1px solid var(--border);
}
.plan-step:last-child { border-bottom: none; }
.plan-num {
  font-family: 'DM Mono', monospace;
  font-size: 0.68rem; font-weight: 500;
  color: var(--accent);
  background: var(--accent-soft);
  min-width: 26px; height: 26px;
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; margin-top: 0.1rem;
}
.plan-step:first-child .plan-num {
  color: var(--crit); background: var(--crit-soft);
}
.plan-text {
  font-size: 0.9rem; color: var(--text-bright);
  line-height: 1.55;
}

/* ===== BLOCKERS (inline) ===== */
.blockers { margin-bottom: 3.5rem; }
.blk {
  background: var(--crit-soft);
  border: 1px solid var(--crit-med);
  border-radius: 12px;
  padding: 1rem 1.3rem;
  margin-bottom: 0.55rem;
  font-size: 0.88rem; color: #fca5a5;
  line-height: 1.6;
  box-shadow: 0 1px 6px rgba(0,0,0,0.12);
}

/* ===== CONTEXT DRAWER ===== */
.ctx-toggle {
  font-family: 'DM Mono', monospace;
  font-size: 0.62rem; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--text-mid);
  background: none; border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.5rem 0.9rem;
  cursor: pointer; transition: all 0.2s;
  display: inline-flex; align-items: center; gap: 0.4rem;
  margin-bottom: 1rem;
}
.ctx-toggle:hover { border-color: var(--border-hi); color: var(--text); }
.ctx-toggle .arrow { transition: transform 0.2s; display: inline-block; font-size: 0.5rem; }
.ctx-toggle.open .arrow { transform: rotate(90deg); }
.ctx-drawer {
  max-height: 0; overflow: hidden;
  transition: max-height 0.35s ease;
}
.ctx-drawer.open { max-height: 1200px; }
.ctx-inner { padding-bottom: 2rem; }

/* Context sub-sections */
.ctx-block {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.1rem 1.4rem;
  margin-bottom: 0.7rem;
  box-shadow: 0 1px 6px rgba(0,0,0,0.12);
}
.ctx-block-title {
  font-family: 'DM Mono', monospace;
  font-size: 0.58rem; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--text-mid);
  margin-bottom: 0.6rem;
}
.ctx-text {
  font-size: 0.86rem; color: var(--text-bright);
  line-height: 1.65;
}
.ctx-rule {
  padding: 0.45rem 0;
  border-bottom: 1px solid var(--border);
  font-size: 0.84rem; color: var(--text-bright);
  line-height: 1.55;
}
.ctx-rule:last-child { border-bottom: none; }
.person-row {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.35rem 0;
}
.person-av {
  width: 24px; height: 24px; border-radius: 50%;
  background: var(--accent-soft);
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 0.58rem; color: var(--accent);
  flex-shrink: 0;
}
.person-name { font-weight: 600; font-size: 0.8rem; color: var(--text-bright); }
.person-role { font-size: 0.72rem; color: var(--text-mid); margin-left: 0.3rem; }

/* ===== EMPTY ===== */
.empty { text-align:center; padding:3rem; color:var(--text-mid); font-size:0.85rem; }

/* ===== RESPONSIVE ===== */
@media (max-width: 600px) {
  .shell { padding: 1.8rem 1rem; }
  .timeline { padding-left: 60px; }
  .timeline::before { left: 48px; }
  .tl-date { width: 50px; right: calc(100% + 16px); font-size: 0.55rem; }
  .tl-today::before { left: -62px; }
  .nd-grid { grid-template-columns: 1fr; }
  .tl-card { padding: 0.9rem 1rem; }
  .nd-card { padding: 0.9rem 1rem; }
  .blk { padding: 0.9rem 1.1rem; }
}
</style>
</head>
<body>

<div class="shell">
  <div class="hdr">
    <h1>Strategic Briefing</h1>
    <span class="hdr-sub">Generated """ + now + """</span>
  </div>
  <div id="app"></div>
</div>

<script>
const DATA = """ + js_data + """;
const TODAY = new Date(); TODAY.setHours(0,0,0,0);
const MS_DAY = 864e5;

let S = { topic: 0, open: new Set(), ndOpen: new Set(), ctxOpen: false };

function el(t, a, ...c) {
  const e = document.createElement(t);
  if (a) Object.entries(a).forEach(([k,v]) => {
    if (k === 'cls') e.className = v;
    else if (k.startsWith('on')) e.addEventListener(k.slice(2).toLowerCase(), v);
    else e.setAttribute(k, v);
  });
  c.flat().forEach(ch => { if (ch != null) e.append(typeof ch === 'string' ? document.createTextNode(ch) : ch); });
  return e;
}

function dayDiff(dateStr) {
  if (!dateStr) return null;
  return Math.round((new Date(dateStr+'T00:00:00') - TODAY) / MS_DAY);
}

function fmtDateShort(d) {
  if (!d) return '';
  return new Date(d+'T00:00:00').toLocaleDateString('en-US', { month:'short', day:'numeric' });
}

function relLabel(d, status) {
  const diff = dayDiff(d);
  if (diff === null) return '';
  if (status === 'done') return 'done';
  if (diff < -1) return Math.abs(diff) + 'd behind';
  if (diff === -1) return 'yesterday';
  if (diff === 0) return 'today';
  if (diff === 1) return 'tomorrow';
  if (diff <= 7) return 'in ' + diff + 'd';
  return '';
}

function relClass(d, status) {
  if (status === 'done') return 'done';
  const diff = dayDiff(d);
  if (diff === null) return '';
  if (diff < 0) return 'behind';
  if (diff <= 7) return 'soon';
  return '';
}

function initials(n) {
  return n.split(/\\s+/).map(w => w[0]).join('').toUpperCase().slice(0,2);
}

function statusLabel(s) {
  return {done:'DONE',behind:'BEHIND',due_soon:'DUE SOON',upcoming:'UPCOMING',ongoing:'ONGOING',no_date:'NO DATE'}[s]||s;
}

function render() {
  const app = document.getElementById('app');
  app.innerHTML = '';
  if (!DATA.length) { app.append(el('div',{cls:'empty'},'No data.')); return; }

  // Topic pills
  if (DATA.length > 1) {
    const tp = el('div',{cls:'topics'});
    DATA.forEach((t,i) => tp.append(el('button',{
      cls:'tpill'+(i===S.topic?' on':''),
      onClick:()=>{S.topic=i;S.open.clear();S.ndOpen.clear();S.ctxOpen=false;render();}
    },t.name)));
    app.append(tp);
  }

  const d = DATA[S.topic].data;
  const items = d.items || [];
  const risk = d.risk_level || 'unknown';

  // === RISK BANNER ===
  const rb = el('div',{cls:'risk '+risk});
  const riskNames = {critical:'CRITICAL',warning:'WARNING',on_track:'ON TRACK',unknown:'UNKNOWN'};
  rb.append(
    el('div',{cls:'risk-label'}, el('span',{cls:'dot'}), riskNames[risk]||'STATUS'),
    el('div',{}, d.status_summary||'No summary.')
  );
  app.append(rb);

  // === NEXT ACTION (first item from recommended_sequence) ===
  const seq = d.recommended_sequence || [];
  if (seq.length) {
    const urgentItem = items.find(i => i.urgency === 'high' && (i.status === 'due_soon' || i.status === 'behind'));
    const na = el('div',{cls:'next-action'});
    // If there's a genuinely urgent item, make it red. Otherwise calmer styling.
    if (urgentItem) {
      na.style.cssText = '';  // default red left border
      na.append(el('div',{cls:'na-eyebrow'}, 'Do this now'));
    } else {
      na.querySelector && (na.style.cssText = '');
      na.append(el('div',{cls:'na-eyebrow',style:'color:var(--accent)'}, 'Next up'));
      // Override the left border to accent
      na.style.setProperty('--na-color', 'var(--accent)');
    }
    na.append(el('div',{cls:'na-title'}, seq[0]));
    if (urgentItem && urgentItem.date) {
      na.append(el('div',{cls:'na-date'}, fmtDateShort(urgentItem.date) + ' \\u2014 ' + relLabel(urgentItem.date, urgentItem.status)));
    }
    app.append(na);
  }

  // === BLOCKERS (if any, show right after next action) ===
  const blockers = d.blockers || [];
  if (blockers.length) {
    const bs = el('div',{cls:'blockers'});
    bs.append(el('div',{cls:'sec-hdr'}, 'Blockers'));
    blockers.forEach(b => bs.append(el('div',{cls:'blk'}, b)));
    app.append(bs);
  }

  // === VERTICAL TIMELINE ===
  const datedItems = items.filter(i => i.date).sort((a,b) => a.date.localeCompare(b.date));
  const undatedItems = items.filter(i => !i.date);

  if (datedItems.length) {
    app.append(el('div',{cls:'sec-hdr'}, 'Timeline'));
    const tl = el('div',{cls:'timeline'});

    // Split into past (done/behind) and future
    const pastDone = datedItems.filter(i => i.status === 'done');
    const pastBehind = datedItems.filter(i => i.status === 'behind');
    const future = datedItems.filter(i => i.status !== 'done' && i.status !== 'behind');

    // Done items (muted, collapsed)
    if (pastDone.length) {
      pastDone.forEach(it => tl.append(makeTlItem(it, items, true)));
    }

    // Behind items (alert zone)
    if (pastBehind.length) {
      const zone = el('div',{cls:'tl-zone-behind'});
      pastBehind.forEach(it => zone.append(makeTlItem(it, items, false)));
      tl.append(zone);
    }

    // TODAY marker
    const todayLine = el('div',{cls:'tl-today'});
    todayLine.append(el('div',{cls:'tl-today-dot'}));
    todayLine.append(el('span',{cls:'tl-today-label'},
      'Today — ' + TODAY.toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric'})
    ));
    tl.append(todayLine);

    // Future items
    future.forEach(it => tl.append(makeTlItem(it, items, false)));

    app.append(tl);
  }

  // === UNDATED ITEMS (context grid) ===
  if (undatedItems.length) {
    const nds = el('div',{cls:'nd-section'});
    nds.append(el('div',{cls:'sec-hdr'}, 'Reference (' + undatedItems.length + ')'));
    const grid = el('div',{cls:'nd-grid'});
    undatedItems.forEach((it,i) => {
      const idx = items.indexOf(it);
      const isOpen = S.ndOpen.has(idx);
      const card = el('div',{
        cls:'nd-card'+(isOpen?' open':''),
        onClick:()=>{S.ndOpen.has(idx)?S.ndOpen.delete(idx):S.ndOpen.add(idx);render();}
      });
      card.append(
        el('div',{cls:'nd-card-title'}, it.title),
        el('div',{cls:'tl-card-badges'},
          it.category ? el('span',{cls:'badge cat'}, it.category) : null,
          it.weight ? el('span',{cls:'badge wt'}, it.weight) : null
        )
      );
      if (it.detail || it.source_quote) {
        const det = el('div',{cls:'nd-card-detail'});
        if (it.detail) det.append(el('div',{cls:'td-row'}, it.detail));
        if (it.source_quote) {
          det.append(el('div',{cls:'td-row'}, el('span',{cls:'td-label'},'Evidence'), el('div',{cls:'td-quote'},'"'+it.source_quote+'"')));
        }
        card.append(det);
      }
      grid.append(card);
    });
    nds.append(grid);
    app.append(nds);
  }

  // === GAME PLAN (always visible) ===
  if (seq.length > 1) {
    const plan = el('div',{cls:'plan'});
    plan.append(el('div',{cls:'sec-hdr'}, 'Game Plan'));
    seq.forEach((s,i) => {
      plan.append(el('div',{cls:'plan-step'},
        el('div',{cls:'plan-num'}, ''+(i+1)),
        el('div',{cls:'plan-text'}, s)
      ));
    });
    app.append(plan);
  }

  // === CONTEXT DRAWER (rules, people, description — collapsed) ===
  const hasCtx = (d.context) || (d.key_rules && d.key_rules.length) || (d.people && d.people.length);
  if (hasCtx) {
    const toggle = el('button',{
      cls:'ctx-toggle'+(S.ctxOpen?' open':''),
      onClick:()=>{S.ctxOpen=!S.ctxOpen;render();}
    },
      el('span',{cls:'arrow'}, '\\u25B6'),
      'Context & Rules'
    );
    app.append(toggle);

    const drawer = el('div',{cls:'ctx-drawer'+(S.ctxOpen?' open':'')});
    const inner = el('div',{cls:'ctx-inner'});

    if (d.context) {
      const blk = el('div',{cls:'ctx-block'});
      blk.append(el('div',{cls:'ctx-block-title'},'About'));
      blk.append(el('div',{cls:'ctx-text'}, d.context));
      inner.append(blk);
    }

    if (d.people && d.people.length) {
      const blk = el('div',{cls:'ctx-block'});
      blk.append(el('div',{cls:'ctx-block-title'},'People'));
      d.people.forEach(p => {
        blk.append(el('div',{cls:'person-row'},
          el('div',{cls:'person-av'}, initials(p.name)),
          el('span',{cls:'person-name'}, p.name),
          p.role ? el('span',{cls:'person-role'}, '— '+p.role) : null
        ));
      });
      inner.append(blk);
    }

    if (d.key_rules && d.key_rules.length) {
      const blk = el('div',{cls:'ctx-block'});
      blk.append(el('div',{cls:'ctx-block-title'},'Key Rules'));
      d.key_rules.forEach(r => blk.append(el('div',{cls:'ctx-rule'}, r)));
      inner.append(blk);
    }

    drawer.append(inner);
    app.append(drawer);
  }
}

function makeTlItem(it, allItems, isDone) {
  const idx = allItems.indexOf(it);
  const isOpen = S.open.has(idx);
  const wrapper = el('div',{cls:'tl-item' + (isDone ? ' is-done' : '')});

  // Date label (left of track)
  const dateEl = el('div',{cls:'tl-date'});
  dateEl.append(el('span',{}, fmtDateShort(it.date)));
  const rl = relLabel(it.date, it.status);
  if (rl) {
    dateEl.append(el('span',{cls:'tl-rel '+relClass(it.date, it.status)}, rl));
  }
  wrapper.append(dateEl);

  // Dot on track
  wrapper.append(el('div',{cls:'tl-dot '+(it.urgency||'info')}));

  // Card
  const card = el('div',{
    cls:'tl-card'+(isOpen?' open':''),
    onClick:()=>{S.open.has(idx)?S.open.delete(idx):S.open.add(idx);render();}
  });

  card.append(el('div',{cls:'tl-card-title'}, it.title));

  const badges = el('div',{cls:'tl-card-badges'});
  if (it.status) badges.append(el('span',{cls:'badge '+it.status}, statusLabel(it.status)));
  if (it.category) badges.append(el('span',{cls:'badge cat'}, it.category));
  if (it.weight) badges.append(el('span',{cls:'badge wt'}, it.weight));
  if (it.depends_on) badges.append(el('span',{cls:'badge dep'}, '\\u2190 '+it.depends_on));
  card.append(badges);

  // Expandable detail
  const expand = el('div',{cls:'tl-expand'});
  const detail = el('div',{cls:'tl-detail'});
  if (it.detail) detail.append(el('div',{cls:'td-row'}, it.detail));
  if (it.source_quote) {
    detail.append(el('div',{cls:'td-row'},
      el('span',{cls:'td-label'},'Evidence'),
      el('div',{cls:'td-quote'}, '"'+it.source_quote+'"')
    ));
  }
  if (it.people && it.people.length) {
    detail.append(el('div',{cls:'td-row'}, el('span',{cls:'td-label'},'People'), el('span',{}, it.people.join(', '))));
  }
  if (it.source_file) {
    detail.append(el('div',{cls:'td-row'}, el('span',{cls:'td-label'},'Source'), el('span',{}, it.source_file)));
  }
  expand.append(detail);
  card.append(expand);
  wrapper.append(card);
  return wrapper;
}

render();
</script>
</body></html>"""

    with open(output_path, 'w') as f:
        f.write(page)
    print(f"  Wrote {output_path}")


def render_transcript(topic_reports, output_path="index.html"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    js_data = json.dumps(topic_reports, ensure_ascii=False)

    page = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Transcript Report</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Sora:wght@300;400;600;800&display=swap');

*, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }

:root {
  --bg: #07090e;
  --surface: #0d1119;
  --surface-2: #141924;
  --border: #1c2235;
  --border-hi: #2a3350;
  --text: #8890a8;
  --text-mid: #5c6380;
  --text-bright: #d0d5e4;
  --text-white: #eef0f7;
  --accent: #3b82f6;
  --accent-soft: rgba(59,130,246,0.08);
  --crit: #ef4444;
  --crit-soft: rgba(239,68,68,0.07);
  --crit-med: rgba(239,68,68,0.18);
  --warn: #eab308;
  --warn-soft: rgba(234,179,8,0.07);
  --warn-med: rgba(234,179,8,0.18);
  --good: #10b981;
  --good-soft: rgba(16,185,129,0.07);
  --info: #818cf8;
  --info-soft: rgba(129,140,248,0.07);
}

html { background: var(--bg); }
body {
  font-family: 'Sora', sans-serif;
  color: var(--text);
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}

.shell {
  max-width: 900px;
  margin: 0 auto;
  padding: 2.5rem 1.5rem 6rem;
}

/* ===== HEADER ===== */
.hdr { margin-bottom: 2rem; }
.hdr h1 {
  font-weight: 800; font-size: 1.5rem;
  color: var(--text-white);
  letter-spacing: -0.04em;
}
.hdr-sub {
  font-family: 'DM Mono', monospace;
  font-size: 0.62rem; color: var(--text-mid);
  margin-top: 0.35rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

/* ===== TOPIC PILLS ===== */
.topics { display: flex; gap: 0.35rem; margin-bottom: 2rem; flex-wrap: wrap; }
.tpill {
  font-family: 'Sora'; font-weight: 600; font-size: 0.75rem;
  padding: 0.4rem 1rem; border-radius: 99px;
  border: 1px solid var(--border);
  background: var(--surface); color: var(--text);
  cursor: pointer; transition: all 0.2s;
}
.tpill:hover { border-color: var(--accent); }
.tpill.on { background: var(--accent-soft); border-color: var(--accent); color: var(--accent); }

/* ===== CONTENT WARNING ===== */
.cw-banner {
  padding: 0.9rem 1.3rem;
  border-radius: 12px;
  border-left: 3px solid var(--crit);
  background: var(--crit-soft);
  margin-bottom: 2rem;
  font-size: 0.88rem;
  color: #fca5a5;
  line-height: 1.6;
}
.cw-label {
  font-family: 'DM Mono', monospace;
  font-size: 0.58rem; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--crit);
  margin-bottom: 0.3rem;
}

/* ===== SUMMARY ===== */
.summary-block {
  padding: 1.1rem 1.4rem;
  border-radius: 12px;
  border-left: 3px solid var(--accent);
  background: var(--accent-soft);
  margin-bottom: 2.5rem;
  font-size: 0.92rem;
  color: var(--text-bright);
  line-height: 1.7;
}

/* ===== SECTION HEADERS ===== */
.sec-hdr {
  font-family: 'DM Mono', monospace;
  font-size: 0.85rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--text-bright);
  margin-bottom: 1.2rem;
  padding-bottom: 0.6rem;
  border-bottom: 1px solid var(--border);
}

/* ===== TOPIC CARDS ===== */
.topic-list { margin-bottom: 3rem; }
.topic-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.1rem 1.3rem;
  margin-bottom: 0.65rem;
  box-shadow: 0 1px 6px rgba(0,0,0,0.14);
}
.topic-card-heading {
  font-weight: 600; font-size: 0.95rem;
  color: var(--text-bright);
  line-height: 1.4;
  margin-bottom: 0.5rem;
}
.topic-card-summary {
  font-size: 0.86rem; color: var(--text);
  line-height: 1.65;
  margin-bottom: 0.7rem;
}
.ts-pills { display: flex; gap: 0.3rem; flex-wrap: wrap; margin-bottom: 0.6rem; }
.ts-pill {
  font-family: 'DM Mono', monospace;
  font-size: 0.6rem; font-weight: 500;
  padding: 0.18rem 0.55rem; border-radius: 99px;
  background: var(--accent-soft); color: var(--accent);
  border: 1px solid rgba(59,130,246,0.2);
}
.quotes-toggle {
  font-family: 'DM Mono', monospace;
  font-size: 0.6rem; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--text-mid);
  background: none; border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0.3rem 0.7rem;
  cursor: pointer; transition: all 0.2s;
  display: inline-flex; align-items: center; gap: 0.35rem;
}
.quotes-toggle:hover { border-color: var(--border-hi); color: var(--text); }
.quotes-toggle .arrow { transition: transform 0.2s; display: inline-block; font-size: 0.5rem; }
.quotes-toggle.open .arrow { transform: rotate(90deg); }
.quotes-drawer { max-height: 0; overflow: hidden; transition: max-height 0.3s ease; }
.quotes-drawer.open { max-height: 600px; }
.quote-item {
  margin-top: 0.6rem;
  font-style: italic;
  font-size: 0.83rem;
  color: var(--text);
  padding: 0.5rem 0.8rem;
  border-left: 2px solid var(--border);
  line-height: 1.6;
}

/* ===== KEY CLAIMS ===== */
.claims-list { margin-bottom: 3rem; }
.claim-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1rem 1.3rem;
  margin-bottom: 0.65rem;
  box-shadow: 0 1px 6px rgba(0,0,0,0.14);
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}
.claim-card:hover { border-color: var(--border-hi); background: var(--surface-2); }
.claim-text {
  font-size: 0.9rem; color: var(--text-bright);
  line-height: 1.5;
  margin-bottom: 0.45rem;
}
.claim-badges { display: flex; gap: 0.35rem; flex-wrap: wrap; align-items: center; }
.badge {
  font-family: 'DM Mono', monospace;
  font-size: 0.58rem; font-weight: 500;
  padding: 0.2rem 0.5rem; border-radius: 4px;
  text-transform: uppercase; letter-spacing: 0.04em;
}
.badge.speaker { background: var(--accent-soft); color: var(--accent); }
.badge.ts { background: rgba(92,99,128,0.12); color: var(--text-mid); }
.claim-expand { max-height: 0; overflow: hidden; transition: max-height 0.3s ease; }
.claim-card.open .claim-expand { max-height: 300px; }
.claim-quote {
  padding-top: 0.7rem;
  margin-top: 0.7rem;
  border-top: 1px solid var(--border);
  font-style: italic;
  font-size: 0.82rem;
  color: var(--text);
  padding-left: 0.6rem;
  border-left: 2px solid var(--border);
  line-height: 1.6;
}

/* ===== PEOPLE GRID ===== */
.people-section { margin-bottom: 3rem; }
.people-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 0.65rem;
}
.person-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1rem 1.2rem;
  box-shadow: 0 1px 6px rgba(0,0,0,0.14);
}
.person-row {
  display: flex; align-items: center; gap: 0.6rem;
  margin-bottom: 0.5rem;
}
.person-av {
  width: 32px; height: 32px; border-radius: 50%;
  background: var(--accent-soft);
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 0.68rem; color: var(--accent);
  flex-shrink: 0;
}
.person-name { font-weight: 600; font-size: 0.86rem; color: var(--text-bright); }
.person-role { font-size: 0.75rem; color: var(--text-mid); }
.person-mentions {
  list-style: none;
  padding: 0;
}
.person-mentions li {
  font-size: 0.8rem; color: var(--text);
  line-height: 1.55;
  padding: 0.3rem 0;
  border-bottom: 1px solid var(--border);
}
.person-mentions li:last-child { border-bottom: none; }

/* ===== TAKEAWAYS ===== */
.takeaways { margin-bottom: 3rem; }
.takeaway-step {
  display: flex; gap: 1rem;
  padding: 0.9rem 0;
  border-bottom: 1px solid var(--border);
}
.takeaway-step:last-child { border-bottom: none; }
.takeaway-num {
  font-family: 'DM Mono', monospace;
  font-size: 0.68rem; font-weight: 500;
  color: var(--accent);
  background: var(--accent-soft);
  min-width: 26px; height: 26px;
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; margin-top: 0.1rem;
}
.takeaway-text {
  font-size: 0.9rem; color: var(--text-bright);
  line-height: 1.55;
}

/* ===== TRANSCRIPT DRAWER ===== */
.ctx-toggle {
  font-family: 'DM Mono', monospace;
  font-size: 0.62rem; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--text-mid);
  background: none; border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.5rem 0.9rem;
  cursor: pointer; transition: all 0.2s;
  display: inline-flex; align-items: center; gap: 0.4rem;
  margin-bottom: 1rem;
}
.ctx-toggle:hover { border-color: var(--border-hi); color: var(--text); }
.ctx-toggle .arrow { transition: transform 0.2s; display: inline-block; font-size: 0.5rem; }
.ctx-toggle.open .arrow { transform: rotate(90deg); }
.ctx-drawer { max-height: 0; overflow: hidden; transition: max-height 0.5s ease; }
.ctx-drawer.open { max-height: 9999px; }
.transcript-pre {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.2rem 1.4rem;
  font-family: 'DM Mono', monospace;
  font-size: 0.78rem;
  color: var(--text);
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-word;
  box-shadow: 0 1px 6px rgba(0,0,0,0.14);
}

/* ===== EMPTY ===== */
.empty { text-align:center; padding:3rem; color:var(--text-mid); font-size:0.85rem; }

/* ===== RESPONSIVE ===== */
@media (max-width: 600px) {
  .shell { padding: 1.8rem 1rem; }
  .people-grid { grid-template-columns: 1fr; }
}
</style>
</head>
<body>

<div class="shell">
  <div class="hdr">
    <h1 id="page-title">Transcript Report</h1>
    <span class="hdr-sub" id="page-sub">Generated """ + now + """</span>
  </div>
  <div id="app"></div>
</div>

<script>
const DATA = """ + js_data + """;

let S = { topic: 0, claimOpen: new Set(), quotesOpen: new Set(), txOpen: false };

function el(t, a, ...c) {
  const e = document.createElement(t);
  if (a) Object.entries(a).forEach(([k,v]) => {
    if (k === 'cls') e.className = v;
    else if (k.startsWith('on')) e.addEventListener(k.slice(2).toLowerCase(), v);
    else e.setAttribute(k, v);
  });
  c.flat().forEach(ch => { if (ch != null) e.append(typeof ch === 'string' ? document.createTextNode(ch) : ch); });
  return e;
}

function initials(n) {
  return n.split(/\\s+/).filter(w => w.length > 0).map(w => w[0]).join('').toUpperCase().slice(0,2);
}

function render() {
  const app = document.getElementById('app');
  app.innerHTML = '';
  if (!DATA.length) { app.append(el('div',{cls:'empty'},'No data.')); return; }

  // Topic pills (multi-topic)
  if (DATA.length > 1) {
    const tp = el('div',{cls:'topics'});
    DATA.forEach((t,i) => tp.append(el('button',{
      cls:'tpill'+(i===S.topic?' on':''),
      onClick:()=>{S.topic=i;S.claimOpen.clear();S.quotesOpen.clear();S.txOpen=false;render();}
    },t.name)));
    app.append(tp);
  }

  const entry = DATA[S.topic];
  const d = entry.data || {};
  const transcript = entry.transcript || '';

  // Update page title
  document.getElementById('page-title').textContent = d.title || ('Transcript: ' + entry.name);
  document.getElementById('page-sub').textContent =
    entry.name + '  \\u2014  Generated """ + now + """';

  // === CONTENT WARNINGS ===
  const cws = d.content_warnings || [];
  if (cws.length) {
    const banner = el('div',{cls:'cw-banner'});
    banner.append(el('div',{cls:'cw-label'}, 'Content Warning'));
    cws.forEach(w => banner.append(el('div',{}, w)));
    app.append(banner);
  }

  // === SUMMARY ===
  if (d.summary) {
    app.append(el('div',{cls:'summary-block'}, d.summary));
  }

  // === TOPICS DISCUSSED ===
  const topics = d.topics || [];
  if (topics.length) {
    const sec = el('div',{cls:'topic-list'});
    sec.append(el('div',{cls:'sec-hdr'}, 'Topics Discussed'));
    topics.forEach((tp,i) => {
      const card = el('div',{cls:'topic-card'});
      card.append(el('div',{cls:'topic-card-heading'}, tp.heading || ''));
      if (tp.summary) card.append(el('div',{cls:'topic-card-summary'}, tp.summary));
      const tss = tp.timestamps || [];
      if (tss.length) {
        const pills = el('div',{cls:'ts-pills'});
        tss.forEach(ts => pills.append(el('span',{cls:'ts-pill'}, ts)));
        card.append(pills);
      }
      const quotes = tp.key_quotes || [];
      if (quotes.length) {
        const isOpen = S.quotesOpen.has(i);
        const qBtn = el('button',{
          cls:'quotes-toggle'+(isOpen?' open':''),
          onClick:()=>{S.quotesOpen.has(i)?S.quotesOpen.delete(i):S.quotesOpen.add(i);render();}
        }, el('span',{cls:'arrow'}, '\\u25B6'), quotes.length + ' Quote' + (quotes.length>1?'s':''));
        card.append(qBtn);
        const qDrawer = el('div',{cls:'quotes-drawer'+(isOpen?' open':'')});
        quotes.forEach(q => qDrawer.append(el('div',{cls:'quote-item'}, '\\u201C'+q+'\\u201D')));
        card.append(qDrawer);
      }
      sec.append(card);
    });
    app.append(sec);
  }

  // === KEY CLAIMS ===
  const claims = d.key_claims || [];
  if (claims.length) {
    const sec = el('div',{cls:'claims-list'});
    sec.append(el('div',{cls:'sec-hdr'}, 'Key Claims & Facts'));
    claims.forEach((cl,i) => {
      const isOpen = S.claimOpen.has(i);
      const card = el('div',{
        cls:'claim-card'+(isOpen?' open':''),
        onClick:()=>{S.claimOpen.has(i)?S.claimOpen.delete(i):S.claimOpen.add(i);render();}
      });
      card.append(el('div',{cls:'claim-text'}, cl.claim || ''));
      const badges = el('div',{cls:'claim-badges'});
      if (cl.speaker) badges.append(el('span',{cls:'badge speaker'}, cl.speaker));
      if (cl.timestamp) badges.append(el('span',{cls:'badge ts'}, cl.timestamp));
      card.append(badges);
      if (cl.source_quote) {
        const exp = el('div',{cls:'claim-expand'});
        exp.append(el('div',{cls:'claim-quote'}, '\\u201C'+cl.source_quote+'\\u201D'));
        card.append(exp);
      }
      sec.append(card);
    });
    app.append(sec);
  }

  // === PEOPLE ===
  const people = d.people || [];
  if (people.length) {
    const sec = el('div',{cls:'people-section'});
    sec.append(el('div',{cls:'sec-hdr'}, 'People'));
    const grid = el('div',{cls:'people-grid'});
    people.forEach(p => {
      const card = el('div',{cls:'person-card'});
      const row = el('div',{cls:'person-row'});
      row.append(el('div',{cls:'person-av'}, initials(p.name||'?')));
      const info = el('div',{});
      info.append(el('div',{cls:'person-name'}, p.name||''));
      if (p.role) info.append(el('div',{cls:'person-role'}, p.role));
      row.append(info);
      card.append(row);
      const mentions = p.mentions || [];
      if (mentions.length) {
        const ul = el('ul',{cls:'person-mentions'});
        mentions.forEach(m => ul.append(el('li',{}, m)));
        card.append(ul);
      }
      grid.append(card);
    });
    sec.append(grid);
    app.append(sec);
  }

  // === TAKEAWAYS ===
  const takeaways = d.takeaways || [];
  if (takeaways.length) {
    const sec = el('div',{cls:'takeaways'});
    sec.append(el('div',{cls:'sec-hdr'}, 'Key Takeaways'));
    takeaways.forEach((t,i) => {
      sec.append(el('div',{cls:'takeaway-step'},
        el('div',{cls:'takeaway-num'}, ''+(i+1)),
        el('div',{cls:'takeaway-text'}, t)
      ));
    });
    app.append(sec);
  }

  // === FULL TRANSCRIPT (collapsible) ===
  if (transcript) {
    const toggle = el('button',{
      cls:'ctx-toggle'+(S.txOpen?' open':''),
      onClick:()=>{S.txOpen=!S.txOpen;render();}
    },
      el('span',{cls:'arrow'}, '\\u25B6'),
      'Full Transcript'
    );
    app.append(toggle);
    const drawer = el('div',{cls:'ctx-drawer'+(S.txOpen?' open':'')});
    drawer.append(el('pre',{cls:'transcript-pre'}, transcript));
    app.append(drawer);
  }
}

render();
</script>
</body></html>"""

    with open(output_path, 'w') as f:
        f.write(page)
    print(f"  Wrote {output_path}")