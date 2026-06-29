import argparse
import json
import sys
from pathlib import Path
from src.config import Config
from src.llm.openai_client import OpenAIClient

WORKSPACE_ROOT = Path(__file__).parent.parent

def get_llm():
    config_path = Config.get_default_path()
    if not config_path.exists():
        print("错误：请先运行 `python -m src.main config init` 初始化配置，并填入API Key")
        sys.exit(1)
    config = Config.load(config_path)
    if not config.llm.api_key:
        print("错误：请在配置文件中设置API Key：", config_path)
        sys.exit(1)
    return OpenAIClient(config.llm)

def cmd_config_init(args):
    path = Config.get_default_path()
    config = Config.init_config(path)
    print(f"配置文件已创建：{path}")
    print("请编辑该文件填入你的OpenAI API Key（或兼容的API地址）。")

def cmd_distill(args):
    llm = get_llm()
    from src.workflows.distill import DistillationWorkflow
    wf = DistillationWorkflow(llm, WORKSPACE_ROOT)
    result = wf.run(Path(args.input), args.author)
    print(json.dumps(result, ensure_ascii=False, indent=2))

def cmd_novel_init(args):
    from src.bible.writer import NovelBible
    for d in ["novels", "authors", "imports"]:
        (WORKSPACE_ROOT / d).mkdir(exist_ok=True)
    bible = NovelBible.create(WORKSPACE_ROOT, args.slug, args.title, args.author)
    print(f"小说已创建：{bible.root}")
    print("请把初始设定文件放到：", WORKSPACE_ROOT / "imports" / args.slug)
    print("然后运行：python -m src.main novel import-setting --slug", args.slug, "--dir imports/"+args.slug)

def cmd_novel_import_setting(args):
    from src.bible.writer import NovelBible
    bible = NovelBible.load(WORKSPACE_ROOT, args.slug)
    src_dir = Path(args.dir)
    if not src_dir.exists():
        print(f"错误：目录不存在：{src_dir}")
        sys.exit(1)
    for fn in ["setting.md", "power_system.md", "locations.md"]:
        src = src_dir / fn
        if src.exists():
            bible.save_worldbuilding(fn, src.read_text(encoding="utf-8"))
    chars_dir = src_dir / "characters"
    if chars_dir.exists():
        for f in chars_dir.glob("*.md"):
            slug = f.stem
            content = f.read_text(encoding="utf-8")
            name = slug
            for line in content.split("\n"):
                if line.strip().startswith("# "):
                    name = line.strip()[2:].strip()
                    break
            from src.bible.models import CharacterCard, Character
            card = CharacterCard(slug=slug, name=name, basic_info=Character(name=name))
            bible.save_character(card)
    outline = src_dir / "outline.md"
    if outline.exists():
        bible.save_outline(outline.read_text(encoding="utf-8"))
    timeline = src_dir / "timeline.md"
    if timeline.exists():
        bible._p("plot", "timeline.md").write_text(timeline.read_text(encoding="utf-8"), encoding="utf-8")
    from src.bible.models import NovelStatus
    meta = bible.load_meta()
    meta.status = NovelStatus.WRITING
    bible.save_meta(meta)
    bible.git_commit("import initial settings")
    print("设定导入完成！")

def cmd_hotspot_import(args):
    llm = get_llm()
    from src.workflows.daily_update import DailyUpdateWorkflow
    wf = DailyUpdateWorkflow(llm, WORKSPACE_ROOT, args.slug)
    text = args.text or ""
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    if not text.strip():
        print("错误：请提供热点文本（--text 或 --file）")
        sys.exit(1)
    material = wf.add_hotspot(text)
    print(f"热点素材已导入：{material.id} - {material.title}")

def cmd_novel_write_next(args):
    llm = get_llm()
    from src.workflows.daily_update import DailyUpdateWorkflow
    wf = DailyUpdateWorkflow(llm, WORKSPACE_ROOT, args.slug)
    result = wf.write_next_chapter()
    if result.get("success"):
        print(f"第{result['chapter_number']}章写完！字数：{result['word_count']}，审稿结论：{result['verdict']}，重试次数：{result['retry_count']}")
        print("---预览---")
        print(result["content_preview"])
    else:
        print(f"写作失败：{result.get('error','未知错误')}")

def cmd_chat(args):
    llm = get_llm()
    from src.agents.editor_assistant import EditorAssistantAgent
    from src.bible.writer import NovelBible
    agent = EditorAssistantAgent(llm)
    bible = NovelBible.load(WORKSPACE_ROOT, args.slug) if args.slug else None
    status = ""
    if bible:
        from src.workflows.daily_update import DailyUpdateWorkflow
        wf = DailyUpdateWorkflow(llm, WORKSPACE_ROOT, args.slug)
        status = json.dumps(wf.get_status(), ensure_ascii=False, indent=2)
    print("总编助理模式（输入/quit退出）")
    while True:
        try:
            user_input = input("你> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user_input in ("/quit", "/exit", "退出"):
            break
        if not user_input:
            continue
        result = agent.run(user_input=user_input, novel_status=status)
        print(f"助理> {result.get('response_to_user', result)}")
        if result.get("clarifying_question"):
            print(f"助理> （问一下：{result['clarifying_question']}）")

def cmd_novel_status(args):
    llm = get_llm()
    from src.workflows.daily_update import DailyUpdateWorkflow
    wf = DailyUpdateWorkflow(llm, WORKSPACE_ROOT, args.slug)
    status = wf.get_status()
    print(json.dumps(status, ensure_ascii=False, indent=2))

def cmd_novel_rollback(args):
    from src.bible.writer import NovelBible
    from src.utils.git import GitManager
    bible = NovelBible.load(WORKSPACE_ROOT, args.slug)
    gm = GitManager(bible.root)
    commits = gm.get_log(50)
    target_commit = None
    target_ch = args.chapter
    for c in commits:
        if f"chapter {target_ch}" in c["message"] or f"第{target_ch}章" in c["message"]:
            target_commit = c["hash"]
            break
    if target_commit:
        gm.reset_to_commit(target_commit)
        print(f"已回滚到第{target_ch}章（commit {target_commit[:8]}）")
    else:
        print(f"未找到第{target_ch}章的提交记录")

def main():
    parser = argparse.ArgumentParser(description="个人创作助手 - 小说创作系统")
    sub = parser.add_subparsers(dest="command", required=True)
    p_config = sub.add_parser("config", help="配置管理")
    p_config_sub = p_config.add_subparsers(dest="config_cmd", required=True)
    p_config_init = p_config_sub.add_parser("init", help="初始化配置文件")
    p_config_init.set_defaults(func=cmd_config_init)
    p_distill = sub.add_parser("distill", help="蒸馏作者风格")
    p_distill.add_argument("--input", required=True, help="小说txt文件路径")
    p_distill.add_argument("--author", required=True, help="作者标识slug")
    p_distill.set_defaults(func=cmd_distill)
    p_novel = sub.add_parser("novel", help="小说管理")
    p_novel_sub = p_novel.add_subparsers(dest="novel_cmd", required=True)
    p_novel_init = p_novel_sub.add_parser("init", help="创建新小说")
    p_novel_init.add_argument("--slug", required=True)
    p_novel_init.add_argument("--title", required=True)
    p_novel_init.add_argument("--author", default=None)
    p_novel_init.set_defaults(func=cmd_novel_init)
    p_novel_import = p_novel_sub.add_parser("import-setting", help="导入初始设定")
    p_novel_import.add_argument("--slug", required=True)
    p_novel_import.add_argument("--dir", required=True)
    p_novel_import.set_defaults(func=cmd_novel_import_setting)
    p_novel_write = p_novel_sub.add_parser("write-next", help="写下一章")
    p_novel_write.add_argument("--slug", required=True)
    p_novel_write.set_defaults(func=cmd_novel_write_next)
    p_novel_status = p_novel_sub.add_parser("status", help="查看小说状态")
    p_novel_status.add_argument("--slug", required=True)
    p_novel_status.set_defaults(func=cmd_novel_status)
    p_novel_rollback = p_novel_sub.add_parser("rollback", help="回滚到指定章节")
    p_novel_rollback.add_argument("--slug", required=True)
    p_novel_rollback.add_argument("--chapter", type=int, required=True)
    p_novel_rollback.set_defaults(func=cmd_novel_rollback)
    p_hotspot = sub.add_parser("hotspot", help="热点素材管理")
    p_hotspot_sub = p_hotspot.add_subparsers(dest="hotspot_cmd", required=True)
    p_hotspot_import = p_hotspot_sub.add_parser("import", help="导入热点")
    p_hotspot_import.add_argument("--slug", required=True)
    p_hotspot_import.add_argument("--text", default=None)
    p_hotspot_import.add_argument("--file", default=None)
    p_hotspot_import.set_defaults(func=cmd_hotspot_import)
    p_chat = sub.add_parser("chat", help="和总编助理对话")
    p_chat.add_argument("--slug", default=None)
    p_chat.set_defaults(func=cmd_chat)
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
