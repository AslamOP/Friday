"""SolidWorks automation via COM API. Windows + pywin32 required."""

from __future__ import annotations

from pathlib import Path

from friday._registry import Catalog
from friday._tools import Outcome, Proc, Spec

_DOC_MAP = {"sldprt": 1, "sldasm": 2, "slddrw": 3}


def _sw():
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    app = win32com.client.Dispatch("SldWorks.Application")
    app.Visible = True
    return app


def _doc(sw):
    doc = sw.ActiveDoc
    if doc is None:
        raise RuntimeError("no active document")
    return doc


@Catalog.tag("proc", "sw_open")
class SWOpen(Proc):
    label = "sw_open"

    @property
    def spec(self) -> Spec:
        return Spec(
            name="sw_open",
            desc="Open a SolidWorks file",
            params={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Full path to .sldprt/.sldasm/.slddrw"},
                },
                "required": ["path"],
            },
        )

    def run(self, **kw) -> Outcome:
        p = Path(kw.get("path", "")).resolve()
        if not p.exists():
            return Outcome(action="sw_open", text=f"not found: {p}", ok=False)
        ext = p.suffix.lower().lstrip(".")
        dt = _DOC_MAP.get(ext)
        if dt is None:
            return Outcome(action="sw_open", text=f"unsupported: {ext}", ok=False)
        try:
            sw = _sw()
            doc = sw.OpenDoc6(str(p), dt, 0, "", 0, 0)
            if doc is None:
                return Outcome(action="sw_open", text="failed to open", ok=False)
            return Outcome(action="sw_open", text=f"opened: {doc.GetTitle()}")
        except Exception as e:
            return Outcome(action="sw_open", text=f"error: {e}", ok=False)


@Catalog.tag("proc", "sw_mass")
class SWMass(Proc):
    label = "sw_mass"

    @property
    def spec(self) -> Spec:
        return Spec(
            name="sw_mass",
            desc="Get mass properties of active document",
            params={
                "type": "object",
                "properties": {
                    "prec": {"type": "integer", "description": "Decimal places", "default": 3},
                },
            },
        )

    def run(self, **kw) -> Outcome:
        try:
            sw = _sw()
            d = _doc(sw)
            mp = d.Extension.GetMassProperties(0, 1, 0)
            if mp is None:
                return Outcome(action="sw_mass", text="no mass props", ok=False)
            prec = kw.get("prec", 3)
            f = f".{prec}f"
            lines = [
                f"Mass: {mp[0]:{f}} kg" if mp[0] else "Mass: N/A",
                f"Volume: {mp[1]:{f}} m³" if mp[1] else "Volume: N/A",
                f"Area: {mp[2]:{f}} m²" if mp[2] else "Area: N/A",
            ]
            return Outcome(action="sw_mass", text="\n".join(lines))
        except Exception as e:
            return Outcome(action="sw_mass", text=f"error: {e}", ok=False)


@Catalog.tag("proc", "sw_param")
class SWParam(Proc):
    label = "sw_param"

    @property
    def spec(self) -> Spec:
        return Spec(
            name="sw_param",
            desc="Set a dimension value by name",
            params={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "e.g. D1@Sketch1"},
                    "val": {"type": "number", "description": "Value in mm"},
                },
                "required": ["name", "val"],
            },
            sensitive=True,
        )

    def run(self, **kw) -> Outcome:
        try:
            sw = _sw()
            d = _doc(sw)
            name = kw["name"]
            val = kw["val"]
            param = d.Parameter(name)
            if param is None:
                return Outcome(action="sw_param", text=f"'{name}' not found", ok=False)
            param.SystemValue = val
            d.EditRebuild3()
            return Outcome(action="sw_param", text=f"set {name} = {val} mm")
        except Exception as e:
            return Outcome(action="sw_param", text=f"error: {e}", ok=False)


@Catalog.tag("proc", "sw_stl")
class SWSTL(Proc):
    label = "sw_stl"

    @property
    def spec(self) -> Spec:
        return Spec(
            name="sw_stl",
            desc="Export active doc to STL",
            params={
                "type": "object",
                "properties": {
                    "out": {"type": "string", "description": "Output .stl path"},
                    "quality": {"type": "string", "enum": ["coarse", "fine", "custom"], "default": "fine"},
                },
                "required": ["out"],
            },
        )

    def run(self, **kw) -> Outcome:
        try:
            sw = _sw()
            d = _doc(sw)
            out = Path(kw.get("out", "")).resolve()
            out.parent.mkdir(parents=True, exist_ok=True)
            qmap = {"coarse": 1, "fine": 3, "custom": 2}
            qual = qmap.get(kw.get("quality", "fine"), 3)
            ok = d.Extension.SaveAs(str(out), 0, 0, None, qual, 0)
            return Outcome(action="sw_stl", text=f"exported to {out}" if ok else "export failed", ok=ok)
        except Exception as e:
            return Outcome(action="sw_stl", text=f"error: {e}", ok=False)


@Catalog.tag("proc", "sw_tree")
class SWTree(Proc):
    label = "sw_tree"

    @property
    def spec(self) -> Spec:
        return Spec(
            name="sw_tree",
            desc="List feature tree of active document",
            params={"type": "object", "properties": {}},
        )

    def run(self, **kw) -> Outcome:
        def walk(folder, indent=0):
            items = []
            ch = folder.GetFirstFeature()
            while ch:
                name = ch.Name
                if ch.GetTypeName2() == "Folder":
                    sub = walk(ch.GetFeatureByTypeName("Folder"), indent + 1)
                    items.append(f"{'  ' * indent}[{name}]")
                    items.extend(sub)
                else:
                    items.append(f"{'  ' * indent}{name} ({ch.GetTypeName2()})")
                ch = ch.GetNextFeature()
            return items

        try:
            sw = _sw()
            d = _doc(sw)
            fm = d.FeatureManager
            if fm is None:
                return Outcome(action="sw_tree", text="no feature manager", ok=False)
            root = fm.GetFeatureTreeRoot()
            if root is None:
                return Outcome(action="sw_tree", text="empty tree", ok=False)
            items = walk(root)
            return Outcome(action="sw_tree", text="\n".join(items) if items else "(empty)")
        except Exception as e:
            return Outcome(action="sw_tree", text=f"error: {e}", ok=False)
