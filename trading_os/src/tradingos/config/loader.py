"""YAML -> pydantic config loading with helpful errors."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel, ValidationError

from tradingos.config.schemas import GridSpec, StrategyConfig
from tradingos.core.errors import ConfigError

T = TypeVar("T", bound=BaseModel)


def load_yaml(path: Path | str) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"config file not found: {path}")
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"invalid YAML in {path}: {e}") from e
    if not isinstance(data, dict):
        raise ConfigError(f"{path} must contain a YAML mapping at top level")
    return data


def parse_model(model: type[T], data: dict[str, Any], source: str = "<dict>") -> T:
    try:
        return model.model_validate(data)
    except ValidationError as e:
        raise ConfigError(f"invalid config in {source}:\n{e}") from e


def load_strategy(path: Path | str) -> StrategyConfig:
    return parse_model(StrategyConfig, load_yaml(path), str(path))


def load_grid(path: Path | str) -> GridSpec:
    data = load_yaml(path)
    # allow `base` to be a path to a strategy yaml instead of an inline mapping
    base = data.get("base")
    if isinstance(base, str):
        base_path = Path(base)
        if not base_path.is_absolute():
            base_path = Path(path).parent / base_path
        data = {**data, "base": load_yaml(base_path)}
    return parse_model(GridSpec, data, str(path))
