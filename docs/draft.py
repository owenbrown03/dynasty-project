import requests
import re
import os

# --- CONFIG ---
USERNAME = "browntown333"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DISPERSAL_FILE = os.path.join(BASE_DIR, "dispersal_leagues.txt")

def get_nfl_year():
    try:
        state = requests.get("https://api.sleeper.app/v1/state/nfl").json()
        return str(state.get("season", "2026"))
    except: return "2026"

def clean_name(name):
    """Strips @ and all whitespace for strict comparison."""
    if not name: return ""
    return re.sub(r'[@\s]', '', str(name)).lower()

def get_dispersal_config():
    config = {}
    if not os.path.exists(DISPERSAL_FILE):
        return config

    with open(DISPERSAL_FILE, "r") as f:
        content = f.read()

    blocks = re.split(r'(\d{18,19})', content)
    for i in range(1, len(blocks), 2):
        l_id = blocks[i].strip()
        order_text = blocks[i+1] if i+1 < len(blocks) else ""

        # KEY FIX: This regex captures the name but STOPS at the first space, tab, or newline
        # It handles @Orphan 4 by allowing one space only if followed by digits
        matches = re.findall(r'(\d+):\s*@([a-zA-Z0-9._-]+(?:\s\d+)?)', order_text)

        if matches:
            config[l_id] = {int(slot): val.strip() for slot, val in matches}
    return config

def run_draft_export():
    season = get_nfl_year()
    mapping_data = get_dispersal_config()

    u_data = requests.get(f"https://api.sleeper.app/v1/user/{USERNAME}").json()
    u_id = u_data.get("user_id")
    leagues = requests.get(f"https://api.sleeper.app/v1/user/{u_id}/leagues/nfl/{season}").json()

    output_path = os.path.join(BASE_DIR, "draft_output.txt")

    with open(output_path, "w", encoding="utf-8") as out:
        out.write(f"📢 FULL 2026 ROOKIE DRAFT BOARDS\n\n")

        for league in leagues:
            l_id = str(league['league_id'])
            if l_id not in mapping_data: continue

            l_name = league['name']
            slot_map = mapping_data[l_id]
            print(f"✅ Mapping {l_name}...")

            # API Data
            rosters = requests.get(f"https://api.sleeper.app/v1/league/{l_id}/rosters").json()
            users = requests.get(f"https://api.sleeper.app/v1/league/{l_id}/users").json()
            traded = requests.get(f"https://api.sleeper.app/v1/league/{l_id}/traded_picks").json()

            u_id_to_name = {u['user_id']: u['display_name'] for u in users}

            # Map Clean Names to Roster IDs
            name_to_roster = {}
            roster_to_display = {}

            for r in rosters:
                rid = r['roster_id']
                oid = r.get('owner_id')
                disp_name = u_id_to_name.get(oid, "ORPHAN")

                # Store standard clean name
                name_to_roster[clean_name(disp_name)] = rid
                # Store "orphanX" format
                name_to_roster[f"orphan{rid}"] = rid
                roster_to_display[rid] = disp_name

            out.write(f"{'='*40}\n🏆 {l_name.upper()}\n{'='*40}\n")

            num_teams = league.get('total_rosters', 12)
            num_rounds = league.get('settings', {}).get('draft_rounds', 3)

            for rd in range(1, num_rounds + 1):
                out.write(f"\nROUND {rd}\n")
                for slot in range(1, num_teams + 1):
                    assigned_in_file = slot_map.get(slot, "")

                    # Logic: Try to find the roster ID by the name in your file
                    orig_roster_id = name_to_roster.get(clean_name(assigned_in_file))

                    if orig_roster_id is None:
                        out.write(f"{rd}.{str(slot).zfill(2)}: ❓ UNKNOWN (@{assigned_in_file})\n")
                        continue

                    # Trade tracking
                    current_owner_id = orig_roster_id
                    for tp in traded:
                        if str(tp['season']) == season and int(tp['round']) == rd and int(tp['roster_id']) == orig_roster_id:
                            current_owner_id = int(tp['owner_id'])

                    # Display Labeling
                    final_name = roster_to_display.get(current_owner_id, "ORPHAN")
                    if "orphan" in final_name.lower() or final_name == "ORPHAN":
                        label = "🚩 DISPERSAL"
                    else:
                        label = f"@{final_name}"

                    out.write(f"{rd}.{str(slot).zfill(2)}: {label}\n")
            out.write("\n")

    print(f"\n🚀 SUCCESS! Output saved to: {output_path}")

if __name__ == "__main__":
    run_draft_export()
