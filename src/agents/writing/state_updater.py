from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import uuid
from src.bible.models import (
    CharacterCard, ChapterMeta, Foreshadow, ForeshadowMap, ForeshadowStatus,
    ForeshadowType, HotspotMaterial, KeyEvent, MaterialStatus, NovelMeta,
)
from src.bible.writer import NovelBible

class StateUpdater:
    def __init__(self, bible: NovelBible):
        self.bible = bible

    def update(self, chapter_num: int, content: str, summary: Dict[str, Any]) -> ChapterMeta:
        word_count = summary.get("word_count", len(content))
        for cu in summary.get("character_updates", []):
            slug = cu.get("character_slug")
            if not slug:
                continue
            try:
                card = self.bible.load_character(slug)
            except Exception:
                card = CharacterCard(slug=slug, name=cu.get("name", slug))
            if cu.get("mental_change"):
                card.key_events.append(KeyEvent(chapter=chapter_num, event=f"心理变化：{cu['mental_change']}"))
            for rel in cu.get("relationship_changes", []):
                card.relationships.append(rel) if isinstance(rel, dict) else None
            for ev in cu.get("events_happened", []):
                card.key_events.append(KeyEvent(chapter=chapter_num, event=ev))
            self.bible.save_character(card)
        fm = self.bible.load_foreshadow_map()
        for nf in summary.get("new_foreshadows", []):
            fid = f"fs_{chapter_num:03d}_{uuid.uuid4().hex[:4]}"
            ftype = ForeshadowType.HEAVY if nf.get("type") == "heavy" else ForeshadowType.LIGHT
            fm.add(Foreshadow(
                id=fid, content=nf.get("content", ""), type=ftype,
                planted_chapter=chapter_num,
                related_material_id=nf.get("material_id"),
                notes=nf.get("planned_reveal_hint", ""),
            ))
        for rid in summary.get("revealed_foreshadows", []):
            fm.mark_revealed(rid, chapter_num)
        self.bible.save_foreshadow_map(fm)
        time_adv = summary.get("time_advanced", "")
        if time_adv:
            self.bible.save_timeline(f"- 第{chapter_num}章：{time_adv}")
        for mid in summary.get("used_materials", []):
            h = self.bible.load_hotspot(mid)
            if h:
                h.status = MaterialStatus.USED
                h.used_in_chapter = chapter_num
                self.bible.save_hotspot(h)
        title = f"第{chapter_num}章"
        for line in content.split("\n"):
            if line.strip().startswith("#"):
                title = line.strip().lstrip("#").strip()
                break
        meta = ChapterMeta(
            number=chapter_num, title=title, word_count=word_count,
            summary=summary.get("chapter_event_summary", ""),
            used_materials=summary.get("used_materials", []),
            planted_foreshadows=[nf.get("content","") for nf in summary.get("new_foreshadows",[])],
            revealed_foreshadows=summary.get("revealed_foreshadows", []),
        )
        self.bible.save_chapter(chapter_num, content, meta)
        return meta
