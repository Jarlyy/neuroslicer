from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import configparser
import json
import re


@dataclass(frozen=True)
class ProfileChange:
    parameter: str
    old_value: str
    new_value: str
    reason: str


class ProfileManager:
    def __init__(self, parameters: dict[str, str], source_format: str):
        self.parameters = parameters
        self.source_format = source_format

    @classmethod
    def load(cls, path: str | Path) -> "ProfileManager":
        path = Path(path)
        suffix = path.suffix.lower()
        if suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            parameters = {str(k): str(v) for k, v in payload.items()}
            return cls(parameters, "json")

        if suffix in {".ini", ".cfg"}:
            parser = configparser.ConfigParser()
            parser.read(path, encoding="utf-8")
            parameters: dict[str, str] = {}
            for section in parser.sections():
                for key, value in parser[section].items():
                    parameters[key] = value
            return cls(parameters, "ini")

        raise ValueError(f"Unsupported profile format: {path.suffix}")

    def save(self, path: str | Path) -> None:
        path = Path(path)
        if self.source_format == "json":
            path.write_text(json.dumps(self.parameters, ensure_ascii=False, indent=2), encoding="utf-8")
            return

        if self.source_format == "ini":
            parser = configparser.ConfigParser()
            parser["profile"] = self.parameters
            with path.open("w", encoding="utf-8") as f:
                parser.write(f)
            return

        raise ValueError(f"Unsupported profile format: {self.source_format}")

    def apply_changes(self, changes: list[ProfileChange]) -> list[ProfileChange]:
        applied: list[ProfileChange] = []
        for change in changes:
            if change.parameter not in self.parameters:
                continue
            self.parameters[change.parameter] = change.new_value
            applied.append(change)
        return applied


class ProfileAdvisor:
    def suggest_changes(self, defect_type: str, parameters: dict[str, str]) -> list[ProfileChange]:
        defect = defect_type.lower()
        if defect == "layer separation":
            return _layer_separation_changes(parameters)
        if defect == "stringing":
            return _stringing_changes(parameters)
        if defect == "poor bed adhesion":
            return _bed_adhesion_changes(parameters)
        return []


def _layer_separation_changes(parameters: dict[str, str]) -> list[ProfileChange]:
    changes: list[ProfileChange] = []
    changes.extend(_delta_numeric(parameters, "nozzle_temperature", 10.0, "Увеличить межслойную адгезию"))
    changes.extend(_set_value_if_exists(parameters, "fan_speed_first_layer", "0", "Снизить обдув первых слоев"))
    changes.extend(_scale_numeric(parameters, "print_speed", 0.8, "Снизить скорость для лучшей спайки слоев"))
    return changes


def _stringing_changes(parameters: dict[str, str]) -> list[ProfileChange]:
    changes: list[ProfileChange] = []
    changes.extend(_delta_numeric(parameters, "retraction_distance", 0.5, "Увеличить ретракт для уменьшения нитей"))
    changes.extend(_delta_numeric(parameters, "nozzle_temperature", -5.0, "Уменьшить соплетечение"))
    changes.extend(_delta_numeric(parameters, "travel_speed", 20.0, "Быстрее перемещения без экструзии"))
    return changes


def _bed_adhesion_changes(parameters: dict[str, str]) -> list[ProfileChange]:
    changes: list[ProfileChange] = []
    changes.extend(_delta_numeric(parameters, "bed_temperature", 5.0, "Улучшить прилипание первого слоя"))
    changes.extend(_scale_numeric(parameters, "first_layer_speed", 0.8, "Замедлить первый слой для адгезии"))
    return changes


def _set_value_if_exists(parameters: dict[str, str], key: str, value: str, reason: str) -> list[ProfileChange]:
    if key not in parameters:
        return []
    return [ProfileChange(parameter=key, old_value=parameters[key], new_value=value, reason=reason)]


def _delta_numeric(parameters: dict[str, str], key: str, delta: float, reason: str) -> list[ProfileChange]:
    old = _extract_numeric(parameters.get(key))
    if old is None:
        return []
    new = old + delta
    return [ProfileChange(parameter=key, old_value=parameters[key], new_value=_format_num(new), reason=reason)]


def _scale_numeric(parameters: dict[str, str], key: str, factor: float, reason: str) -> list[ProfileChange]:
    old = _extract_numeric(parameters.get(key))
    if old is None:
        return []
    new = old * factor
    return [ProfileChange(parameter=key, old_value=parameters[key], new_value=_format_num(new), reason=reason)]


def _extract_numeric(value: str | None) -> float | None:
    if value is None:
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", value)
    if not m:
        return None
    return float(m.group(0))


def _format_num(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")
