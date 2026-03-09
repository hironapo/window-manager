"""
config_mgr.py - 設定管理（JSON）
"""
import json
import uuid
from pathlib import Path

DEFAULT_CONFIG = {
    "popup_hotkey": "ctrl+alt+w",
    "presets": []
}

# プリセットの layout は画面比率（0.0〜1.0）
# {
#   "id": "uuid",
#   "name": "横並び",
#   "hotkey": "ctrl+alt+1",
#   "windows": [
#     {"app": "chrome", "layout": {"x": 0.0, "y": 0.0, "w": 0.5, "h": 1.0}},
#     {"app": "notepad", "layout": {"x": 0.5, "y": 0.0, "w": 0.5, "h": 1.0}}
#   ]
# }


class ConfigManager:
    def __init__(self):
        self.config_path = Path(__file__).parent / "config.json"
        self.on_change = None
        self._load()

    def _load(self):
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            self.data = {**DEFAULT_CONFIG, "presets": []}
            self._save()

    def _save(self):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        if self.on_change:
            self.on_change()

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self._save()

    def get_presets(self):
        return self.data.get('presets', [])

    def get_preset(self, preset_id):
        for p in self.get_presets():
            if p['id'] == preset_id:
                return p
        return None

    def add_preset(self, preset):
        preset['id'] = str(uuid.uuid4())
        self.data.setdefault('presets', []).append(preset)
        self._save()
        return preset['id']

    def update_preset(self, preset_id, updates):
        presets = self.get_presets()
        for i, p in enumerate(presets):
            if p['id'] == preset_id:
                presets[i].update(updates)
                self._save()
                return True
        return False

    def delete_preset(self, preset_id):
        self.data['presets'] = [p for p in self.get_presets() if p['id'] != preset_id]
        self._save()
