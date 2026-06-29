import json
import shutil
from pathlib import Path
from typing import Any, Dict
from src.llm.base import BaseLLMClient
from src.utils.text_clean import load_and_clean
from src.agents.distillation.preprocessor import PreprocessorAgent
from src.agents.distillation.statistician import StatisticianAgent
from src.agents.distillation.literature_analyst import LiteratureAnalystAgent
from src.agents.distillation.antipattern_detector import AntipatternDetectorAgent
from src.agents.distillation.validator import DistillationValidatorAgent

SAMPLE_SIZE = 30000

class DistillationWorkflow:
    def __init__(self, llm_client: BaseLLMClient, workspace_root: Path):
        self.llm = llm_client
        self.workspace = Path(workspace_root)
        self.preprocessor = PreprocessorAgent(llm_client)
        self.statistician = StatisticianAgent(llm_client)
        self.literary = LiteratureAnalystAgent(llm_client)
        self.antipattern = AntipatternDetectorAgent(llm_client)
        self.validator = DistillationValidatorAgent(llm_client)

    def _get_sample(self, cleaned_text: str) -> str:
        total = len(cleaned_text)
        if total <= SAMPLE_SIZE * 3:
            return cleaned_text
        parts = []
        parts.append(cleaned_text[:SAMPLE_SIZE])
        mid_start = total // 2 - SAMPLE_SIZE // 2
        parts.append(cleaned_text[mid_start:mid_start + SAMPLE_SIZE])
        parts.append(cleaned_text[-SAMPLE_SIZE:])
        return "\n\n---样本分隔---\n\n".join(parts)

    def _save_layers(self, output_dir: Path, result: Dict[str, Any]):
        output_dir.mkdir(parents=True, exist_ok=True)
        layer0 = result.get("layer0_redlines", [])
        layer1 = result.get("layer1_meta", {})
        layer3 = result.get("layer3_characters", {})
        layer4 = result.get("layer4_structure", {})
        anti = result.get("antipatterns", {})
        stats = result.get("statistics", {})
        def md_list(items):
            return "\n".join(f"- {item}" for item in items) if items else "（待补充）"
        def md_dict(d, indent=0):
            lines = []
            for k, v in d.items():
                if isinstance(v, list):
                    lines.append(f"{'  '*indent}- **{k}**：")
                    for item in v:
                        lines.append(f"{'  '*(indent+1)}- {item}")
                elif isinstance(v, dict):
                    lines.append(f"{'  '*indent}- **{k}**：")
                    lines.append(md_dict(v, indent+1))
                else:
                    lines.append(f"{'  '*indent}- **{k}**：{v}")
            return "\n".join(lines)
        (output_dir / "layer0_redlines.md").write_text(f"# 绝对红线（Layer 0）\n\n{md_list(layer0)}\n", encoding="utf-8")
        l1_content = f"# 写作元规则（Layer 1）\n\n{md_dict(layer1)}\n"
        if stats.get("sentence_length_distribution"):
            l1_content += f"\n## 句式长度分布\n\n{md_dict(stats['sentence_length_distribution'])}\n"
        if stats.get("dialogue_ratio") is not None:
            l1_content += f"\n- 对话占比：{stats['dialogue_ratio']}\n"
        (output_dir / "layer1_meta.md").write_text(l1_content, encoding="utf-8")
        l2 = f"# 文笔DNA（Layer 2）\n\n"
        if stats.get("common_words"):
            l2 += f"## 常用词\n\n{md_list(stats['common_words'])}\n\n"
        if stats.get("common_bad_words"):
            l2 += f"## 作者常用口语/口头禅\n\n{md_list(stats['common_bad_words'])}\n\n"
        if anti.get("ai_overused_phrases_in_this_style"):
            l2 += f"## 禁用词清单（AI常用但作者不会用）\n\n{md_list(anti['ai_overused_phrases_in_this_style'])}\n\n"
        if stats.get("paragraph_style"):
            l2 += f"## 段落风格\n\n{md_dict(stats['paragraph_style'])}\n\n"
        if stats.get("punctuation_habits"):
            l2 += f"## 标点习惯\n\n- {stats['punctuation_habits']}\n\n"
        if stats.get("description_ratios"):
            l2 += f"## 描写比例\n\n{md_dict(stats['description_ratios'])}\n"
        (output_dir / "layer2_prose_dna.md").write_text(l2, encoding="utf-8")
        (output_dir / "layer3_characters.md").write_text(f"# 人物塑造规则（Layer 3）\n\n{md_dict(layer3)}\n", encoding="utf-8")
        (output_dir / "layer4_structure.md").write_text(f"# 故事结构规则（Layer 4）\n\n{md_dict(layer4)}\n", encoding="utf-8")
        l5 = f"# 反模式库（Layer 5）\n\n"
        if anti.get("bad_cliches"):
            l5 += f"## 烂俗桥段禁用\n\n{md_list(anti['bad_cliches'])}\n\n"
        if anti.get("things_author_never_does"):
            l5 += f"## 作者绝对不会做的事\n\n{md_list(anti['things_author_never_does'])}\n\n"
        if anti.get("writing_anti_patterns"):
            l5 += f"## AI模仿时需要避免的写法\n\n{md_list(anti['writing_anti_patterns'])}\n"
        (output_dir / "layer5_antipatterns.md").write_text(l5, encoding="utf-8")
        (output_dir / "corrections.json").write_text("[]", encoding="utf-8")

    def run(self, input_file: Path, author_slug: str, output_dir: Path = None) -> Dict[str, Any]:
        input_file = Path(input_file)
        if output_dir is None:
            output_dir = self.workspace / "authors" / author_slug
        print(f"[1/6] 加载并清洗文本：{input_file.name}")
        data = load_and_clean(input_file)
        cleaned = data["cleaned_text"]
        print(f"  总字符数：{data['total_chars']}，章节数：{data['total_chapters']}")
        sample = self._get_sample(cleaned)
        print(f"[2/6] 文本质量检查...")
        prep = self.preprocessor.run(
            sample_text=sample[:5000],
            total_chars=data["total_chars"],
            chapter_count=data["total_chapters"],
        )
        print(f"  预估字数：{prep.get('total_words_estimate', '?')}，类型：{prep.get('genre_hint', '?')}")
        print(f"[3/6] 量化统计...")
        stats = self.statistician.run(sample_text=sample)
        print(f"  短句占比：{stats.get('sentence_length_distribution',{}).get('short_percent','?')}%，对话占比：{stats.get('dialogue_ratio','?')}")
        print(f"[4/6] 文学分析...")
        literary_result = self.literary.run(sample_text=sample, statistics_json=json.dumps(stats, ensure_ascii=False, indent=2))
        print(f"[5/6] 反模式检测...")
        anti = self.antipattern.run(sample_text=sample)
        all_result = {**literary_result, "antipatterns": anti, "statistics": stats}
        print(f"[6/6] 迭代校验（最多3轮）...")
        iterations = 0
        passed = False
        validation_log = []
        for i in range(3):
            iterations = i + 1
            original_samples = []
            for sec in [cleaned[:SAMPLE_SIZE], cleaned[len(cleaned)//2:len(cleaned)//2+2000], cleaned[-2000:]]:
                paras = [p for p in sec.split("\n\n") if len(p.strip()) > 200]
                if paras:
                    original_samples.append(paras[0][:1000])
                if len(original_samples) >= 3:
                    break
            while len(original_samples) < 3:
                original_samples.append("（样本不足）")
            generated_samples = []
            test_prompts = [
                "请写一段1000字左右的对话场景，两个人物在对话中产生冲突。",
                "请写一段1000字左右的动作/冲突场景。",
                "请写一段1000字左右的人物内心独白/环境描写场景。",
            ]
            from src.agents.writing.writer import WriterAgent
            writer = WriterAgent(self.llm)
            style_rules_md = "\n\n".join([
                f"## {k}\n{v}" for k, v in {
                    "Layer0": md_list_or_str(all_result.get("layer0_redlines", [])),
                    "Layer1": json.dumps(all_result.get("layer1_meta", {}), ensure_ascii=False),
                    "Layer2": "（文笔规则略，按网络小说流畅自然风格写）",
                    "Layer3": json.dumps(all_result.get("layer3_characters", {}), ensure_ascii=False),
                    "Layer5": md_list_or_str(anti.get("ai_overused_phrases_in_this_style", [])),
                }.items()
            ])
            for tp in test_prompts:
                fake_outline = json.dumps({"chapter_title":"试写","core_event":"试写","scenes":[{"scene_desc":tp,"characters_involved":[],"purpose":"test","emotion_note":"自然"}],"emotion_curve":"自然","chapter_ending_hook":"","time_advance":"","word_count_target":1000}, ensure_ascii=False)
                result = writer.run(
                    user_message=tp,
                    style_rules=style_rules_md,
                    outline=fake_outline,
                    characters="人物：甲乙两人",
                    prev_chapter_ending="",
                    materials="",
                    foreshadows="",
                )
                generated_samples.append(result.get("content", "")[:1000] if not result.get("blocked") else "（生成被阻塞）")
            validation = self.validator.run(
                original_samples="\n\n---片段分隔---\n\n".join(original_samples),
                generated_samples="\n\n---片段分隔---\n\n".join(generated_samples),
            )
            validation_log.append(validation)
            if validation.get("pass_validation"):
                passed = True
                print(f"  第{i+1}轮：通过校验（置信度{validation.get('confidence',0):.2f}）")
                break
            else:
                print(f"  第{i+1}轮：未通过，修正规则中...")
                for fix in validation.get("suggested_fixes", []):
                    layer = fix.get("layer", "")
        self._save_layers(output_dir, all_result)
        report = f"# 蒸馏报告\n\n- 作者：{author_slug}\n- 源文件：{input_file.name}\n- 迭代轮数：{iterations}\n- 最终是否通过：{'是' if passed else '否（需要人工调整）'}\n\n"
        report += "## 校验记录\n\n"
        for i, v in enumerate(validation_log):
            report += f"### 第{i+1}轮\n- 置信度：{v.get('confidence',0):.2f}\n- 发现差异：{len(v.get('distinctions',[]))}处\n"
            for d in v.get("distinctions", []):
                report += f"  - {d.get('segment','')}: {d.get('reason','')}\n"
            report += "\n"
        (output_dir / "distillation_report.md").write_text(report, encoding="utf-8")
        print(f"蒸馏完成！规则已保存到：{output_dir}")
        return {
            "author_slug": author_slug,
            "output_dir": str(output_dir),
            "iterations": iterations,
            "passed": passed,
        }

def md_list_or_str(items):
    if isinstance(items, list):
        return "\n".join(f"- {x}" for x in items)
    return str(items)
