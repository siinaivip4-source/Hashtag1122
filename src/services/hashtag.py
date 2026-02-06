import re
from typing import List

STOPWORDS = {
    "a", "an", "the", "of", "on", "in", "and", "with", "for", "to", "at",
    "is", "are", "this", "that", "it", "by", "from",
}


def caption_to_hashtags(caption: str, num_tags: int = 5, language: str = "vi", custom_keywords: List[str] = None) -> List[str]:
    # Check if custom keywords are provided
    if custom_keywords:
        # Normalize caption and keywords for matching
        caption_lower = caption.lower()
        matched = []
        for kw in custom_keywords:
            kw_clean = kw.strip()
            if kw_clean and kw_clean.lower() in caption_lower:
                matched.append(kw_clean)
        
        # Format as hashtags
        tags = [f"#{w.replace(' ', '')}" for w in matched]
        # Limit to num_tags
        if num_tags > 0:
            tags = tags[:num_tags]
        return tags

    # Default logic (auto-generation)
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
