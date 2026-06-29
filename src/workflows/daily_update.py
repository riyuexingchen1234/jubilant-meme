import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.llm.base import BaseLLMClient
from src.bible.writer import NovelBible
from src.bible.models import HotspotMaterial, MaterialStatus, NovelStatus
from src.agents.writing.hotspot_collector import HotspotCollectorAgent
from src.agents.writing.material_matcher import MaterialMatcherAgent
from src.agents.writing.outline_writer import OutlineWriterAgent
from src.agents.writing.writer import WriterAgent
from src.agents.writing.style_reviewer import StyleReviewer
from src.agents.writing.logic_reviewer import LogicReviewer
from src.agents.writing.rationality_reviewer import RationalityReviewer
from src.agents.writing.review_aggregator import ReviewAggregator
from src.agents.writing.state_updater import StateUpdater

class DailyUpdateWorkflow:
    def __init__(self, llm_client: BaseLLMClient, workspace_root: Path, novel_slug: str):
        self.llm = llm_client
        self.workspace = Path(workspace_root)
        self.novel_slug = novel_slug
        self.bible = NovelBible.load(workspace_root, novel_slug)
        self._init_agents()
        self._ensure_style_rules()

    def _init_agents(self):
        self.hotspot_collector = HotspotCollectorAgent(self.llm)
        self.material_matcher = MaterialMatcherAgent(self.llm)
        self.outline_writer = OutlineWriterAgent(self.llm)
        self.writer = WriterAgent(self.llm)
        self.style_reviewer = StyleReviewer(self.llm)
        self.logic_reviewer = LogicReviewer(self.llm)
        self.rationality_reviewer = RationalityReviewer(self.llm)
        self.review_aggregator = ReviewAggregator()
        self.state_updater = StateUpdater(self.bible)

    def _ensure_style_rules(self):
        style_dir = self.bible._p("author_style")
        layers = ["layer0_redlines","layer1_meta","layer2_prose_dna","layer3_characters","layer4_structure","layer5_antipatterns"]
        missing = [l for l in layers if not (style_dir / f"{l}.md").exists()]
        meta = self.bible.load_meta()
        if missing and meta.author_style_source:
            author_dir = self.workspace / "authors" / meta.author_style_source[0]
            if author_dir.exists():
                for l in layers:
                    src = author_dir / f"{l}.md"
                    dst = style_dir / f"{l}.md"
                    if src.exists() and not dst.exists():
                        import shutil
                        shutil.copy2(src, dst)

    def add_hotspot(self, text: str) -> HotspotMaterial:
        result = self.hotspot_collector.run(raw_text=text)
        hid = result.get("id", f"hs_{uuid.uuid4().hex[:8]}")
        material = HotspotMaterial(
            id=hid,
            title=result.get("title","未命名热点"),
            category=result.get("category","社会"),
            emotion_tags=result.get("emotion_tags",[]),
            core_fact=result.get("core_fact",""),
            core_conflict=result.get("core_conflict",""),
            fictionable_points=result.get("fictionable_points",[]),
            predicted_trends=result.get("predicted_trends",[]),
            fictionable_score=result.get("fictionable_score",5),
        )
        self.bible.save_hotspot(material)
        return material

    def _load_style_rules_text(self) -> str:
        layers = self.bible.load_all_style_rules()
        parts = []
        for name, content in layers.items():
            if content:
                parts.append(f"# {name}\n{content}")
        return "\n\n".join(parts)

    def _load_characters_text(self, slugs: List[str]) -> str:
        parts = []
        for slug in slugs:
            try:
                card = self.bible.load_character(slug)
                parts.append(f"## {card.name}\nOOC红线：{', '.join(card.ooc_redlines) if card.ooc_redlines else '无'}\n")
            except Exception:
                pass
        return "\n".join(parts) if parts else "（暂无人物卡）"

    def write_next_chapter(self, materials: List[str] = None) -> Dict[str, Any]:
        meta = self.bible.load_meta()
        if meta.status != NovelStatus.WRITING:
            meta.status = NovelStatus.WRITING
            self.bible.save_meta(meta)
        next_ch = meta.current_chapter + 1
        max_retries = meta.config.max_retries_per_chapter
        style_rules = self._load_style_rules_text()
        prev_ending = self.bible.load_chapter(meta.current_chapter) if meta.current_chapter > 0 else self.bible.load_outline()[:500]
        if prev_ending and len(prev_ending) > 1000:
            prev_ending = prev_ending[-1000:]
        planted_fs = self.bible.load_foreshadow_map().get_planted()
        fs_text = json.dumps([f.model_dump() for f in planted_fs], ensure_ascii=False, default=str) if planted_fs else "无"
        hotspot_ids = materials if materials else self.bible.list_hotspots()[-5:]
        hotspots_data = []
        for hid in hotspot_ids:
            h = self.bible.load_hotspot(hid)
            if h:
                hotspots_data.append(h.model_dump())
        hotspots_json = json.dumps(hotspots_data, ensure_ascii=False, default=str) if hotspots_data else "无"
        current_plot = f"当前第{next_ch}章，总进度：{meta.current_chapter}/{meta.config.chapter_word_count_target[1]}字/章"
        chars_text = "出场人物待大纲确定"
        match_result = self.material_matcher.run(
            current_plot=current_plot,
            characters=chars_text,
            foreshadows=fs_text,
            hotspots_json=hotspots_json,
        )
        class_a = match_result.get("class_a", [])
        class_b = match_result.get("class_b", [])
        final_content = None
        final_summary = None
        verdict = "rewrite"
        retries = 0
        while retries < max_retries:
            retries += 1
            print(f"  尝试第{retries}次...")
            outline_result = self.outline_writer.run(
                style_rules=style_rules,
                outline=self.bible.load_outline()[:3000],
                prev_chapter_ending=prev_ending,
                class_a_materials=json.dumps(class_a, ensure_ascii=False),
                class_b_materials=json.dumps(class_b, ensure_ascii=False),
                characters=chars_text,
                foreshadows_to_reveal=fs_text,
                novel_time=meta.novel_current_time or "待定",
                target_word_count=meta.config.chapter_word_count_target[1],
            )
            if outline_result.get("blocked"):
                print(f"  大纲被阻塞：{outline_result.get('block_reason','')}")
                if retries >= max_retries:
                    return {"success": False, "chapter": next_ch, "error": outline_result.get("block_reason","大纲阻塞")}
                continue
            write_result = self.writer.run(
                style_rules=style_rules,
                outline=json.dumps(outline_result, ensure_ascii=False),
                characters=chars_text,
                prev_chapter_ending=prev_ending,
                materials=json.dumps(class_a + class_b, ensure_ascii=False),
                foreshadows=fs_text,
            )
            if write_result.get("blocked"):
                print(f"  写作被阻塞：{write_result.get('block_reason','')}")
                continue
            content = write_result.get("content", "")
            summary = write_result.get("chapter_summary", {})
            if not content or len(content) < 500:
                continue
            style_rev = self.style_reviewer.run(
                style_rules=style_rules,
                character_cards=chars_text,
                chapter_content=content,
            )
            logic_rev = self.logic_reviewer.run(
                characters="（全部人物卡）",
                timeline=self.bible.load_timeline()[:1000],
                foreshadow_map=fs_text,
                prev_chapters_summaries="",
                chapter_content=content,
            )
            rat_rev = self.rationality_reviewer.run(
                outline=json.dumps(outline_result, ensure_ascii=False),
                materials_used=json.dumps(class_a, ensure_ascii=False),
                character_cards=chars_text,
                chapter_content=content,
            )
            agg = self.review_aggregator.aggregate(style_rev, logic_rev, rat_rev)
            verdict = agg["verdict"]
            if verdict == "pass":
                final_content = content
                final_summary = summary
                break
            elif verdict == "revise":
                revise_prompt = "请根据以下审稿意见修改本章：\n" + json.dumps(agg["general_issues"], ensure_ascii=False, indent=2)
                write_result2 = self.writer.call_llm(
                    self.writer.system_prompt(
                        style_rules=style_rules, outline=json.dumps(outline_result, ensure_ascii=False),
                        characters=chars_text, prev_chapter_ending=prev_ending,
                        materials=json.dumps(class_a+class_b, ensure_ascii=False), foreshadows=fs_text,
                    ),
                    revise_prompt + "\n\n原文：\n" + content,
                    temperature=0.7,
                )
                parsed2 = self.writer.parse_response(write_result2)
                content2 = parsed2.get("content", content)
                summary2 = parsed2.get("chapter_summary", summary)
                if len(content2) > 500:
                    content, summary = content2, summary2
                final_content = content
                final_summary = summary
                break
            else:
                print(f"  需要重写：{[i.get('issue','') for i in agg['fatal_issues']]}")
                continue
        if not final_content:
            return {"success": False, "chapter": next_ch, "error": f"经过{retries}次尝试仍未通过审稿"}
        self.state_updater.update(next_ch, final_content, final_summary or {})
        self.bible.git_commit(f"feat: write chapter {next_ch}")
        return {
            "success": True,
            "chapter_number": next_ch,
            "verdict": verdict,
            "word_count": len(final_content),
            "retry_count": retries,
            "content_preview": final_content[:500],
        }

    def get_status(self) -> Dict[str, Any]:
        meta = self.bible.load_meta()
        return {
            "title": meta.title,
            "slug": meta.novel_slug,
            "status": meta.status,
            "current_chapter": meta.current_chapter,
            "character_count": len(self.bible.list_characters()),
            "foreshadow_count": len(self.bible.load_foreshadow_map().foreshadows),
            "hotspot_count": len(self.bible.list_hotspots()),
            "updated_at": meta.updated_at.isoformat(),
        }
