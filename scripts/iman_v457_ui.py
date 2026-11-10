"""Non-destructive v0.45.7 UI adjustments on the *generated* native Compose app.

Called AFTER the fully validated v0.45.6 builder. Only runtime styling files
are touched. Source book, quizzes, quote data, five-tab routing and user prefs
are explicitly outside this transform.
"""
from pathlib import Path
import re
from scripts.iman_v44_transform import matching, split_args

ABOUT_INTRO = 'Text("Здесь сохранён полный текст издания с исходным порядком глав и дополнительной тематической навигацией.")'
ABOUT_HADITH = 'Text("Источники хадисов показываются только там, где они указаны в тексте книги. Степень достоверности здесь автоматически не присваивается.")'


def remove_medical_notice(source: str) -> str:
    """Remove complete obsolete note container, not just its visible caption."""
    if source.count(ABOUT_INTRO) != 1 or source.count(ABOUT_HADITH) != 1:
        raise RuntimeError("About page headings changed; refuse a blind text edit")
    begin = source.index(ABOUT_INTRO) + len(ABOUT_INTRO)
    end = source.index(ABOUT_HADITH, begin)
    notice = source[begin:end]
    if 'Важное примечание' not in notice or 'Card(' not in notice:
        raise RuntimeError("Unrelated medical note not identified precisely")
    if notice.count('{') != notice.count('}'):
        raise RuntimeError("Medical notice includes unmatched Kotlin code")
    return source[:begin] + "\n            " + source[end:]


def flatten_controls(source: str) -> str:
    """Keep onClick/enabled/semantics and remove decorative outlined surfaces."""
    source = re.sub(r'(?<![\w.])(OutlinedButton|FilledTonalButton|Button)\s*\(',
                    'TextButton(', source)
    # Chips are not buttons: retain their label/click function and suppress
    # borders through their supported Material3 border argument.
    for match in reversed(list(re.finditer(
            r'(?<![\w.])(SuggestionChip|AssistChip|FilterChip|InputChip)\s*\(', source))):
        start = source.index('(', match.start())
        end = matching(source, start)
        args = split_args(source[start + 1:end])
        if not any(arg.startswith('border =') for arg in args):
            args.append('border = null')
        else:
            args = ['border = null' if a.startswith('border =') else a for a in args]
        source = source[:start + 1] + ', '.join(args) + source[end:]
    return source


PURPLE_COLOR = re.compile(r'Color\(0xFF([0-9a-fA-F]{6})\)')


def warm_purple_literals(source: str) -> str:
    """Replace accidental hard-coded lavender/purple accents, not book images."""
    def replace(match):
        rgb = match.group(1)
        r, g, b = int(rgb[:2], 16), int(rgb[2:4], 16), int(rgb[4:], 16)
        purple = b >= r + 5 and b >= g + 9 and r >= g - 8
        if not purple:
            return match.group(0)
        return 'Color(0xFFE0CEB5)' if (r + g + b) / 3 >= 175 else 'Color(0xFF87694D)'
    return PURPLE_COLOR.sub(replace, source)


def patch_ui(java: Path) -> dict:
    affected = {}
    for name in (
        'Screens.kt', 'Reader.kt', 'FaithStudy.kt',
        'IbnV38StudyEngine.kt', 'WebDesign.kt',
        'IbnQayyimStyle.kt', 'ReadingStatisticsV36.kt',
        'ImanV38More.kt',
    ):
        path = java / name
        before = path.read_text('utf-8')
        after = remove_medical_notice(before) if name == 'Screens.kt' else before
        if name in ('Reader.kt', 'FaithStudy.kt', 'IbnV38StudyEngine.kt',
                    'Screens.kt', 'WebDesign.kt', 'IbnQayyimStyle.kt'):
            after = flatten_controls(after)
        after = warm_purple_literals(after)
        if after != before:
            path.write_text(after, 'utf-8')
            affected[name] = (len(before), len(after))
    if 'Screens.kt' not in affected or 'Reader.kt' not in affected:
        raise RuntimeError('v457 failed to edit actual About/Reader Compose screens')
    return affected
