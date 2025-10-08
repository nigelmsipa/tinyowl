"""Query enhancement utilities for better biblical search results"""

from typing import Dict, List, Set

# Biblical phrase expansions for better retrieval
BIBLICAL_PHRASES: Dict[str, List[str]] = {
    # Messianic titles
    "king of glory": ["LORD strong mighty", "Psalm 24", "gates lift up heads", "King of Glory"],
    "son of god": ["Jesus Christ", "divine", "Messiah", "only begotten"],
    "son of man": ["Daniel", "Jesus", "humanity", "prophet"],
    "lamb of god": ["sacrifice", "John Baptist", "Passover", "redemption"],
    "bread of life": ["Jesus living bread", "John 6", "manna", "eternal life"],
    "light of the world": ["Jesus light", "darkness", "John 8", "lamp"],
    "good shepherd": ["Jesus shepherd", "sheep", "John 10", "lay down life"],
    "alpha omega": ["beginning end", "first last", "Revelation", "eternal"],

    # Key doctrines
    "unpardonable sin": ["blasphemy holy spirit", "forgiveness", "Matthew 12", "eternal sin"],
    "investigative judgment": ["sanctuary", "1844", "Daniel 8:14", "cleansing sanctuary"],
    "second coming": ["return Jesus", "parousia", "clouds glory", "revelation"],
    "sabbath": ["seventh day", "rest", "holy", "commandment", "remember"],
    "state of dead": ["soul sleep", "death", "resurrection", "grave"],
    "remnant church": ["commandments God", "testimony Jesus", "Revelation 12:17"],

    # Biblical concepts
    "born again": ["new birth", "regeneration", "John 3", "Nicodemus", "Spirit"],
    "justified by faith": ["Romans", "righteousness", "believe", "grace", "works"],
    "sanctification": ["holy", "Spirit", "progressive", "growth", "righteousness"],
    "atonement": ["sacrifice", "reconciliation", "blood", "forgiveness", "propitiation"],
    "covenant": ["promise", "testament", "Abraham", "new covenant", "blood"],
    "grace": ["unmerited favor", "gift", "salvation", "mercy", "free"],
    "redemption": ["ransom", "bought", "blood", "deliverance", "salvation"],

    # Prophetic terms
    "little horn": ["Daniel 7", "Daniel 8", "antichrist", "power", "persecution"],
    "mark of beast": ["Revelation 13", "666", "forehead hand", "worship"],
    "beast revelation": ["dragon", "leopard", "bear", "lion", "sea"],
    "woman wilderness": ["Revelation 12", "church", "persecution", "1260 days"],
    "144000": ["sealed", "Revelation 7", "Revelation 14", "firstfruits"],

    # Old Testament figures
    "son of david": ["Messiah", "throne", "covenant", "eternal kingdom"],
    "servant of lord": ["Isaiah 53", "suffering servant", "Messiah", "prophecy"],
    "branch": ["Zechariah", "Messiah", "righteous", "David"],

    # Theological questions
    "who is god": ["LORD", "Yahweh", "creator", "eternal", "holy"],
    "what is sin": ["transgression law", "unrighteousness", "death", "separation"],
    "what is salvation": ["saved", "grace", "faith", "Jesus", "eternal life"],
    "how to be saved": ["believe", "repent", "baptized", "faith Jesus", "confession"],
}

# Common theological synonyms for query expansion
THEOLOGICAL_SYNONYMS: Dict[str, Set[str]] = {
    "jesus": {"christ", "messiah", "savior", "lord", "son of god", "lamb"},
    "god": {"lord", "yahweh", "jehovah", "father", "almighty", "creator"},
    "holy spirit": {"spirit", "comforter", "ghost", "advocate", "paraclete"},
    "devil": {"satan", "adversary", "enemy", "serpent", "dragon", "lucifer"},
    "heaven": {"paradise", "glory", "eternal life", "kingdom", "new jerusalem"},
    "hell": {"gehenna", "lake of fire", "destruction", "perdition", "grave"},
    "church": {"assembly", "congregation", "body of christ", "ecclesia", "believers"},
    "gospel": {"good news", "message", "evangel", "glad tidings"},
    "faith": {"belief", "trust", "confidence", "assurance"},
    "prayer": {"supplication", "petition", "intercession", "communion"},
}


def expand_biblical_query(query: str) -> str:
    """
    Expand query with biblical phrases and theological synonyms

    Args:
        query: Original user query

    Returns:
        Expanded query with additional theological terms
    """
    query_lower = query.lower().strip()

    # Check for exact biblical phrases
    for phrase, expansions in BIBLICAL_PHRASES.items():
        if phrase in query_lower:
            # Add expansion terms to boost retrieval
            return f"{query} {' '.join(expansions)}"

    # Check for theological synonyms (expand single important terms)
    words = query_lower.split()
    expanded_terms = []

    for word in words:
        word_clean = word.strip('.,!?;:"\'()[]{}')
        if word_clean in THEOLOGICAL_SYNONYMS:
            # Add top 2-3 synonyms
            synonyms = list(THEOLOGICAL_SYNONYMS[word_clean])[:3]
            expanded_terms.extend(synonyms)

    if expanded_terms:
        return f"{query} {' '.join(expanded_terms)}"

    return query


def extract_key_biblical_terms(query: str) -> List[str]:
    """
    Extract key biblical terms from query for keyword matching

    Args:
        query: User query

    Returns:
        List of important biblical terms to search for
    """
    query_lower = query.lower()
    key_terms = []

    # Extract biblical phrases
    for phrase in BIBLICAL_PHRASES.keys():
        if phrase in query_lower:
            key_terms.append(phrase)

    # Extract theological terms
    for term in THEOLOGICAL_SYNONYMS.keys():
        if term in query_lower:
            key_terms.append(term)

    # Extract book names (simplified - full list in osis_canonical.yaml)
    book_names = [
        "genesis", "exodus", "leviticus", "numbers", "deuteronomy",
        "joshua", "judges", "ruth", "samuel", "kings", "chronicles",
        "ezra", "nehemiah", "esther", "job", "psalm", "proverbs",
        "ecclesiastes", "song", "isaiah", "jeremiah", "lamentations",
        "ezekiel", "daniel", "hosea", "joel", "amos", "obadiah",
        "jonah", "micah", "nahum", "habakkuk", "zephaniah", "haggai",
        "zechariah", "malachi", "matthew", "mark", "luke", "john",
        "acts", "romans", "corinthians", "galatians", "ephesians",
        "philippians", "colossians", "thessalonians", "timothy",
        "titus", "philemon", "hebrews", "james", "peter", "jude",
        "revelation"
    ]

    for book in book_names:
        if book in query_lower:
            key_terms.append(book)

    return key_terms


def should_use_hybrid_search(query: str) -> bool:
    """
    Determine if query should use hybrid search (semantic + keyword)

    Hybrid search is best for:
    - Biblical phrases ("King of Glory")
    - Specific doctrinal terms
    - Queries with book names

    Args:
        query: User query

    Returns:
        True if hybrid search should be used
    """
    query_lower = query.lower()

    # Use hybrid for known biblical phrases
    if any(phrase in query_lower for phrase in BIBLICAL_PHRASES.keys()):
        return True

    # Use hybrid for theological terms
    if any(term in query_lower for term in THEOLOGICAL_SYNONYMS.keys()):
        return True

    # Use hybrid for short queries (likely looking for specific terms)
    if len(query.split()) <= 4:
        return True

    return False
