"""Generated editorial labels shared by Datenfutter and Datafodder."""
from datetime import date


_LABELS = {
    'de': {
        'publication': 'datenfutter',
        'sources': 'Quellen',
        'methods': 'Methoden',
        'retrieved': 'Abruf',
        'as_of': 'Stand',
        'slide': 'Folie',
        'source_note': 'Quellen und Methodik: vollständige URLs in der Caption.',
    },
    'en': {
        'publication': 'datafodder',
        'sources': 'Sources',
        'methods': 'Methods',
        'retrieved': 'Retrieved',
        'as_of': 'As of',
        'slide': 'Slide',
        'source_note': 'Sources and methods: full URLs in the caption.',
    },
}
_ENGLISH_MONTHS = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')


def labels(language: str) -> dict:
    """Reject unsupported languages instead of silently selecting a fallback."""
    if not isinstance(language, str) or language not in _LABELS:
        raise ValueError('Unsupported language; supply language=de or language=en.')
    return _LABELS[language]


def display_date(value: date, language: str) -> str:
    """Format editorial/retrieval dates independently of the process locale."""
    labels(language)
    if language == 'de':
        return value.strftime('%d.%m.%Y')
    return f'{value.day:02d} {_ENGLISH_MONTHS[value.month - 1]} {value.year:04d}'
