import requests
import subprocess
import os
import shutil
import re
import json
from datetime import datetime

# --- CONFIG ---
USERNAME = "browntown333"
DOMAIN = "orphan-lab.vercel.app"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DISPERSAL_FILE = os.path.join(BASE_DIR, "dispersal_leagues.txt")
HIDDEN_FILE = os.path.join(BASE_DIR, "hidden_leagues.txt")
DEPLOY_DIR = os.path.join(BASE_DIR, "dist")
PREVIEW_IMG = "preview.png"

# --- HELPERS ---
def clean_name(name):
    return re.sub(r'[@\s]', '', str(name)).lower() if name else ""

def get_file_ids(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return [line.strip() for line in f if line.strip().isdigit()]
    return []

def get_dispersal_mapping():
    config = {}
    if not os.path.exists(DISPERSAL_FILE): return config
    with open(DISPERSAL_FILE, "r") as f:
        content = f.read()
    blocks = re.split(r'(\d{18,19})', content)
    for i in range(1, len(blocks), 2):
        l_id = blocks[i].strip()
        order_text = blocks[i+1] if i+1 < len(blocks) else ""
        matches = re.findall(r'(\d+):\s*@([a-zA-Z0-9._-]+(?:\s\d+)?)', order_text)
        if matches:
            config[l_id] = {int(slot): val.strip() for slot, val in matches}
    return config

def get_current_season():
    try:
        res = requests.get("https://api.sleeper.app/v1/state/nfl").json()
        return int(res.get("season", "2026"))
    except: return 2026

def get_fc_values():
    print("📈 Fetching values from FantasyCalc...")
    url = "https://api.fantasycalc.com/values/current?isDynasty=true&numQbs=2&numTeams=12&ppr=1"
    try:
        data = requests.get(url).json()
        v_map = {}
        for p in data:
            val = p.get('value', 0)
            player_obj = p.get('player', {})
            sid = player_obj.get('sleeperId')
            if sid: v_map[str(sid)] = val
            p_name = player_obj.get('name')
            if p_name: v_map[p_name.lower()] = val
        return v_map
    except Exception as e:
        print(f"❌ FC Fetch Error: {e}"); return {}

def is_commish(league_id, my_user_id):
    users = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/users").json()
    return any(u.get("user_id") == my_user_id and u.get("is_owner") for u in users)

# --- CORE DATA ---
def get_data():
    season = get_current_season()
    p_map = requests.get("https://api.sleeper.app/v1/players/nfl").json()
    u_data = requests.get(f"https://api.sleeper.app/v1/user/{USERNAME}").json()
    u_id = u_data.get("user_id")
    leagues = requests.get(f"https://api.sleeper.app/v1/user/{u_id}/leagues/nfl/{season}").json()

    fc_values = get_fc_values()
    disp_config = get_dispersal_mapping()
    hidden_ids = get_file_ids(HIDDEN_FILE)

    orphan_data, dispersal_data = [], []

    for league in leagues:
        l_id = str(league['league_id']).strip()
        if l_id in hidden_ids or not is_commish(l_id, u_id): continue

        settings = league.get('settings', {})
        scoring = league.get('scoring_settings', {})
        roster_pos = league.get('roster_positions', [])

        common_settings = {
            "bb": "Best Ball" if settings.get('best_ball')==1 else "Lineup",
            "team": f"{league.get('total_rosters', 12)} Team",
            "start": f"Start {len([x for x in roster_pos if x != 'BN'])}",
            "roster": f"{len(roster_pos) + settings.get('reserve_slots', 0) + settings.get('taxi_slots', 0)} Roster",
            "sf": "SF" if "SUPER_FLEX" in roster_pos else "1QB",
            "ppr": f"{scoring.get('rec', 0)} PPR",
            "tep": f"{scoring.get('bonus_rec_te', 0)} TEP" if scoring.get('bonus_rec_te', 0) > 0 else None,
            "pptd": f"{scoring.get('pass_td', 4)} PPTD"
        }

        rosters = requests.get(f"https://api.sleeper.app/v1/league/{l_id}/rosters").json()
        users = requests.get(f"https://api.sleeper.app/v1/league/{l_id}/users").json()
        traded_picks = requests.get(f"https://api.sleeper.app/v1/league/{l_id}/traded_picks").json()

        u_id_to_name = {u['user_id']: u['display_name'] for u in users}
        orphans = [r for r in rosters if not r.get("owner_id") or r.get("owner_id") == "0"]

        if not orphans:
            continue
            
        orphan_rids = [r['roster_id'] for r in orphans]

        if l_id in disp_config:
            pool, future_val, slot_map = [], 0, disp_config[l_id]
            name_to_rid = {}
            for r in rosters:
                d_name = u_id_to_name.get(r.get('owner_id'), "ORPHAN")
                name_to_rid[clean_name(d_name)] = r['roster_id']
                name_to_rid[f"orphan{r['roster_id']}"] = r['roster_id']

            for r in orphans:
                for pid in (r.get("players") or []):
                    p = p_map.get(str(pid), {})
                    name = f"{p.get('first_name','')} {p.get('last_name','')}"
                    val = fc_values.get(str(pid), fc_values.get(name.lower(), 0))
                    if val > 0: pool.append({"name": name, "pos": p.get("position"), "val": val})

            for y in [season, season+1, season+2]:
                for rd in range(1, settings.get("draft_rounds", 3) + 1):
                    for slot, assigned_name in slot_map.items():
                        orig_rid = name_to_rid.get(clean_name(assigned_name))
                        if not orig_rid: continue
                        curr_owner_rid = orig_rid
                        for t in traded_picks:
                            if str(t['season']) == str(y) and t['round'] == rd and t['roster_id'] == orig_rid:
                                curr_owner_rid = t['owner_id']
                        if curr_owner_rid in orphan_rids:
                            if y == season:
                                key, lbl = f"DP_{rd-1}_{slot-1}", f"{y} {rd}.{slot:02d}"
                                v = fc_values.get(key, 0)
                                if v > 0: pool.append({"name": lbl, "pos": "PICK", "val": v})
                            else:
                                key = f"FP_{y}_{rd}"
                                future_val += fc_values.get(key, 0)

            sorted_pool = sorted(pool, key=lambda x: x['val'], reverse=True)
            dispersal_data.append({
                "league": league['name'], "label": f"{len(orphans)} Team Dispersal",
                "val": (sum(a['val'] for a in sorted_pool) + future_val) // len(orphans),
                "settings": common_settings, "top": sorted_pool[:20], "rest": sorted_pool[20:], "count": len(sorted_pool)
            })
        else:
            draft_map = {}
            try:
                drafts = requests.get(f"https://api.sleeper.app/v1/league/{l_id}/drafts").json()
                if drafts:
                    d = drafts[0]
                    if d.get('slot_to_roster_id'): draft_map = {int(v): int(k) for k, v in d['slot_to_roster_id'].items()}
                    elif d.get('draft_order'):
                        u_to_s = d['draft_order']
                        for r in rosters:
                            if r.get('owner_id') in u_to_s: draft_map[r['roster_id']] = u_to_s[r['owner_id']]
            except: pass

            for r in orphans:
                p_details, ages, picks, p_val = [], [], [], 0
                for pid in (r.get("players") or []):
                    p = p_map.get(str(pid), {})
                    name = f"{p.get('first_name','')} {p.get('last_name','')}"
                    val = fc_values.get(str(pid), fc_values.get(name.lower(), 0))
                    if p.get('age'): ages.append(p.get('age'))
                    p_details.append({"name": name, "pos": p.get("position"), "val": val})

                for y in [season, season+1, season+2]:
                    for rd in range(1, settings.get("draft_rounds", 3) + 1):
                        for o_rid in [ros['roster_id'] for ros in rosters]:
                            curr = o_rid
                            for t in traded_picks:
                                if str(t['season']) == str(y) and t['round'] == rd and t['roster_id'] == o_rid: curr = t['owner_id']
                            if curr == r['roster_id']:
                                slot = draft_map.get(o_rid)
                                if y == season and slot:
                                    v, l = fc_values.get(f"DP_{rd-1}_{slot-1}", 0), f"{y} {rd}.{slot:02d}"
                                else:
                                    v, l = fc_values.get(f"FP_{y}_{rd}", 0), f"{y} Rd {rd}"
                                p_val += v
                                picks.append({"label": l, "val": v, "highlight": (o_rid != r['roster_id'])})

                lineup, remaining = [], sorted(p_details, key=lambda x: x['val'], reverse=True)
                for s in [pos for pos in roster_pos if pos != 'BN']:
                    m = next((p for p in remaining if s == 'SUPER_FLEX' or s == p['pos'] or (s == 'FLEX' and p['pos'] in ['RB','WR','TE'])), None)
                    if m: remaining.remove(m)
                    lineup.append({"slot": s.replace("SUPER_FLEX", "SFLEX"), "name": m['name'] if m else "EMPTY", "val": m['val'] if m else 0})

                orphan_data.append({
                    "league": league['name'], "label": f"Team {r['roster_id']}", "val": sum(p['val'] for p in p_details) + p_val,
                    "avg_age": round(sum(ages)/len(ages), 1) if ages else 0, "pick_val": p_val, "settings": common_settings, "lineup": lineup, "bench": remaining, "picks": picks
                })
    return sorted(orphan_data, key=lambda x: x['val'], reverse=True), sorted(dispersal_data, key=lambda x: x['val'], reverse=True)

# --- SITE BUILDER ---
def build_site(orphans, dispersals):
    last_updated = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    season = get_current_season()

    def make_badges(st):
        l_k, r_k = ['bb','team','start','roster'], ['sf','ppr','tep','pptd']
        l_b = "".join([f"<span class='block bg-slate-900 border border-slate-700 text-zinc-300 px-1 py-1.5 rounded-lg text-[9px] font-bold mb-1.5 w-full text-center tracking-tight'>{st[k]}</span>" for k in l_k if st.get(k)])
        r_b = "".join([f"<span class='block bg-slate-900 border border-slate-700 text-zinc-300 px-1 py-1.5 rounded-lg text-[9px] font-bold mb-1.5 w-full text-center tracking-tight'>{st[k]}</span>" for k in r_k if st.get(k)])
        return l_b, r_b

    def get_orphan_cards(data):
        h = ""
        for item in data:
            l_b, r_b = make_badges(item['settings'])
            lineup_h = "".join([f"<li class='flex items-center justify-between py-2 border-b border-white/5 last:border-0'><span class='text-slate-500 font-bold w-14 text-[9px] uppercase tracking-tighter flex-shrink-0'>{p['slot']}</span><span class='text-slate-200 truncate pr-2 font-medium flex-grow leading-tight py-0.5'>{p['name']}</span><span class='text-emerald-400 font-mono font-bold leading-tight'>{p['val']}</span></li>" for p in item['lineup']])
            bench_h = "".join([f"<li class='flex items-center justify-between py-2 border-b border-white/5 last:border-0'><span class='text-slate-500 font-bold w-14 text-[9px] uppercase tracking-tighter flex-shrink-0'>{p['pos']}</span><span class='text-slate-200 truncate pr-2 font-medium flex-grow leading-tight py-0.5'>{p['name']}</span><span class='text-slate-400 font-mono font-bold leading-tight'>{p['val']}</span></li>" for p in item['bench']])
            picks_h = "".join([f"<li class='flex items-center justify-between py-2 border-b border-white/5 last:border-0'><span class='text-slate-500 font-bold w-14 text-[9px] uppercase tracking-tighter flex-shrink-0'>PICK</span><span class='font-bold flex-grow leading-tight py-0.5 {'text-emerald-400' if p['highlight'] else 'text-sky-400'} text-[12px] uppercase tracking-tight'>{'+' if p['highlight'] else ''}{p['label']}</span><span class='text-slate-500 font-mono font-bold leading-tight'>{p['val']}</span></li>" for p in item['picks']])
            h += f"""
            <div class="bg-[#0f0f0f] border border-slate-800 rounded-[2rem] p-5 sm:p-7 flex flex-col h-fit w-full shadow-2xl" x-data="{{ open: false }}">
                <div class="mb-5 text-center"><h2 class="text-xl sm:text-2xl font-black text-white leading-tight uppercase tracking-tighter break-words">{item['league']}</h2></div>
                <div class="flex items-stretch gap-2 mb-6">
                    <div class="w-16 sm:w-20 flex-shrink-0 flex flex-col justify-center">{l_b}</div>
                    <div class="flex-grow bg-white/5 rounded-2xl p-4 flex flex-col justify-center items-center border border-white/10">
                        <p class="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1">{item['label']}</p>
                        <p class="text-3xl sm:text-4xl font-black text-emerald-400 leading-none mb-1">{item['val']:,}</p>
                        <p class="text-[8px] text-slate-600 font-bold uppercase tracking-widest">Market Value</p>
                    </div>
                    <div class="w-16 sm:w-20 flex-shrink-0 flex flex-col justify-center">{r_b}</div>
                </div>
                <div class="flex justify-between items-center mb-6 px-1">
                    <div><p class="text-[9px] text-slate-600 font-bold uppercase tracking-wider mb-0.5">Avg Age</p><p class="text-[13px] font-black text-white">{item['avg_age']}</p></div>
                    <div class="text-right"><p class="text-[9px] text-slate-600 font-bold uppercase tracking-wider mb-0.5">Picks Value</p><p class="text-[13px] font-black text-sky-400">{item['pick_val']:,}</p></div>
                </div>
                <div class='flex items-center gap-2 mb-3'><p class="text-[9px] text-slate-600 font-black uppercase tracking-[0.2em]">Starting Lineup</p><div class='h-px flex-grow bg-slate-800/50'></div></div>
                <ul class="mb-6 flex-grow">{lineup_h}</ul>
                <button @click="open = !open" class="w-full py-4 bg-white/5 border border-white/10 rounded-2xl text-[12px] font-black text-slate-300 uppercase tracking-widest hover:bg-white hover:text-black transition-all">
                    <span x-text="open ? 'Hide Assets' : 'Details & Assets'"></span>
                </button>
                <div x-show="open" x-collapse class="mt-6 pt-6 border-t border-slate-800 space-y-8">
                    <div><div class='flex items-center gap-2 mb-4'><p class="text-[9px] text-slate-600 font-black uppercase tracking-[0.2em]">Bench Assets</p><div class='h-px flex-grow bg-slate-800/50'></div></div><ul class="flex flex-col">{bench_h}</ul></div>
                    <div><div class='flex items-center gap-2 mb-4'><p class="text-[9px] text-slate-600 font-black uppercase tracking-[0.2em]">Draft Capital</p><div class='h-px flex-grow bg-slate-800/50'></div></div><ul class="flex flex-col">{picks_h}</ul></div>
                </div>
            </div>"""
        return h

    def get_dispersal_cards(data):
        h = ""
        for item in data:
            l_b, r_b = make_badges(item['settings'])
            top_h = "".join([f"<li class='flex items-center justify-between py-2 border-b border-white/5 last:border-0'><span class='text-slate-500 font-bold w-12 text-[9px] uppercase tracking-tighter flex-shrink-0'>{a['pos']}</span><span class='text-slate-200 truncate pr-2 font-medium flex-grow leading-tight py-0.5'>{a['name']}</span><span class='{'text-sky-400' if a['pos']=='PICK' else 'text-emerald-400'} font-mono font-bold leading-tight'>{a['val']}</span></li>" for a in item['top']])
            rest_h = "".join([f"<li class='flex items-center justify-between py-2 border-b border-white/5 last:border-0'><span class='text-slate-500 font-bold w-12 text-[9px] uppercase tracking-tighter flex-shrink-0'>{a['pos']}</span><span class='text-slate-200 truncate pr-2 font-medium flex-grow leading-tight py-0.5 text-[13px]'>{a['name']}</span><span class='text-slate-400 font-mono font-bold leading-tight text-[11px]'>{a['val']}</span></li>" for a in item['rest']])
            h += f"""
            <div class="bg-[#0f0f0f] border border-slate-800 rounded-[2rem] p-5 sm:p-7 flex flex-col h-fit w-full shadow-2xl" x-data="{{ open: false }}">
                <div class="mb-5 text-center"><h2 class="text-xl sm:text-2xl font-black text-white leading-tight uppercase tracking-tighter break-words">{item['league']}</h2></div>
                <div class="flex items-stretch gap-2 mb-6">
                    <div class="w-16 sm:w-20 flex-shrink-0 flex flex-col justify-center">{l_b}</div>
                    <div class="flex-grow bg-white/5 rounded-2xl p-4 flex flex-col justify-center items-center border border-white/10">
                        <p class="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1">{item['label']}</p>
                        <p class="text-3xl sm:text-4xl font-black text-emerald-400 leading-none mb-1">{item['val']:,}</p>
                        <p class="text-[8px] text-slate-600 font-bold uppercase tracking-widest">Average Team Value</p>
                    </div>
                    <div class="w-16 sm:w-20 flex-shrink-0 flex flex-col justify-center">{r_b}</div>
                </div>
                <div class="mb-6 px-1">
                    <p class="text-[9px] text-slate-600 font-bold uppercase tracking-wider mb-0.5">Total Assets in Pool</p>
                    <p class="text-[13px] font-black text-white">{item['count']}</p>
                </div>
                <div class='flex items-center gap-2 mb-3'><p class="text-[9px] text-slate-600 font-black uppercase tracking-[0.2em]">Top 20 Assets</p><div class='h-px flex-grow bg-slate-800/50'></div></div>
                <ul class="mb-6 flex-grow">{top_h}</ul>
                <button @click="open = !open" class="w-full py-4 bg-white/5 border border-white/10 rounded-2xl text-[12px] font-black text-slate-300 uppercase tracking-widest hover:bg-white hover:text-black transition-all">
                    <span x-text="open ? 'Hide Secondary' : 'Show All Assets'"></span>
                </button>
                <div x-show="open" x-collapse class="mt-6 pt-6 border-t border-slate-800"><ul class="flex flex-col">{rest_h}</ul></div>
            </div>"""
        return h

    full_html = f"""
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>Orphan Lab - {USERNAME}</title>
    <meta property="og:title" content="Orphans in {USERNAME} leagues">
    <meta property="og:description" content="Bylaws and exact {season} pick slots available upon request. Take your pick, first to pay gets to play!">
    <meta property="og:image" content="https://{DOMAIN}/{PREVIEW_IMG}">
    <script src='https://cdn.tailwindcss.com'></script>
    <script defer src='https://unpkg.com/@alpinejs/collapse@3.x.x/dist/cdn.min.js'></script>
    <script defer src='https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js'></script>
    <style>
        * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
        html, body {{ background-color: black; color: #cbd5e1; min-height: 100%; }}
        .orphan-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 350px), 1fr)); gap: 1.5rem; width: 100%; max-width: 1200px; }}
        .tab-btn.active {{ color: white; border-bottom: 3px solid #10b981; }}
    </style>
    </head><body x-data="{{ tab: 'dispersals' }}"><div class='flex flex-col items-center p-4'>
    <header class='text-center w-full max-w-[1200px] mb-12 flex flex-col items-center'>
        <h1 class='text-6xl sm:text-8xl font-black text-white italic tracking-tighter uppercase'>ORPHAN<span class='text-emerald-500'>LAB.</span></h1>
        <div class="flex flex-wrap justify-center items-center gap-3 mt-6">
            <span class="px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[10px] font-black uppercase tracking-widest rounded-full">Commish: {USERNAME}</span>
            <a href="https://www.fantasycalc.com" target="_blank" class="px-3 py-1 bg-sky-500/10 border border-sky-500/30 text-sky-400 text-[10px] font-black uppercase tracking-widest rounded-full hover:bg-sky-500/20 transition-all">FantasyCalc Values</a>
        </div>
        <div class='flex justify-center gap-8 mt-12 border-b border-slate-900 w-full'>
            <button @click="tab = 'dispersals'" :class="tab == 'dispersals' ? 'active' : ''" class='tab-btn pb-4 font-black uppercase text-[10px] text-slate-500 tracking-widest'>Dispersals ({len(dispersals)})</button>
            <button @click="tab = 'orphans'" :class="tab == 'orphans' ? 'active' : ''" class='tab-btn pb-4 font-black uppercase text-[10px] text-slate-500 tracking-widest'>Orphans ({len(orphans)})</button>
        </div>
    </header>
    <div x-show="tab == 'dispersals'" class='orphan-grid'>{get_dispersal_cards(dispersals)}</div>
    <div x-show="tab == 'orphans'" class='orphan-grid'>{get_orphan_cards(orphans)}</div>
    <footer class="mt-20 pb-10 text-center"><p class="text-[10px] font-black text-slate-700 uppercase tracking-[0.3em]">Last Updated</p><p class="text-[12px] font-bold text-slate-500 mt-1">{last_updated}</p></footer>
    </div></body></html>"""

    if os.path.exists(DEPLOY_DIR): shutil.rmtree(DEPLOY_DIR)
    os.makedirs(DEPLOY_DIR)
    with open(os.path.join(DEPLOY_DIR, "index.html"), "w", encoding="utf-8") as f: f.write(full_html)
    if os.path.exists(os.path.join(BASE_DIR, PREVIEW_IMG)):
        shutil.copy(os.path.join(BASE_DIR, PREVIEW_IMG), os.path.join(DEPLOY_DIR, PREVIEW_IMG))

def deploy():
    print(f"🚀 Deploying to Vercel...")
    subprocess.run(f"vercel {DEPLOY_DIR} --prod --yes", shell=True)

if __name__ == "__main__":
    o, d = get_data()
    build_site(o, d)
    deploy()
