import sys
from pathlib import Path
import os

backend_path = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_path))

from thinker import Thinker
import aiohttp
import re
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


class NYTThinker(Thinker):
    async def think(self, thought: str) -> str:
        logger.debug(f"Received thought: {thought}")
        if not thought or not thought.strip():
            logger.debug("Empty or invalid thought provided.")
            return ""

        query = thought.strip()
        api_key = "3SYcLc0XC83D4UrbCaaeqdq1C1fjIB5Q"
        search_api = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
        session_timeout = aiohttp.ClientTimeout(total=10)

        headers = {
            "User-Agent": "NYTThinker/1.0 (https://github.com/your-repo)"
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            # 1) Search for relevant articles
            params = {
                "q": query,
                "api-key": api_key,
                "sort": "relevance"
            }
            try:
                async with session.get(search_api, params=params, timeout=session_timeout) as resp:
                    search_json = await resp.json()
                    logger.debug(f"Search API response: {search_json}")
            except Exception as e:
                logger.error(f"Error during search API call: {e}")
                return ""

            docs = search_json.get("response", {}).get("docs", [])
            headline = None
            qlower = query.lower()

            # prefer exact or containing-headline match
            for doc in docs:
                h = doc.get("headline", {}).get("main", "")
                if h and (h.lower() == qlower or qlower in h.lower()):
                    headline = h
                    break

            # 2) fallback to first search result
            if not headline and docs:
                headline = docs[0].get("headline", {}).get("main", "")

            if not headline:
                logger.debug("No headline found for the query.")
                return ""

            # 3) Get article content (abstract or lead_paragraph)
            article = docs[0] if docs else {}
            abstract = article.get("abstract", "")
            lead_paragraph = article.get("lead_paragraph", "")

            extract = abstract or lead_paragraph or ""

            if not extract:
                logger.debug("No extract found for the article.")
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
                return result            # last resort: use the first token from the headline
            headline_tokens = re.findall(r"[A-Za-z][A-Za-z'-]*", headline)
            if headline_tokens and headline_tokens[0].lower() != thought.lower():
                logger.debug(f"Fallback headline token: {headline_tokens[0]}")
                return headline_tokens[0]
            
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
        thinker = NYTThinker("NYTThinker")

        # Test with a valid thought
        thought = "climate change"
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
