import re
from typing import List

STOPWORDS = {
    "a", "an", "the", "of", "on", "in", "and", "with", "for", "to", "at",
    "is", "are", "this", "that", "it", "by", "from",
}


def caption_to_hashtags(caption: str, num_tags: int = 5, language: str = "vi") -> List[str]:
    words = re.findall(r"[A-Za-z0-9]+", caption.lower())
    filtered = [w for w in words if len(w) > 2 and w not in STOPWORDS]

    seen = set()
    unique_words = []
    for w in filtered:
        if w not in seen:
            seen.add(w)
            unique_words.append(w)

    tags = [f"#{w}" for w in unique_words]
    if num_tags > 0:
        tags = tags[:num_tags]

    return tags or ["#content", "#image"]
