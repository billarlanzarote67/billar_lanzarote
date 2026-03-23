import os, sys
from flask import Flask, request, jsonify, send_from_directory
sys.path.append(r"C:\AI\BillarLanzarote\automation")
from _shared import load_json
ROOT=r"C:\AI\BillarLanzarote"; STATE=os.path.join(ROOT,"state"); CFG=os.path.join(ROOT,"config","live_system_config.json"); WEB=os.path.join(ROOT,"overlay","web")
app=Flask(__name__, static_folder=WEB, static_url_path="")
@app.route("/overlay")
def overlay(): return send_from_directory(WEB,"overlay.html")
@app.route("/api/overlay")
def api_overlay():
    table=request.args.get("table","mesa1"); st=load_json(os.path.join(STATE,f"{table}_live.json"),{}); cfg=load_json(CFG,{}); meta=cfg.get("tables",{}).get(table,{})
    return jsonify({"table_name":meta.get("name",table),"player_a":st.get("player_a"),"player_b":st.get("player_b"),"score_a":st.get("score_a"),"score_b":st.get("score_b"),"discipline":st.get("discipline"),"challenge_url":st.get("challenge_url"),"active":st.get("active",False)})
if __name__=="__main__":
    port=load_json(CFG,{}).get("ui",{}).get("overlay_port",8789); app.run(host="127.0.0.1", port=port, debug=False)
