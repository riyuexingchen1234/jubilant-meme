import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class NovelStatus(str, Enum):
    PLANNING = "planning"
    WRITING = "writing"
    PAUSED = "paused"

class ForeshadowType(str, Enum):
    LIGHT = "light"
    HEAVY = "heavy"

class ForeshadowStatus(str, Enum):
    PLANTED = "planted"
    REVEALED = "revealed"
    ABANDONED = "abandoned"

class MaterialStatus(str, Enum):
    UNUSED = "unused"
    USED = "used"
    PLANTED_SEED = "planted_seed"

class ChapterWritingConfig(BaseModel):
    chapter_word_count_target: List[int] = Field(default_factory=lambda: [3000, 5000])
    hotspot_integration_ratio: float = 0.3
    auto_write_enabled: bool = False

class NovelMeta(BaseModel):
    novel_slug: str
    title: str
    author_style_source: List[str] = Field(default_factory=list)
    status: NovelStatus = NovelStatus.PLANNING
    current_chapter: int = 0
    novel_current_time: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    config: ChapterWritingConfig = Field(default_factory=ChapterWritingConfig)
    version: int = 1

class Character(BaseModel):
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    first_appearance_chapter: int = 0
    role: str = "supporting"

class KeyEvent(BaseModel):
    chapter: int
    event: str
    impact: str = ""

class CharacterCard(BaseModel):
    slug: str
    name: str
    basic_info: Character = Field(default_factory=lambda: Character(name=""))
    personality_traits: List[Dict[str, str]] = Field(default_factory=list)
    speech_patterns: Dict[str, Any] = Field(default_factory=dict)
    relationships: List[Dict[str, str]] = Field(default_factory=list)
    arc: Dict[str, Any] = Field(default_factory=dict)
    ooc_redlines: List[str] = Field(default_factory=list)
    key_events: List[KeyEvent] = Field(default_factory=list)

class Foreshadow(BaseModel):
    id: str
    content: str
    type: ForeshadowType = ForeshadowType.LIGHT
    planted_chapter: int
    planned_reveal_chapter: Optional[int] = None
    status: ForeshadowStatus = ForeshadowStatus.PLANTED
    related_material_id: Optional[str] = None
    notes: str = ""

class ForeshadowMap(BaseModel):
    foreshadows: List[Foreshadow] = Field(default_factory=list)
    def add(self, fs: Foreshadow):
        self.foreshadows.append(fs)
    def get_planted(self) -> List[Foreshadow]:
        return [f for f in self.foreshadows if f.status == ForeshadowStatus.PLANTED]
    def mark_revealed(self, fs_id: str, chapter: int):
        for f in self.foreshadows:
            if f.id == fs_id:
                f.status = ForeshadowStatus.REVEALED
                f.planned_reveal_chapter = chapter
                return
    def to_json(self) -> List[Dict[str, Any]]:
        return [f.model_dump() for f in self.foreshadows]
    @classmethod
    def from_json(cls, data: List[Dict[str, Any]]) -> "ForeshadowMap":
        return cls(foreshadows=[Foreshadow(**d) for d in data])

class HotspotMaterial(BaseModel):
    id: str
    title: str
    source: str = ""
    collected_at: datetime = Field(default_factory=datetime.now)
    category: str = "社会"
    emotion_tags: List[str] = Field(default_factory=list)
    core_fact: str = ""
    core_conflict: str = ""
    fictionable_points: List[str] = Field(default_factory=list)
    predicted_trends: List[str] = Field(default_factory=list)
    fictionable_score: int = 5
    related_characters: List[str] = Field(default_factory=list)
    status: MaterialStatus = MaterialStatus.UNUSED
    used_in_chapter: Optional[int] = None

class ChapterMeta(BaseModel):
    number: int
    title: str = ""
    word_count: int = 0
    summary: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    used_materials: List[str] = Field(default_factory=list)
    planted_foreshadows: List[str] = Field(default_factory=list)
    revealed_foreshadows: List[str] = Field(default_factory=list)

class Correction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = Field(default_factory=datetime.now)
    scene: str
    wrong: str
    correct: str
    applied_scope: str = "global"
