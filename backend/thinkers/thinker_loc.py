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


class LOCThinker(Thinker):
    async def think(self, thought: str) -> str:
        logger.debug(f"Received thought: {thought}")
        if not thought or not thought.strip():
            logger.debug("Empty or invalid thought provided.")
            common_nouns = ["idea", "concept", "thought", "question", "answer", "theory", "subject", "topic", "matter", "issue"]
            result = random.choice(common_nouns)
            logger.debug(f"Generated random noun: {result}")
            return result

        query = thought.strip()
        search_api = "https://www.loc.gov/search/"
        session_timeout = aiohttp.ClientTimeout(total=10)

        headers = {
            "User-Agent": "LOCThinker/1.0 (https://github.com/your-repo)"
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            # 1) Search for relevant items
            params = {
                "q": query,
                "fo": "json",
                "c": 10
            }
            try:
                async with session.get(search_api, params=params, timeout=session_timeout) as resp:
                    search_json = await resp.json()
                    logger.debug(f"Search API response: {search_json}")
            except Exception as e:
                logger.error(f"Error during search API call: {e}")
                return ""

            results = search_json.get("results", [])
            title = None
            qlower = query.lower()

            # prefer exact or containing-title match
            for r in results:
                t = r.get("title", "")
                if t and (t.lower() == qlower or qlower in t.lower()):
                    title = t
                    break

            # 2) fallback to first search result
            if not title and results:
                title = results[0].get("title", "")

            if not title:
                logger.debug("No title found for the query.")
                common_nouns = ["idea", "concept", "thought", "question", "answer", "theory", "subject", "topic", "matter", "issue"]
                result = random.choice(common_nouns)
                logger.debug(f"Generated random noun: {result}")
                return result

            # 3) Get item content (description or summary)
            item = results[0] if results else {}
            description = item.get("description", [])

            # Description can be a list, join if necessary
            if isinstance(description, list):
                extract = " ".join(description)
            else:
                extract = description or ""

            # Fallback to title if no description
            extract = extract or title

            if not extract:
                logger.debug("No extract found for the item.")
                common_nouns = ["idea", "concept", "thought", "question", "answer", "theory", "subject", "topic", "matter", "issue"]
                result = random.choice(common_nouns)
                logger.debug(f"Generated random noun: {result}")
                return result

            # 4) Get the first sentence
            extract = re.sub(r"\s+", " ", extract).strip()
            sentences = re.split(r"(?<=[.!?])\s+", extract)
            first_sentence = sentences[0].strip() if sentences else extract

            # 5) Use spaCy for noun extraction if available
            if self.nlp:
                doc = self.nlp(first_sentence)
                candidates = []

                # First, collect proper nouns (PROPN)
                for token in doc:
                    if token.pos_ == "PROPN" and token.text.lower() != thought.lower() and not token.text.isdigit() and token.text.isalpha():
                        candidates.append(token.text)

                # Next, collect named entities
                for ent in doc.ents:
                    if ent.text.lower() != thought.lower() and not ent.text.isdigit() and any(c.isalpha() for c in ent.text):
                        candidates.append(ent.text)

                # Fallback: collect any noun longer than 2 characters
                if not candidates:
                    for token in doc:
                        if token.pos_ in ["NOUN", "PROPN"] and len(token.text) > 2 and token.text.lower() != thought.lower() and not token.text.isdigit() and token.text.isalpha():
                            candidates.append(token.text)

                # Return random candidate if any found
                if candidates:
                    result = random.choice(candidates)
                    logger.debug(f"Extracted noun (spaCy): {result} from {len(candidates)} candidates")
                    return result

            # 6) Fallback to regex-based extraction if spaCy not available
            tokens = re.findall(r"[A-Za-z][A-Za-z'-]*", first_sentence)
            articles = {"the", "a", "an", "this", "that", "these", "those"}
            candidates = []

            # Look for capitalized words (proper nouns)
            i = 0
            while i < len(tokens):
                tok = tokens[i]
                if tok.lower() not in articles and tok[0].isupper() and tok.isalpha():
                    name = tok
                    j = i + 1
                    while j < len(tokens) and tokens[j][0].isupper() and tokens[j].isalpha():
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
                    if tok.lower() not in articles and len(tok) > 2 and tok.lower() != thought.lower() and tok.isalpha():
                        candidates.append(tok)

            # Return random candidate if any found
            if candidates:
                result = random.choice(candidates)
                logger.debug(f"Extracted noun (regex): {result} from {len(candidates)} candidates")
                return result

            # last resort: use the first token from the title
            title_tokens = re.findall(r"[A-Za-z][A-Za-z'-]*", title)
            if title_tokens and title_tokens[0].lower() != thought.lower():
                logger.debug(f"Fallback title token: {title_tokens[0]}")
                return title_tokens[0]

            # ultimate fallback: generate a random common noun
            if self.nlp:
                common_nouns = ["idea", "concept", "thought", "question", "answer", "theory", "subject", "topic", "matter", "issue"]
                result = random.choice(common_nouns)
                logger.debug(f"Generated random noun: {result}")
                return result

            return ""


if __name__ == "__main__":
    import asyncio

    async def main():
        thinker = LOCThinker("LOCThinker")

        # Test with a valid thought
        thought = "Abraham Lincoln"
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
