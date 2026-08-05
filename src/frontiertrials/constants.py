"""Stable vocabulary and policy constants."""

FORMAT_VERSION = "1"
APP_VERSION = "0.3.1"

KINDS = ("task", "candidate", "response", "rubric", "pairing", "ballot", "rater")
DIRECTORIES = {kind: f"{kind}s" for kind in KINDS}

TASK_CATEGORIES = (
    "analysis",
    "coding",
    "engineering",
    "research",
    "writing",
    "reasoning",
    "multilingual",
    "other",
)
RESPONSE_STATES = ("captured", "excluded")
PAIRING_STATES = ("ready", "retired")
BALLOT_CHOICES = ("left", "right", "tie", "abstain")
RATING_SCALE = (1, 2, 3, 4, 5)
CAPTURE_SURFACES = (
    "web",
    "desktop",
    "mobile",
    "cli-subscription",
    "manual",
    "other",
)
LEAKAGE_TERMS = (
    "chatgpt",
    "openai",
    "claude",
    "anthropic",
    "gemini",
    "google ai",
    "deepseek",
    "qwen",
    "tongyi",
    "kimi",
    "moonshot",
    "glm",
    "zhipu",
    "grok",
    "mistral",
    "llama",
)
ALIAS_WORDS = (
    "Aster",
    "Birch",
    "Cedar",
    "Dahlia",
    "Elm",
    "Flint",
    "Grove",
    "Hazel",
    "Iris",
    "Juniper",
    "Kestrel",
    "Linden",
    "Maple",
    "Nectar",
    "Orchid",
    "Pine",
)
