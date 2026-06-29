from pathlib import Path
from typing import Any, Dict, List, Optional
from git import Repo

class GitManager:
    def __init__(self, repo_path: Path, author_name: str = "Novel Assistant", author_email: str = "assistant@local"):
        self.repo_path = Path(repo_path)
        self.author_name = author_name
        self.author_email = author_email

    def is_repo(self) -> bool:
        try:
            Repo(str(self.repo_path))
            return True
        except Exception:
            return False

    def init(self):
        if not self.is_repo():
            self.repo = Repo.init(str(self.repo_path))
            with self.repo.config_writer() as c:
                c.set_value("user", "name", self.author_name)
                c.set_value("user", "email", self.author_email)
        else:
            self.repo = Repo(str(self.repo_path))

    def _ensure(self):
        if not hasattr(self, "repo"):
            self.init()

    def commit_all(self, message: str) -> Optional[str]:
        self._ensure()
        self.repo.git.add(A=True)
        if not self.repo.is_dirty(untracked_files=True):
            return None
        commit = self.repo.index.commit(message)
        return str(commit.hexsha)

    def get_log(self, limit: int = 10) -> List[Dict[str, Any]]:
        self._ensure()
        result = []
        for c in self.repo.iter_commits(max_count=limit):
            result.append({
                "hash": str(c.hexsha), "message": c.message.strip(),
                "author": str(c.author), "timestamp": c.committed_datetime.isoformat(),
            })
        return result

    def reset_to_commit(self, commit_hash: str, hard: bool = True):
        self._ensure()
        if hard:
            self.repo.git.reset("--hard", commit_hash)
        else:
            self.repo.git.reset("--mixed", commit_hash)

    def get_current_hash(self) -> str:
        self._ensure()
        return str(self.repo.head.commit.hexsha)
