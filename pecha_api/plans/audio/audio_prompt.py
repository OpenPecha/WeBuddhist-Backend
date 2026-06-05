from pecha_api.plans.plans_enums import PlanAudioType

DEFAULT_VOICE_NAME = "Algenib"
DEFAULT_ACCENT = "Neutral"

RECITATION_SCENE = """## Scene:
"""

RECITATION_SAMPLE_CONTEXT = """## Sample Context:
"""

INSTRUCTION_SCENE = """## Scene:
 The Corporate Studio.
"""

INSTRUCTION_SAMPLE_CONTEXT = """## Sample Context:
InstructionAal E-learning. Measured pacAing with clear pauses for clarity. Tone is authoritative, accessible, and articulate.
."""

TEXT_READING_SCENE = """## Scene:
It is dawn inside a vast, silent meditation hall nestled deep within a quiet forest monastery. A senior monk sits perfectly upright, speaking to a small circle of practitioners. The room possesses a subtle, warm, and spacious acoustic resonance. The atmosphere demands an organic, deeply grounded, and entirely unhurried delivery, where every word is heavy with presence.
"""

TEXT_READING_SAMPLE_CONTEXT = """## Sample Context:
This voice profile is the definitive standard for serene scriptural readings, timeless philosophical translations, and monastic audiobooks where the listener requires immense breathing room to contemplate profound truths
"""

AUDIO_TYPE_CONFIGS = {
    PlanAudioType.RECITATION: {
        "style": "Warm, understanding, soft tone with gentle inflections.",
        "pace": "Natural conversational pace.",
        "scene": RECITATION_SCENE,
        "sample_context": RECITATION_SAMPLE_CONTEXT,
    },
    PlanAudioType.INSTRUCTION: {
        "style": "Authoritative, accessible, and articulate",
        "pace": "Natural conversational pace with clear pauses for clarity",
        "scene": INSTRUCTION_SCENE,
        "sample_context": INSTRUCTION_SAMPLE_CONTEXT,
    },
    PlanAudioType.TEXT_READING: {
        "style": "Warm, understanding, soft tone with gentle inflections. Pace: Natural conversational pace.",
        "pace": "Natural comfortable reading pace",
        "scene": TEXT_READING_SCENE,
        "sample_context": TEXT_READING_SAMPLE_CONTEXT,
    },
}


def build_tts_prompt(
    transcript: str,
    audio_type: PlanAudioType,
) -> str:
    type_config = AUDIO_TYPE_CONFIGS[audio_type]

    director_note = (
        f"# Director's note\n"
        f"Style: {type_config['style']}. "
        f"Pace: {type_config['pace']}. "
        f"Accent: {DEFAULT_ACCENT}."
    )

    parts = [
        "Read the following transcript based on the director's note.",
        "",
        director_note,
        "",
        type_config["scene"],
        "",
        type_config["sample_context"],
        "",
        f"## Transcript:\n{transcript}",
    ]

    return "\n".join(parts)
