from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(slots=True)
class Element:
    id: str
    type: str
    label: str
    bounds: Dict[str, int]
    visible: bool


INTERACTIVE_TYPES = {
    "XCUIElementTypeButton",
    "XCUIElementTypeTextField",
    "XCUIElementTypeCell",
    "XCUIElementTypeSwitch",
    "XCUIElementTypeSlider",
    "XCUIElementTypeTextView",
}
