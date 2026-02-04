"""
Simple state manager for pipeline resume support
"""
import json
import os
from typing import Any, Dict

STATE_PATH = 'data/results/state.json'

def load_state() -> Dict[str, Any]:
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_state(state: Dict[str, Any]):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, 'w') as f:
        json.dump(state, f, indent=2)

def get(key: str, default=None):
    s = load_state()
    return s.get(key, default)

def set_(key: str, value: Any):
    s = load_state()
    s[key] = value
    save_state(s)
