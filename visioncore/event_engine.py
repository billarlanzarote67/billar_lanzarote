
import os, json, time, sys
table = sys.argv[1] if len(sys.argv) > 1 else "mesa1"
src = rf"C:\AI\BillarLanzarote\state\{table}_ai_state.json"
runtime = rf"C:\AI\BillarLanzarote\runtime\{table}_event.json"
last = None
print("Event engine:", table)
while True:
    try:
        with open(src, "r", encoding="utf-8") as f:
            state = json.load(f)
        motion = state.get("motion_active", False)
        event = None
        if last is False and motion is True:
            event = "shot_started"
        elif last is True and motion is False:
            event = "shot_ended"
        if event:
            payload = {"table_key": table, "event_type": event, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "state": state}
            with open(runtime, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            print(payload)
        last = motion
    except Exception as e:
        print("event_engine error:", e)
    time.sleep(1)
