import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
import frontmatter
from src.bible.models import (
    CharacterCard, ChapterMeta, Correction, ForeshadowMap, HotspotMaterial,
    NovelMeta, NovelStatus, ChapterWritingConfig, MaterialStatus,
)
from src.bible.reader import BibleReader
from src.utils.git import GitManager

class NovelBible(BibleReader):
    @classmethod
    def create(cls, workspace_root: Path, novel_slug: str, title: str, author_style_slug: str = None) -> "NovelBible":
        novels_dir = Path(workspace_root) / "novels"
        root = novels_dir / novel_slug
        bible = cls(root)
        bible.init_directory_structure()
        meta = NovelMeta(novel_slug=novel_slug, title=title, status=NovelStatus.PLANNING)
        if author_style_slug:
            meta.author_style_source = [author_style_slug]
            author_src = Path(workspace_root) / "authors" / author_style_slug
            if author_src.exists():
                for f in author_src.glob("*.md"):
                    shutil.copy2(f, bible._p("author_style") / f.name)
                corr = author_src / "corrections.json"
                if corr.exists():
                    shutil.copy2(corr, bible._p("author_style") / "corrections.json")
        bible.save_meta(meta)
        bible._write_default_files()
        gm = GitManager(root)
        gm.init()
        gm.commit_all("init: novel bible created")
        return bible

    @classmethod
    def load(cls, workspace_root: Path, novel_slug: str) -> "NovelBible":
        root = Path(workspace_root) / "novels" / novel_slug
        if not root.exists():
            raise FileNotFoundError(f"Novel not found: {root}")
        return cls(root)

    def init_directory_structure(self):
        dirs = [
            "author_style", "worldbuilding", "characters", "plot", "plot/chapter_outlines",
            "material_library", "material_library/hotspots", "chapters", "drafts",
            "editor_ideas",
        ]
        for d in dirs:
            self._p(d).mkdir(parents=True, exist_ok=True)

    def _write_default_files(self):
        for fn in ["setting.md", "power_system.md", "locations.md"]:
            p = self._p("worldbuilding", fn)
            if not p.exists():
                p.write_text(f"# {fn.replace('.md','')}\n\n", encoding="utf-8")
        for fn in ["outline.md"]:
            p = self._p("plot", fn)
            if not p.exists():
                p.write_text("# 大纲\n\n", encoding="utf-8")
        tl = self._p("plot", "timeline.md")
        if not tl.exists():
            tl.write_text("# 时间线\n\n", encoding="utf-8")
        fm = self._p("plot", "foreshadow_map.json")
        if not fm.exists():
            fm.write_text("[]", encoding="utf-8")
        for fn in ["pending.md", "applied.md", "rejected.md"]:
            p = self._p("editor_ideas", fn)
            if not p.exists():
                title = {"pending.md": "待决策想法", "applied.md": "已落地想法", "rejected.md": "已放弃想法"}[fn]
                p.write_text(f"# {title}\n\n", encoding="utf-8")
        corr = self._p("author_style", "corrections.json")
        if not corr.exists():
            corr.write_text("[]", encoding="utf-8")

    def save_meta(self, meta: NovelMeta):
        meta.updated_at = datetime.now()
        self._p("meta.json").write_text(
            json.dumps(meta.model_dump(), indent=2, ensure_ascii=False, default=str),
            encoding="utf-8"
        )

    def save_character(self, card: CharacterCard):
        lines = [f"# {card.name}", ""]
        lines.append("## 基础信息")
        lines.append(f"- 身份：{card.basic_info.occupation or '待补充'}")
        if card.basic_info.age:
            lines.append(f"- 年龄：{card.basic_info.age}")
        if card.basic_info.gender:
            lines.append(f"- 性别：{card.basic_info.gender}")
        lines.append(f"- 定位：{card.basic_info.role}")
        lines.append("")
        lines.append("## 核心性格")
        for pt in card.personality_traits:
            ex = f"：{pt.get('example','')}" if pt.get("example") else ""
            lines.append(f"- {pt.get('trait','')}{ex}")
        lines.append("")
        lines.append("## 说话方式")
        lines.append("（待补充具体说话方式）")
        lines.append("")
        lines.append("## 人物关系")
        for r in card.relationships:
            lines.append(f"- {r.get('with','')}：{r.get('desc','')}")
        lines.append("")
        lines.append("## 成长弧线")
        lines.append(str(card.arc) if card.arc else "（待补充）")
        lines.append("")
        lines.append("## OOC红线")
        for r in card.ooc_redlines:
            lines.append(f"- 绝对不会：{r}")
        lines.append("")
        lines.append("## 已发生关键事件")
        for e in card.key_events:
            lines.append(f"- 第{e.chapter}章：{e.event} {('- '+e.impact) if e.impact else ''}")
        lines.append("")
        self.character_path(card.slug).write_text("\n".join(lines), encoding="utf-8")

    def save_style_layer(self, layer_name: str, content: str):
        self._p("author_style", f"{layer_name}.md").write_text(content, encoding="utf-8")

    def save_chapter(self, num: int, content: str, chapter_meta: ChapterMeta = None):
        self.chapter_path(num).write_text(content, encoding="utf-8")
        if chapter_meta:
            meta = self.load_meta()
            meta.current_chapter = max(meta.current_chapter, num)
            self.save_meta(meta)

    def save_worldbuilding(self, file_name: str, content: str):
        self._p("worldbuilding", file_name).write_text(content, encoding="utf-8")

    def save_outline(self, content: str):
        self.save_worldbuilding("outline.md", content)

    def save_timeline(self, content: str):
        p = self._p("plot", "timeline.md")
        existing = p.read_text(encoding="utf-8") if p.exists() else "# 时间线\n\n"
        p.write_text(existing.rstrip() + "\n" + content + "\n", encoding="utf-8")

    def save_chapter_outline(self, num: int, content: str):
        p = self._p("plot", "chapter_outlines", f"outline_{num:03d}.md")
        p.write_text(content, encoding="utf-8")

    def save_foreshadow_map(self, fm: ForeshadowMap):
        self._p("plot", "foreshadow_map.json").write_text(
            json.dumps(fm.to_json(), indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def save_hotspot(self, m: HotspotMaterial):
        p = self.hotspot_path(m.id)
        post = frontmatter.Post(m.core_fact, **{
            "id": m.id,
            "title": m.title, "source": m.source, "category": m.category,
            "emotion_tags": m.emotion_tags, "core_conflict": m.core_conflict,
            "fictionable_points": m.fictionable_points, "predicted_trends": m.predicted_trends,
            "fictionable_score": m.fictionable_score, "related_characters": m.related_characters,
            "status": m.status.value if hasattr(m.status, 'value') else m.status,
            "used_in_chapter": m.used_in_chapter,
            "collected_at": m.collected_at.isoformat() if hasattr(m.collected_at, 'isoformat') else str(m.collected_at),
        })
        p.write_text(frontmatter.dumps(post), encoding="utf-8")

    def append_pending_idea(self, content: str):
        p = self._p("editor_ideas", "pending.md")
        existing = p.read_text(encoding="utf-8") if p.exists() else "# 待决策想法\n\n"
        p.write_text(existing.rstrip() + f"\n- {content}\n", encoding="utf-8")

    def load_pending_ideas(self) -> str:
        p = self._p("editor_ideas", "pending.md")
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def _move_idea(self, content: str, src: str, dst: str, reason: str = ""):
        src_p = self._p("editor_ideas", src)
        dst_p = self._p("editor_ideas", dst)
        src_text = src_p.read_text(encoding="utf-8") if src_p.exists() else ""
        dst_text = dst_p.read_text(encoding="utf-8") if dst_p.exists() else f"# {dst.replace('.md','')}\n\n"
        line = f"- {content}"
        if reason:
            line += f"（原因：{reason}）"
        src_text = src_text.replace(f"- {content}", "").replace("\n\n\n", "\n\n")
        src_p.write_text(src_text, encoding="utf-8")
        dst_p.write_text(dst_text.rstrip() + "\n" + line + "\n", encoding="utf-8")

    def move_idea_to_applied(self, content: str):
        self._move_idea(content, "pending.md", "applied.md")

    def move_idea_to_rejected(self, content: str, reason: str):
        self._move_idea(content, "pending.md", "rejected.md", reason)

    def save_draft(self, chapter_num: int, content: str, reason: str):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        p = self._p("drafts", f"chapter_{chapter_num:03d}_{ts}.md")
        header = f"<!-- 废弃原因：{reason} -->\n\n"
        p.write_text(header + content, encoding="utf-8")

    def list_drafts(self):
        d = self._p("drafts")
        if not d.exists():
            return []
        return sorted([p.name for p in d.glob("*.md")])

    def move_chapter_to_drafts(self, chapter_num: int, reason: str):
        p = self.chapter_path(chapter_num)
        if p.exists():
            self.save_draft(chapter_num, p.read_text(encoding="utf-8"), reason)
            p.unlink()

    def git_commit(self, message: str):
        gm = GitManager(self.root)
        if not gm.is_repo():
            gm.init()
        return gm.commit_all(message)
