from __future__ import annotations
import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from datetime import datetime

from watchdog_telegram_sender_v1 import append_log, send_telegram, load_json
from obs_websocket_client_v1 import ObsWebSocketClient, ObsConfig

BASE_URL = "https://api.telegram.org/bot{token}/{method}"


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


class RemoteBot:
    def __init__(self):
        self.remote_cfg_path = Path(r"C:\AI\BillarLanzarote\config\telegram_remote_control_config_v1.json")
        self.remote_cfg = read_json(self.remote_cfg_path)
        if not self.remote_cfg:
            raise RuntimeError(f"Missing config: {self.remote_cfg_path}")

        self.base_cfg = read_json(Path(self.remote_cfg["telegram_base_config_path"]))
        self.token = str(self.base_cfg.get("bot_token", "")).strip()
        if not self.token:
            raise RuntimeError("Base telegram bot_token missing")
        self.primary_chat = str(self.remote_cfg["allowed_admins"]["primary_admin_chat_id"]).strip()
        self.second_chat = str(self.remote_cfg["allowed_admins"]["second_admin_chat_id"]).strip()
        self.logs = Path(self.remote_cfg["paths"]["telegram_remote_log"])
        self.audit = Path(self.remote_cfg["paths"]["command_audit_log"])
        self.state_path = Path(self.remote_cfg["paths"]["state_file"])
        self.state = read_json(self.state_path)
        self.cooldown = int(self.remote_cfg["telegram_ui"]["cooldown_seconds"])
        self.last_update_id = int(self.state.get("last_update_id", 0))
        self.allowed_second = {
            "/start", "/help", "/status", "/start_all", "/stop_all",
            "/start_stream", "/stop_stream"
        }

    def log(self, line: str):
        append_log(self.logs, line)

    def audit_log(self, line: str):
        append_log(self.audit, line)

    def save_state(self):
        self.state["last_update_id"] = self.last_update_id
        write_json(self.state_path, self.state)

    def api_call(self, method: str, data: dict | None = None):
        url = BASE_URL.format(token=self.token, method=method)
        payload = urllib.parse.urlencode(data or {}).encode("utf-8")
        with urllib.request.urlopen(url, data=payload, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))

    def get_updates(self):
        url = BASE_URL.format(token=self.token, method="getUpdates")
        params = {"timeout": 20, "offset": self.last_update_id + 1}
        payload = urllib.parse.urlencode(params).encode("utf-8")
        with urllib.request.urlopen(url, data=payload, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))

    def send_text(self, chat_id: str, text: str, reply_markup: dict | None = None):
        data = {"chat_id": chat_id, "text": text}
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)
        return self.api_call("sendMessage", data)

    def answer_callback(self, callback_query_id: str, text: str = ""):
        return self.api_call("answerCallbackQuery", {"callback_query_id": callback_query_id, "text": text})

    def allowed(self, chat_id: str, command: str) -> bool:
        if chat_id == self.primary_chat:
            return True
        if self.second_chat and self.second_chat != "SECOND_ADMIN_CHAT_ID_HERE" and chat_id == self.second_chat:
            return command in self.allowed_second
        return False

    def within_cooldown(self, key: str) -> bool:
        now = time.time()
        last = float(self.state.get(f"cooldown::{key}", 0))
        if (now - last) < self.cooldown:
            return True
        self.state[f"cooldown::{key}"] = now
        self.save_state()
        return False

    def keyboard(self):
        return {
            "keyboard": [
                [{"text": "/status"}, {"text": "/help"}],
                [{"text": "/start_all"}, {"text": "/stop_all"}],
                [{"text": "/start_stream"}, {"text": "/stop_stream"}],
                [{"text": "/scene_mesa1"}, {"text": "/scene_mesa2"}],
                [{"text": "/go_live"}, {"text": "/restart_obs"}],
                [{"text": "/restart_ai"}, {"text": "/restart_streams"}],
                [{"text": "/logs"}]
            ],
            "resize_keyboard": True,
            "is_persistent": True
        }

    def help_text(self) -> str:
        return (
            "Billar Lanzarote remote control\n\n"
            "Status / Help\n"
            "/status - full system summary\n"
            "/help - this help\n\n"
            "Control\n"
            "/start_all - start MediaMTX, OBS, AI, watchdog\n"
            "/stop_all - stop OBS and end remote controller side tasks\n"
            "/restart_obs - restart OBS\n"
            "/restart_ai - restart AI launcher path\n"
            "/restart_streams - kick MediaMTX/start stack\n\n"
            "Stream\n"
            "/start_stream - start OBS stream\n"
            "/stop_stream - stop OBS stream\n"
            "/scene_mesa1 - switch to Mesa 1\n"
            "/scene_mesa2 - switch to Mesa 2\n"
            "/go_live - choose current / Mesa 1 / Mesa 2\n\n"
            "Logs\n"
            "/logs - last watchdog / telegram lines"
        )

    def obs_client(self):
        cfg = self.remote_cfg["obs"]
        return ObsWebSocketClient(ObsConfig(
            host=cfg["host"],
            port=int(cfg["port"]),
            password=str(cfg["password"]),
            timeout=5
        ))

    def run_bat(self, path: str):
        return subprocess.run(["cmd", "/c", path], capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=180)

    def status_summary(self) -> str:
        lines = []
        health = self.remote_cfg["health_files"]
        def fresh(path):
            p = Path(path)
            return p.exists(), (time.time() - p.stat().st_mtime) if p.exists() else None

        # OBS
        obs_process = self.run_bat('tasklist /FI "IMAGENAME eq obs64.exe"')
        obs_running = "obs64.exe" in (obs_process.stdout or "").lower()
        lines.append(f"OBS process: {'OK' if obs_running else 'DOWN'}")
        try:
            ws = self.obs_client()
            ws.connect()
            stream = ws.get_stream_status().get("responseData", {})
            scene = ws.get_current_scene()
            lines.append(f"OBS websocket: OK")
            lines.append(f"OBS current scene: {scene or 'unknown'}")
            lines.append(f"OBS stream active: {stream.get('outputActive', False)}")
            ws.close()
        except Exception as e:
            lines.append(f"OBS websocket: FAIL ({e})")

        # MediaMTX
        med = self.run_bat('tasklist /FI "IMAGENAME eq mediamtx.exe"')
        med_ok = "mediamtx.exe" in (med.stdout or "").lower()
        lines.append(f"MediaMTX process: {'OK' if med_ok else 'DOWN'}")

        # JSON files
        for label, key in [("Master", "master_control"), ("System", "system_health"), ("Match", "current_match"), ("AI", "ai_state")]:
            exists, age = fresh(health[key])
            if exists:
                lines.append(f"{label} JSON: OK ({int(age)}s old)")
            else:
                lines.append(f"{label} JSON: MISSING")

        return "\n".join(lines)

    def tail_logs(self, n=30) -> str:
        parts = []
        for label, path in [
            ("Watchdog", self.remote_cfg["health_files"].get("watchdog_status", "")),
            ("Telegram", self.remote_cfg["paths"]["telegram_remote_log"]),
            ("Audit", self.remote_cfg["paths"]["command_audit_log"])
        ]:
            p = Path(path)
            if p.exists() and p.is_file():
                try:
                    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()[-n:]
                    parts.append(f"== {label} ==\n" + "\n".join(lines[-10:]))
                except Exception as e:
                    parts.append(f"== {label} ==\nERROR reading: {e}")
        return "\n\n".join(parts) if parts else "No logs found."

    def youtube_hook(self, target: str) -> str:
        cfg_path = Path(r"C:\AI\BillarLanzarote\config\youtube_live_config_v1.json")
        if not cfg_path.exists():
            return "YouTube hook skipped: config missing."
        proc = subprocess.run(
            [sys.executable, r"C:\AI\BillarLanzarote\scripts\youtube_live_transition_v1.py", str(cfg_path), target],
            capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=60
        )
        out = (proc.stdout or proc.stderr or "").strip()
        return out or "YouTube hook returned no output."

    def do_start_all(self) -> str:
        out = []
        for key in ["start_master"]:
            proc = self.run_bat(self.remote_cfg["launchers"][key])
            out.append(f"{key}: return={proc.returncode}")
            if proc.stdout.strip():
                out.append(proc.stdout.strip()[-800:])
            if proc.stderr.strip():
                out.append(proc.stderr.strip()[-800:])
        return "\n".join(out)

    def do_stop_all(self) -> str:
        results = []
        # stop OBS stream if possible
        try:
            ws = self.obs_client()
            ws.connect()
            status = ws.get_stream_status().get("responseData", {})
            if status.get("outputActive"):
                ws.stop_stream()
                results.append("OBS stream stopped.")
            ws.close()
        except Exception as e:
            results.append(f"OBS stop skipped: {e}")
        # kill obs
        subprocess.run(["taskkill", "/IM", "obs64.exe", "/F"], capture_output=True, text=True)
        results.append("OBS process kill attempted.")
        return "\n".join(results)

    def do_start_stream(self) -> str:
        ws = self.obs_client()
        ws.connect()
        ws.start_stream()
        status = ws.get_stream_status().get("responseData", {})
        scene = ws.get_current_scene()
        ws.close()
        return f"Stream start requested. Scene={scene} Active={status.get('outputActive', False)}"

    def do_stop_stream(self) -> str:
        ws = self.obs_client()
        ws.connect()
        ws.stop_stream()
        status = ws.get_stream_status().get("responseData", {})
        ws.close()
        return f"Stream stop requested. Active={status.get('outputActive', False)}"

    def do_scene(self, scene_name: str) -> str:
        ws = self.obs_client()
        ws.connect()
        ws.set_scene(scene_name)
        current = ws.get_current_scene()
        ws.close()
        return f"Scene switch requested. Current scene={current}"

    def do_go_live(self, mode: str) -> str:
        if mode in ("Mesa 1", "Mesa 2"):
            try:
                self.do_scene(mode)
            except Exception as e:
                return f"Go Live aborted: scene switch failed: {e}"
        # current mode leaves scene as-is
        start_resp = self.do_start_all()
        try:
            stream_resp = self.do_start_stream()
        except Exception as e:
            return f"Start all done, but stream start failed: {e}\n\n{start_resp}"
        yt_resp = self.youtube_hook("go_live")
        return f"{start_resp}\n\n{stream_resp}\n\n{yt_resp}"

    def process_command(self, chat_id: str, command: str) -> tuple[str, dict | None]:
        if self.within_cooldown(command):
            return "Command ignored: cooldown active. Wait a few seconds and try again.", None

        if command == "/start":
            return "Remote control online.", self.keyboard()
        if command == "/help":
            return self.help_text(), self.keyboard()
        if command == "/status":
            return self.status_summary(), self.keyboard()
        if command == "/start_all":
            return self.do_start_all(), self.keyboard()
        if command == "/stop_all":
            return self.do_stop_all(), self.keyboard()
        if command == "/start_stream":
            return self.do_start_stream(), self.keyboard()
        if command == "/stop_stream":
            return self.do_stop_stream(), self.keyboard()
        if command == "/scene_mesa1":
            return self.do_scene("Mesa 1"), self.keyboard()
        if command == "/scene_mesa2":
            return self.do_scene("Mesa 2"), self.keyboard()
        if command == "/restart_obs":
            proc = self.run_bat(self.remote_cfg["launchers"]["restart_obs"])
            return f"Restart OBS return={proc.returncode}\n{(proc.stdout or proc.stderr or '').strip()[-1200:]}", self.keyboard()
        if command == "/restart_ai":
            proc = self.run_bat(self.remote_cfg["launchers"]["restart_ai"])
            return f"Restart AI return={proc.returncode}\n{(proc.stdout or proc.stderr or '').strip()[-1200:]}", self.keyboard()
        if command == "/restart_streams":
            proc = self.run_bat(self.remote_cfg["launchers"]["start_master"])
            return f"Restart streams/master return={proc.returncode}\n{(proc.stdout or proc.stderr or '').strip()[-1200:]}", self.keyboard()
        if command == "/logs":
            return self.tail_logs(), self.keyboard()
        if command == "/go_live":
            return "Choose live target:", {
                "inline_keyboard": [
                    [{"text": "Go Live (Current Scene)", "callback_data": "go_live::current"}],
                    [{"text": "Go Live Mesa 1", "callback_data": "go_live::Mesa 1"}],
                    [{"text": "Go Live Mesa 2", "callback_data": "go_live::Mesa 2"}]
                ]
            }
        return "Unknown command.", self.keyboard()

    def process_callback(self, chat_id: str, callback_query_id: str, data: str):
        self.answer_callback(callback_query_id, "Working...")
        if data.startswith("go_live::"):
            mode = data.split("::", 1)[1]
            return self.do_go_live(mode)
        return "Unknown action."

    def run(self):
        self.log("[BOOT] Telegram remote control starting")
        self.send_text(self.primary_chat, "Billar Lanzarote Telegram remote control started.", self.keyboard())
        while True:
            try:
                updates = self.get_updates()
                for item in updates.get("result", []):
                    self.last_update_id = item["update_id"]
                    self.save_state()

                    if "message" in item:
                        msg = item["message"]
                        chat_id = str(msg.get("chat", {}).get("id", ""))
                        text = str(msg.get("text", "")).strip()
                        if not text:
                            continue
                        self.audit_log(f"{chat_id} -> {text}")
                        if not self.allowed(chat_id, text):
                            self.send_text(chat_id, "Not authorised for that action.")
                            continue
                        reply_text, markup = self.process_command(chat_id, text)
                        self.send_text(chat_id, reply_text, markup)

                    elif "callback_query" in item:
                        cb = item["callback_query"]
                        chat_id = str(cb.get("message", {}).get("chat", {}).get("id", ""))
                        data = str(cb.get("data", "")).strip()
                        self.audit_log(f"{chat_id} -> callback:{data}")
                        if not self.allowed(chat_id, "/go_live"):
                            self.answer_callback(cb["id"], "Not authorised.")
                            continue
                        reply = self.process_callback(chat_id, cb["id"], data)
                        self.send_text(chat_id, reply, self.keyboard())

                time.sleep(1)
            except KeyboardInterrupt:
                self.log("[STOP] keyboard interrupt")
                break
            except Exception as e:
                self.log(f"[ERROR] Remote bot loop error: {e}")
                time.sleep(5)


if __name__ == "__main__":
    RemoteBot().run()
