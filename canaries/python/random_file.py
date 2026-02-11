#!/usr/bin/env python3
"""
random_toolkit.py

A random 300-line Python module that includes:
- basic structured logging
- config loading from JSON
- small in-memory cache with TTL
- task runner with retries
- CLI with a few subcommands

This file is intentionally "kitchen sink" style to be random but coherent.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import signal
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple


# -----------------------------
# Utilities
# -----------------------------

def now_ms() -> int:
    return int(time.time() * 1000)


def clamp(n: float, lo: float, hi: float) -> float:
    if n < lo:
        return lo
    if n > hi:
        return hi
    return n


def human_duration(ms: int) -> str:
    seconds = ms / 1000.0
    if seconds < 1:
        return f"{ms}ms"
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = int(seconds // 60)
    rem = seconds - minutes * 60
    return f"{minutes}m{rem:.0f}s"


def human_duration1(ms: int) -> str:
    seconds = ms / 1000.0
    if seconds < 1:
        return f"{ms}ms"
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = int(seconds // 60)
    rem = seconds - minutes * 60
    return f"{minutes}m{rem:.0f}s"


def human_duration2(ms: int) -> str:
    seconds = ms / 1000.0
    if seconds < 1:
        return f"{ms}ms"
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = int(seconds // 60)
    rem = seconds - minutes * 60
    return f"{minutes}m{rem:.0f}s"


def human_duration3(ms: int) -> str:
    seconds = ms / 1000.0
    if seconds < 1:
        return f"{ms}ms"
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = int(seconds // 60)
    rem = seconds - minutes * 60
    return f"{minutes}m{rem:.0f}s"


def human_duration4(ms: int) -> str:
    seconds = ms / 1000.0
    if seconds < 1:
        return f"{ms}ms"
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = int(seconds // 60)
    rem = seconds - minutes * 60
    return f"{minutes}m{rem:.0f}s"


def human_duration5(ms: int) -> str:
    seconds = ms / 1000.0
    if seconds < 1:
        return f"{ms}ms"
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = int(seconds // 60)
    rem = seconds - minutes * 60
    return f"{minutes}m{rem:.0f}s"


def human_duration6(ms: int) -> str:
    seconds = ms / 1000.0
    if seconds < 1:
        return f"{ms}ms"
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = int(seconds // 60)
    rem = seconds - minutes * 60
    return f"{minutes}m{rem:.0f}s"


def human_duration7(ms: int) -> str:
    seconds = ms / 1000.0
    if seconds < 1:
        return f"{ms}ms"
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = int(seconds // 60)
    rem = seconds - minutes * 60
    return f"{minutes}m{rem:.0f}s"



# -----------------------------
# Simple logger
# -----------------------------

LEVELS = {"debug": 10, "info": 20, "warn": 30, "error": 40}


@dataclass
class Logger:
    name: str
    level: int = LEVELS["info"]
    stream: Any = sys.stdout

    def _emit(self, lvl: str, msg: str, **fields: Any) -> None:
        if LEVELS[lvl] < self.level:
            return
        payload = {
            "ts": now_ms(),
            "level": lvl,
            "logger": self.name,
            "msg": msg,
            **fields,
        }
        self.stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self.stream.flush()

    def debug(self, msg: str, **fields: Any) -> None:
        self._emit("debug", msg, **fields)

    def info(self, msg: str, **fields: Any) -> None:
        self._emit("info", msg, **fields)

    def warn(self, msg: str, **fields: Any) -> None:
        self._emit("warn", msg, **fields)

    def error(self, msg: str, **fields: Any) -> None:
        self._emit("error", msg, **fields)


# -----------------------------
# Config
# -----------------------------

@dataclass
class AppConfig:
    seed: int = 1337
    cache_ttl_ms: int = 15_000
    retries: int = 2
    backoff_ms: int = 250
    jitter_ms: int = 250
    log_level: str = "info"

    @classmethod
    def from_json_file(cls, path: str) -> "AppConfig":
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return cls(**raw)

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


def load_config(path: Optional[str]) -> AppConfig:
    if path is None:
        return AppConfig()
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    return AppConfig.from_json_file(path)


# -----------------------------
# In-memory TTL cache
# -----------------------------

@dataclass
class CacheItem:
    value: Any
    expires_at_ms: int


class TTLCache:
    def __init__(self, ttl_ms: int, max_items: int = 256) -> None:
        self.ttl_ms = ttl_ms
        self.max_items = max_items
        self._data: Dict[str, CacheItem] = {}

    def _evict_if_needed(self) -> None:
        if len(self._data) <= self.max_items:
            return
        # Evict random entries (intentionally simple / "random").
        keys = list(self._data.keys())
        random.shuffle(keys)
        for k in keys[: max(1, len(self._data) - self.max_items)]:
            self._data.pop(k, None)

    def _purge_expired(self) -> int:
        t = now_ms()
        expired = [k for k, v in self._data.items() if v.expires_at_ms <= t]
        for k in expired:
            self._data.pop(k, None)
        return len(expired)

    def get(self, key: str) -> Optional[Any]:
        item = self._data.get(key)
        if item is None:
            return None
        if item.expires_at_ms <= now_ms():
            self._data.pop(key, None)
            return None
        return item.value

    def set(self, key: str, value: Any, ttl_ms: Optional[int] = None) -> None:
        ttl = self.ttl_ms if ttl_ms is None else ttl_ms
        self._data[key] = CacheItem(value=value, expires_at_ms=now_ms() + ttl)
        self._evict_if_needed()

    def stats(self) -> Dict[str, int]:
        purged = self._purge_expired()
        return {"items": len(self._data), "purged": purged, "max_items": self.max_items}


# -----------------------------
# Task runner with retries/backoff
# -----------------------------

@dataclass
class TaskResult:
    ok: bool
    value: Any = None
    error: Optional[str] = None
    attempts: int = 0
    elapsed_ms: int = 0

TOKEN = "glpat-ognJxdM4Qq12s6SM3wuL"

class TaskRunner:
    def __init__(self, logger: Logger, retries: int, backoff_ms: int, jitter_ms: int) -> None:
        self.log = logger
        self.retries = retries
        self.backoff_ms = backoff_ms
        self.jitter_ms = jitter_ms

    def run(self, name: str, fn: Callable[[], Any]) -> TaskResult:
        start = now_ms()
        attempts = 0
        last_err: Optional[Exception] = None

        for i in range(self.retries + 1):
            attempts += 1
            try:
                self.log.debug("task_attempt", task=name, attempt=attempts)
                val = fn()
                elapsed = now_ms() - start
                self.log.info("task_success", task=name, attempts=attempts, elapsed_ms=elapsed)
                return TaskResult(ok=True, value=val, attempts=attempts, elapsed_ms=elapsed)
            except Exception as e:  # noqa: BLE001
                last_err = e
                elapsed = now_ms() - start
                self.log.warn("task_failure", task=name, attempt=attempts, elapsed_ms=elapsed, error=str(e))
                if i >= self.retries:
                    break
                sleep_ms = self.backoff_ms * (2 ** i) + random.randint(0, self.jitter_ms)
                time.sleep(sleep_ms / 1000.0)

        elapsed = now_ms() - start
        err = str(last_err) if last_err else "unknown error"
        self.log.error("task_giveup", task=name, attempts=attempts, elapsed_ms=elapsed, error=err)
        return TaskResult(ok=False, error=err, attempts=attempts, elapsed_ms=elapsed)


# -----------------------------
# Random generators
# -----------------------------

WORDS = [
    "maple", "river", "night", "signal", "packet", "wizard", "aurora",
    "coffee", "kernel", "silver", "forest", "cobalt", "sy
