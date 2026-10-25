import unicodedata


def normalize_text_with_mapping(text: str) -> tuple[str, list[int]]:
    """Return casefolded, accent-free text and original character indexes."""
    normalized_chars: list[str] = []
    original_indexes: list[int] = []
    for index, character in enumerate(text):
        for normalized_character in unicodedata.normalize("NFKD", character).casefold():
            if not unicodedata.combining(normalized_character):
                normalized_chars.append(normalized_character)
                original_indexes.append(index)
    return "".join(normalized_chars), original_indexes


def normalize_text(text: str) -> str:
    return normalize_text_with_mapping(text)[0]
