from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Callable, Dict, List, Optional

from .models import INTERACTIVE_TYPES


class InterfaceElementProcessor:
    def __init__(self) -> None:
        self._xml_filters: List[Callable[[ET.Element], bool]] = [
            self._filter_zero_size,
            self._filter_invisible,
            self._filter_non_interactive_noise,
        ]

    def filter_page_source(self, xml_text: str) -> str:
        try:
            root = ET.fromstring(xml_text)
        except Exception:
            return xml_text

        type_map = {
            "Other": "Node",
            "Icon": "ImageNode",
            "StaticText": "TextNode",
            "Button": "ButtonNode",
            "TextField": "InputNode",
            "Image": "ImageNode",
            "Cell": "CellNode",
            "Window": "WindowNode",
            "Application": "AppNode",
            "PageIndicator": "IndicatorNode",
            "StatusBar": "StatusNode",
        }

        def node_pass(e: ET.Element) -> bool:
            for predicate in self._xml_filters:
                try:
                    if not predicate(e):
                        return False
                except Exception:
                    return False
            return True

        def clone(
            e: ET.Element, parent_bounds: Optional[Dict[str, int]] = None
        ) -> Optional[ET.Element]:
            children_clones = []
            for c in list(e):
                cloned_child = clone(
                    c,
                    {
                        "x": int(e.attrib.get("x", "0") or 0),
                        "y": int(e.attrib.get("y", "0") or 0),
                        "width": int(e.attrib.get("width", "0") or 0),
                        "height": int(e.attrib.get("height", "0") or 0),
                    }
                )
                if cloned_child is not None:
                    children_clones.append(cloned_child)
            if not node_pass(e) and not children_clones:
                return None
            type_attr = e.attrib.get("type", "").replace("XCUIElementType", "")
            new_tag = type_map.get(type_attr, "Node")
            new_elem = ET.Element(new_tag)
            copy_keys = [
                "name",
                "label",
                "value",
                "x",
                "y",
                "width",
                "height",
                "visible",
                "enabled",
                "accessible",
            ]
            for k in copy_keys:
                if k in e.attrib:
                    v = e.attrib[k]
                    if v != "":
                        if k in ["visible", "enabled"] and v.lower() == "true":
                            continue
                        elif k == "accessible" and v.lower() == "false":
                            continue
                        new_elem.set(k, v)
            if parent_bounds is not None:
                same_pos = (
                    int(e.attrib.get("x", "0") or 0) == parent_bounds["x"]
                    and int(e.attrib.get("y", "0") or 0) == parent_bounds["y"]
                    and int(e.attrib.get("width", "0") or 0)
                    == parent_bounds["width"]
                    and int(e.attrib.get("height", "0") or 0)
                    == parent_bounds["height"]
                )
                if same_pos:
                    for coord_key in ("x", "y", "width", "height"):
                        if coord_key in new_elem.attrib:
                            del new_elem.attrib[coord_key]
            for k in list(new_elem.attrib.keys()):
                if new_elem.attrib[k] == "":
                    del new_elem.attrib[k]
            for cc in children_clones:
                new_elem.append(cc)
            return new_elem

        filtered_root = clone(root, None)
        if filtered_root is None:
            return "<EMPTY/>"
        return ET.tostring(filtered_root, encoding="unicode")

    def _get_int(self, elem: ET.Element, key: str) -> int:
        try:
            return int(elem.attrib.get(key, "0"))
        except ValueError:
            return 0

    def _filter_zero_size(self, e: ET.Element) -> bool:
        w = self._get_int(e, "width")
        h = self._get_int(e, "height")
        return w > 0 and h > 0

    def _filter_invisible(self, e: ET.Element) -> bool:
        visible = e.attrib.get("visible")
        if visible is None:
            return True
        return visible.lower() == "true"

    def _filter_non_interactive_noise(self, e: ET.Element) -> bool:
        t = e.attrib.get("type") or e.tag
        label = (e.attrib.get("label") or e.attrib.get("name") or "").strip()
        value = (e.attrib.get("value") or "").strip()
        accessible = e.attrib.get("accessible", "false").lower() == "true"
        enabled = e.attrib.get("enabled", "true").lower() == "true"
        interactive = t in INTERACTIVE_TYPES or accessible or enabled
        meaningful = bool(label or value)
        has_children = len(list(e)) > 0
        if not interactive and not meaningful and not has_children:
            return False
        return True
