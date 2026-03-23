from __future__ import annotations
import json
import base64
import hashlib
import time
from dataclasses import dataclass
from pathlib import Path

import websocket

@dataclass
class ObsConfig:
    host: str
    port: int
    password: str
    timeout: int = 5

class ObsWebSocketClient:
    def __init__(self, cfg: ObsConfig):
        self.cfg = cfg
        self.ws = None
        self._request_id = 0

    def _next_id(self) -> str:
        self._request_id += 1
        return f"req-{self._request_id}"

    def connect(self):
        url = f"ws://{self.cfg.host}:{self.cfg.port}"
        self.ws = websocket.create_connection(url, timeout=self.cfg.timeout)
        hello = json.loads(self.ws.recv())
        if hello.get("op") != 0:
            raise RuntimeError(f"Unexpected OBS hello: {hello}")
        auth = hello.get("d", {}).get("authentication")
        identify = {"op": 1, "d": {"rpcVersion": 1}}
        if auth:
            salt = auth["salt"]
            challenge = auth["challenge"]
            secret = base64.b64encode(hashlib.sha256((self.cfg.password + salt).encode("utf-8")).digest()).decode("utf-8")
            response = base64.b64encode(hashlib.sha256((secret + challenge).encode("utf-8")).digest()).decode("utf-8")
            identify["d"]["authentication"] = response
        self.ws.send(json.dumps(identify))
        identified = json.loads(self.ws.recv())
        if identified.get("op") != 2:
            raise RuntimeError(f"OBS identify failed: {identified}")
        return True

    def close(self):
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None

    def request(self, request_type: str, request_data: dict | None = None) -> dict:
        if self.ws is None:
            self.connect()
        req_id = self._next_id()
        payload = {
            "op": 6,
            "d": {
                "requestType": request_type,
                "requestId": req_id,
                "requestData": request_data or {}
            }
        }
        self.ws.send(json.dumps(payload))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("op") == 7 and msg.get("d", {}).get("requestId") == req_id:
                return msg["d"]

    def ping(self) -> dict:
        return self.request("GetVersion")

    def get_current_scene(self) -> str:
        data = self.request("GetCurrentProgramScene")
        return data.get("responseData", {}).get("currentProgramSceneName", "")

    def set_scene(self, scene_name: str) -> dict:
        return self.request("SetCurrentProgramScene", {"sceneName": scene_name})

    def get_stream_status(self) -> dict:
        return self.request("GetStreamStatus")

    def start_stream(self) -> dict:
        return self.request("StartStream")

    def stop_stream(self) -> dict:
        return self.request("StopStream")
