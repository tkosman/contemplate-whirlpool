import sys
from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_path))

from thinker import Thinker
import aiohttp
import re
from urllib.parse import quote
import logging
import spacy
import random


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load spaCy model for noun extraction
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("spaCy model 'en_core_web_sm' not found. Install it with: python -m spacy download en_core_web_sm")
    nlp = None


class RedditThinker(Thinker):
    async def think(self, thought: str) -> str:
        logger.debug(f"Received thought: {thought}")
        if not thought or not thought.strip():
            logger.debug("Empty or invalid thought provided.")
            return ""

        query = thought.strip()
        search_api = f"https://www.reddit.com/search.json?q={quote(query)}"
        session_timeout = aiohttp.ClientTimeout(total=10)

        headers = {
            "User-Agent": "RedditThinker/1.0 (https://github.com/your-repo)"
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            # 1) Search for relevant posts
            try:
                async with session.get(search_api, timeout=session_timeout) as resp:
                    search_json = await resp.json()
                    logger.debug(f"Search API response: {search_json}")
            except Exception as e:
                logger.error(f"Error during search API call: {e}")
                return ""

            posts = search_json.get("data", {}).get("children", [])
            title = None
            qlower = query.lower()

            # prefer exact or containing-title match
            for post in posts:
                t = post.get("data", {}).get("title", "")
                if t and (t.lower() == qlower or qlower in t.lower()):
                    title = t
                    break

            # 2) fallback to first search result
            if not title and posts:
                title = posts[0].get("data", {}).get("title", "")

            if not title:
                logger.debug("No title found for the query.")
                return ""

            # 3) Get post content (selftext)
            post_data = posts[0].get("data", {}) if posts else {}
            selftext = post_data.get("selftext", "")

            extract = selftext or title

            if not extract:
                logger.debug("No extract found for the post.")
                return ""

            # 4) Get the first sentence
            extract = re.sub(r"\s+", " ", extract).strip()
            sentences = re.split(r"(?<=[.!?])\s+", extract)
            first_sentence = sentences[0].strip() if sentences else extract

            # 5) Use spaCy for noun extraction if available
            if nlp:
                doc = nlp(first_sentence)
                candidates = []
                
                # First, collect proper nouns (PROPN)
                for token in doc:
                    if token.pos_ == "PROPN" and token.text.lower() != thought.lower():
                        candidates.append(token.text)
                
                # Next, collect named entities
                for ent in doc.ents:
                    if ent.text.lower() != thought.lower():
                        candidates.append(ent.text)
                
                # Fallback: collect any noun longer than 2 characters
                if not candidates:
                    for token in doc:
                        if token.pos_ in ["NOUN", "PROPN"] and len(token.text) > 2 and token.text.lower() != thought.lower():
                            candidates.append(token.text)
                
                # Return random candidate if any found
                if candidates:
                    result = random.choice(candidates)
                    logger.debug(f"Extracted noun (spaCy): {result} from {len(candidates)} candidates")
                    return result            # 6) Fallback to regex-based extraction if spaCy not available
            tokens = re.findall(r"[A-Za-z][A-Za-z'-]*", first_sentence)
            articles = {"the", "a", "an", "this", "that", "these", "those"}
            candidates = []
            
            # Look for capitalized words (proper nouns)
            i = 0
            while i < len(tokens):
                tok = tokens[i]
                if tok.lower() not in articles and tok[0].isupper():
                    name = tok
                    j = i + 1
                    while j < len(tokens) and tokens[j][0].isupper():
                        name += " " + tokens[j]
                        j += 1
                    if name.lower() != thought.lower():
                        candidates.append(name)
                    i = j
                else:
                    i += 1

            # fallback: collect non-article tokens longer than 2
            if not candidates:
                for tok in tokens:
                    if tok.lower() not in articles and len(tok) > 2 and tok.lower() != thought.lower():
                        candidates.append(tok)

            # Return random candidate if any found
            if candidates:
                result = random.choice(candidates)
                logger.debug(f"Extracted noun (regex): {result} from {len(candidates)} candidates")
                return result            # last resort: use the first token from the title
            title_tokens = re.findall(r"[A-Za-z][A-Za-z'-]*", title)
            if title_tokens and title_tokens[0].lower() != thought.lower():
                logger.debug(f"Fallback title token: {title_tokens[0]}")
                return title_tokens[0]
            
            # ultimate fallback: generate a random common noun
            if nlp:
                common_nouns = ["idea", "concept", "thought", "question", "answer", "theory", "subject", "topic", "matter", "issue"]
                result = random.choice(common_nouns)
                logger.debug(f"Generated random noun: {result}")
                return result
            
            return ""


if __name__ == "__main__":
    import asyncio

    async def main():
        thinker = RedditThinker("RedditThinker")

        # Test with a valid thought
        thought = "Python programming"
        result = await thinker.think(thought)
        print(f"Input: {thought}\nOutput: {result}\n")

        # Test with an empty thought
        thought = ""
        result = await thinker.think(thought)
        print(f"Input: {thought}\nOutput: {result}\n")

        # Test with a thought that may not exist
        thought = "asdkjhasdkjhasd"
        result = await thinker.think(thought)
        print(f"Input: {thought}\nOutput: {result}\n")

    asyncio.run(main())
