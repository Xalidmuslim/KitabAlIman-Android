"""Remove medicine-only links and images from the Kitab al-Iman navigation.

Keep the native Compose route stack, storage, settings and search intact.
"""
def _one(s, old, new, label):
    if s.count(old) != 1:
        raise RuntimeError("Pinned source changed: " + label)
    return s.replace(old, new, 1)


def patch_more(source):
    at = source.index("fun WebMoreScreen(")
    begin = source.index("    val rows = listOf(", at)
    end = source.index("\n\n    Column(", begin)
    rows = '''    val rows = listOf(
        MoreItem("▤", "Оглавление", "131 раздел книги", Route.Book),
        MoreItem("▦", "Подборки по вере", "Тематическое изучение", Route.Collections),
        MoreItem("Aa", "Словарь понятий", "Разъяснение терминов", Route.Glossary),
        MoreItem("≡", "Хадисы и источники", "Цитаты из книги", Route.Hadiths),
        MoreItem("✎", "Мои заметки", "Выделения и записи", Route.Notes),
        MoreItem("◷", "История чтения", "Недавно открытые главы", Route.History),
        MoreItem("⚙", "Настройки чтения", "Шрифт и оформление", Route.Settings),
        MoreItem("i", "О книге", "Об авторе и издании", Route.About),
        MoreItem("§", "Об издании", "Состав книги и источники", Route.Source),
    )'''
    return source[:begin] + rows + source[end:]


def patch_home(source):
    begin = '            item(key = "treatments") {'
    end = '            item(key = "quick-books") {'
    if source.count(begin) != 1 or source.count(end) != 1:
        raise RuntimeError("Medicine promotional card moved")
    i = source.index(begin)
    j = source.index(end, i)
    source = source[:i] + source[j:]
    source = _one(source,
        'AntiqueQuickCard(R.drawable.antique_books_detail, "Читать книгу",',
        'AntiqueQuickCard(R.drawable.antique_books_detail, "Оглавление",', "home contents card")
    source = _one(source,
        'AntiqueQuickCard(R.drawable.antique_scroll_detail, "Темы",',
        'AntiqueQuickCard(R.drawable.antique_scroll_detail, "Подборки",', "home topical card")
    source = _one(source,
        'Modifier.weight(1f)) { navigate(Route.Topics) }',
        'Modifier.weight(1f)) { navigate(Route.Collections) }',
        "home topical route")
    source = _one(source,
        'AntiqueQuickCard(R.drawable.antique_scroll_detail, "Указатель понятий",',
        'AntiqueQuickCard(R.drawable.antique_scroll_detail, "Понятия",',
        "remove medical catalogue image")
    source = _one(source,
        'Modifier.weight(1f)) { navigate(Route.Remedies) }',
        'Modifier.weight(1f)) { navigate(Route.Glossary) }',
        "home glossary route")
    if 'Route.Treatments' in source or 'antique_mortar_detail' in source or 'antique_remedies_detail' in source:
        raise RuntimeError("Medicine-only home control survived")
    return source


def patch_legacy_screens(source):
    # Legacy screens are not used by the main nav, but they must not display
    # the medicine product's words when reached from a stale route.
    swaps = (
        ('Icon(Icons.Default.MedicalServices, null,', 'Icon(Icons.Default.MenuBook, null,'),
        ('navigate(Route.Treatments)', 'navigate(Route.Book)'),
        ('navigate(Route.Remedies)', 'navigate(Route.Glossary)'),
        ('"Как лечили / что применялось"', '"Оглавление"'),
        ('"Состояние → понятия → полный текст"', '"Разделы книги"'),
        ('"Справочник средств"', '"Словарь понятий"'),
        ('"111 глав в оригинальном порядке"', '"131 глава в порядке книги"'),
        ('"Головная боль, сон, тревога, рукъя и другое"', '"Тематические подборки по вере"'),
        ('"Рукъя, кыст, тальбина и другое"', '"Понятия по вопросам веры"'),
        ('"Главы, темы, понятия, поиск и справочники собраны из одного полного текста книги."',
         '"Оглавление, поиск и справочники основаны на тексте книги."'),
        ('"Историко-религиозный справочник, а не персональная медицинская инструкция."',
         '"Тематический указатель по содержанию книги."'),
        ('"Как лечили"', '"Вопросы веры"'),
        ('"Состояние или понятие"', '"Тема или понятие"'),
        ('"Средств"', '"Сносок"'),
        ('"Средство"', '"Понятие"'),
        ('"Средства"', '"Понятия"'),
        ('Icons.Default.Medication', 'Icons.Default.MenuBook'),
    )
    for old, new in swaps:
        source = source.replace(old, new)
    source = source.replace(
        'MetricCard("Сносок", (if (book.stats.remedies > 0) book.stats.remedies else book.remedies.size).toString(),',
        'MetricCard("Сносок", book.chapters.sumOf { ch -> ch.blocks.count { it.type == "footnote" } }.toString(),')
    # The unused old More screen is rewritten, so there is no secondary
    # route back into treatment categories.
    at = source.index('fun MoreScreen(')
    start = source.index('    val rows = listOf(', at)
    end = source.index('\n    Column(', start)
    rows = '''    val rows = listOf(
        Triple("Оглавление", "131 глава", Route.Book),
        Triple("Подборки по вере", "Тематическое изучение", Route.Collections),
        Triple("Словарь понятий", "Указатель терминов", Route.Glossary),
        Triple("Хадисы и источники", "Цитаты из книги", Route.Hadiths),
        Triple("Мои заметки", "Выделения и записи", Route.Notes),
        Triple("История чтения", "Недавно открытые главы", Route.History),
        Triple("Настройки чтения", "Шрифт и оформление", Route.Settings),
        Triple("О книге", "Об авторе", Route.About),
    )
'''
    return source[:start] + rows + source[end:]


def patch_app(source):
    return _one(source,
        'NavItem("Темы", R.drawable.nav_topics, current == Route.Topics || current == Route.Book, onTopics),',
        'NavItem("Оглавление", R.drawable.nav_topics, current == Route.Topics || current == Route.Book, onTopics),',
        "main bottom navigation")


def patch_filter(source):
    return _one(source, 'REMEDIES("Средства")', 'REMEDIES("Понятия")', "search category")


def patch_search(source):
    return _one(source,
        'SearchFilter.AUTHOR -> block.type == "text" || block.type == "historical_note"',
        'SearchFilter.AUTHOR -> block.type == "text" || block.type == "historical_note" || block.type == "scholar" || block.type == "verse" || block.type == "verse_context"',
        "search author")
