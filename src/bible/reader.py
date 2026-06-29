import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import frontmatter
from src.bible.models import CharacterCard, Character, ForeshadowMap, HotspotMaterial, NovelMeta, KeyEvent

class BibleReader:
    def __init__(self, novel_root: Path):
        self.root = Path(novel_root)

    def _p(self, *parts) -> Path:
        return self.root.joinpath(*parts)

    def load_meta(self) -> NovelMeta:
        p = self._p("meta.json")
        if not p.exists():
            raise FileNotFoundError(f"meta.json not found at {p}")
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return NovelMeta(**data)

    def load_character(self, slug: str) -> CharacterCard:
        p = self._p("characters", f"{slug}.md")
        if not p.exists():
            return CharacterCard(slug=slug, name=slug, basic_info=Character(name=slug))
        content = p.read_text(encoding="utf-8")
        lines = content.split("\n")
        name = slug
        personality = []
        speech = {}
        relationships = []
        arc = {}
        ooc = []
        events = []
        current_section = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("# "):
                name = stripped[2:].strip()
                current_section = None
            elif stripped.startswith("## "):
                sec = stripped[3:].strip()
                if "性格" in sec or "特质" in sec:
                    current_section = "personality"
                elif "说话" in sec or "语言" in sec:
                    current_section = "speech"
                elif "关系" in sec:
                    current_section = "relationships"
                elif "成长" in sec or "弧线" in sec:
                    current_section = "arc"
                elif "红线" in sec or "OOC" in sec:
                    current_section = "ooc"
                elif "事件" in sec or "经历" in sec:
                    current_section = "events"
                else:
                    current_section = None
            elif stripped.startswith("- ") and current_section:
                item = stripped[2:].strip()
                if current_section == "ooc":
                    ooc.append(item)
                elif current_section == "personality":
                    if "：" in item:
                        k, v = item.split("：", 1)
                        personality.append({"trait": k.strip(), "example": v.strip()})
                    else:
                        personality.append({"trait": item, "example": ""})
                elif current_section == "events":
                    if "：" in item:
                        k, v = item.split("：", 1)
                        try:
                            ch = int(k.replace("第", "").replace("章", "").strip())
                            events.append({"chapter": ch, "event": v.strip(), "impact": ""})
                        except ValueError:
                            events.append({"chapter": 0, "event": item, "impact": ""})
            elif stripped.startswith("- ") and current_section == "relationships":
                if "：" in stripped[2:]:
                    k, v = stripped[2:].split("：", 1)
                    relationships.append({"with": k.strip(), "desc": v.strip()})
        info = Character(name=name)
        return CharacterCard(
            slug=slug, name=name, basic_info=info,
            personality_traits=personality, speech_patterns=speech,
            relationships=relationships, arc=arc, ooc_redlines=ooc,
            key_events=[KeyEvent(**e) for e in events],
        )

    def list_characters(self) -> List[str]:
        d = self._p("characters")
        if not d.exists():
            return []
        return [p.stem for p in d.glob("*.md")]

    def load_style_layer(self, layer_name: str) -> str:
        p = self._p("author_style", f"{layer_name}.md")
        if not p.exists():
            return ""
        return p.read_text(encoding="utf-8")

    def load_all_style_rules(self) -> Dict[str, str]:
        layers = ["layer0_redlines", "layer1_meta", "layer2_prose_dna",
                  "layer3_characters", "layer4_structure", "layer5_antipatterns"]
        return {l: self.load_style_layer(l) for l in layers}

    def load_chapter(self, num: int) -> str:
        p = self._p("chapters", f"chapter_{num:03d}.md")
        if not p.exists():
            return ""
        return p.read_text(encoding="utf-8")

    def get_latest_chapter_num(self) -> int:
        d = self._p("chapters")
        if not d.exists():
            return 0
        chapters = list(d.glob("chapter_*.md"))
        if not chapters:
            return 0
        nums = []
        for c in chapters:
            try:
                nums.append(int(c.stem.split("_")[1]))
            except (IndexError, ValueError):
                pass
        return max(nums) if nums else 0

    def load_worldbuilding(self, file_name: str) -> str:
        p = self._p("worldbuilding", file_name)
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def load_outline(self) -> str:
        return self.load_worldbuilding("outline.md")

    def load_timeline(self) -> str:
        p = self._p("plot", "timeline.md")
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def load_chapter_outline(self, num: int) -> str:
        p = self._p("plot", "chapter_outlines", f"outline_{num:03d}.md")
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def load_foreshadow_map(self) -> ForeshadowMap:
        p = self._p("plot", "foreshadow_map.json")
        if not p.exists():
            return ForeshadowMap()
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ForeshadowMap.from_json(data)

    def load_hotspot(self, hotspot_id: str) -> Optional[HotspotMaterial]:
        p = self._p("material_library", "hotspots", f"{hotspot_id}.md")
        if not p.exists():
            return None
        post = frontmatter.load(str(p))
        data = dict(post.metadata)
        data["core_fact"] = post.content
        return HotspotMaterial(**data)

    def list_hotspots(self) -> List[str]:
        d = self._p("material_library", "hotspots")
        if not d.exists():
            return []
        return [p.stem for p in d.glob("*.md")]

    def chapter_path(self, num: int) -> Path:
        return self._p("chapters", f"chapter_{num:03d}.md")

    def character_path(self, slug: str) -> Path:
        return self._p("characters", f"{slug}.md")

    def hotspot_path(self, hid: str) -> Path:
        return self._p("material_library", "hotspots", f"{hid}.md")
