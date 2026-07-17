import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    max_rounds: int = 5
    confidence_threshold: float = 0.7
    demo_mode: bool = True
    use_openai: bool = False          # experimental; stub engine is the default
    openai_model: str = "gpt-5.6"


def settings_from_env() -> Settings:
    demo_mode = os.getenv("OPSCONTROL_DEMO_MODE", "1") != "0"
    return Settings(
        max_rounds=int(os.getenv("OPSCONTROL_MAX_ROUNDS", "5")),
        confidence_threshold=float(os.getenv("OPSCONTROL_CONFIDENCE_THRESHOLD", "0.7")),
        demo_mode=demo_mode,
        use_openai=not demo_mode
        and os.getenv("OPSCONTROL_USE_OPENAI", "0") == "1"
        and bool(os.getenv("OPENAI_API_KEY")),
        openai_model=os.getenv("OPSCONTROL_MODEL", "gpt-5.6"),
    )
