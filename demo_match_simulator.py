
import os, sys, time, json, random, argparse

ROOT = r"C:\AI\BillarLanzarote_DEMO"
CFG = os.path.join(ROOT, "config", "demo_config.json")
STATE = os.path.join(ROOT, "state")
RUNTIME = os.path.join(ROOT, "runtime")
LOG = os.path.join(ROOT, "logs", "demo_simulator.log")
os.makedirs(STATE, exist_ok=True)
os.makedirs(RUNTIME, exist_ok=True)
os.makedirs(os.path.dirname(LOG), exist_ok=True)

PLAYERS = [
    ("Ais Eyez Bailey", "Sorin Rumpa"),
    ("Dailos Jorge Costa", "Daniel Muñoz Oliveira"),
    ("Aco", "Tito"),
    ("Leo Demo", "Dani Demo")
]
DISCIPLINES = ["8-Ball", "9-Ball", "10-Ball"]
WARNINGS = [
    "",
    "Low confidence on pocket target",
    "Cue ball pocketed • foul warning",
    "Ball cluster detected",
    "Missed shot detected",
    "Turn timer warning"
]

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

def emit_event(table_key, event_type, state):
    save_json(os.path.join(RUNTIME, f"{table_key}_event.json"), {
        "event_type": event_type,
        "table_key": table_key,
        "state": state,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    })

def run(mode):
    interval = 8 if mode == "normal" else 2
    scores = {"mesa1": [0, 0], "mesa2": [0, 0]}
    active = {"mesa1": False, "mesa2": False}
    setup = {
        "mesa1": {"name": "Mesa 1"},
        "mesa2": {"name": "Mesa 2"}
    }

    while True:
        for table_key in ["mesa1", "mesa2"]:
            if not active[table_key]:
                pa, pb = random.choice(PLAYERS)
                st = {
                    "active": True,
                    "table_name": setup[table_key]["name"],
                    "player_a": pa,
                    "player_b": pb,
                    "score_a": 0,
                    "score_b": 0,
                    "discipline": random.choice(DISCIPLINES),
                    "warning": "",
                    "mode": mode
                }
                active[table_key] = True
                scores[table_key] = [0, 0]
                save_json(os.path.join(STATE, f"{table_key}_live.json"), st)
                emit_event(table_key, "match_started", st)
                log(f"{table_key}: match started")
            else:
                st_path = os.path.join(STATE, f"{table_key}_live.json")
                st = json.load(open(st_path, "r", encoding="utf-8"))
                if random.random() < 0.18:
                    st["active"] = False
                    st["warning"] = "Match ended"
                    save_json(st_path, st)
                    emit_event(table_key, "match_ended", st)
                    active[table_key] = False
                    log(f"{table_key}: match ended")
                else:
                    who = random.choice([0, 1])
                    scores[table_key][who] += 1
                    st["score_a"] = scores[table_key][0]
                    st["score_b"] = scores[table_key][1]
                    st["warning"] = random.choice(WARNINGS)
                    save_json(st_path, st)
                    emit_event(table_key, "state_changed", st)
                    log(f"{table_key}: score {st['score_a']}-{st['score_b']}")
        time.sleep(interval)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["normal","stress"], default="normal")
    args = ap.parse_args()
    run(args.mode)
