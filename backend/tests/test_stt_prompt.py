"""The transcriber prompt keeps English words English and spells the scene's words right."""

from app.services.prompts import stt_prompt


def test_prompt_mixes_languages_and_lists_the_scene_words() -> None:
    p = stt_prompt(["café", "l'addition"], ["par carte"])
    assert "coffee" in p and "How do you say" in p  # code-switch cues
    assert p.endswith("café, l'addition, par carte.")


def test_prompt_without_words_is_just_the_style() -> None:
    assert stt_prompt() == stt_prompt([], [])
    assert stt_prompt().endswith("par carte.")
