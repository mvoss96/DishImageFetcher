import re
import unicodedata

def normalize(keyword: str) -> str:
    """
    Removes unnecessary whitespaces, punctuation, replaces umlauts and accented characters generically,
    and removes all characters that would not appear in a dish name (only lowercase a-z and spaces).
    """
    # Convert to lower case
    keyword = keyword.lower()
    # Replace Special Chars
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss'
    }
    for orig, repl in replacements.items():
        keyword = keyword.replace(orig, repl)

    # Unicode normalization (decompose accents)
    keyword = unicodedata.normalize('NFKD', keyword)
    # Remove accents (diacritics)
    keyword = ''.join(c for c in keyword if unicodedata.category(c) != 'Mn')
    # Allow only Unicode letters and spaces
    keyword = ''.join(c for c in keyword if c.isalpha() or c.isspace())
    # Reduce multiple whitespaces to a single space
    keyword = re.sub(r'\s+', ' ', keyword).strip()
    return keyword


if __name__ == "__main__":
    normalized = normalize("寿司")
    print(normalized)
