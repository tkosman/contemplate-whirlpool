import sys
from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_path))

from Thinker import Thinker
import aiohttp
import re
from urllib.parse import quote
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class WikipediaThinker(Thinker):
    async def think(self, thought: str) -> str:
        logger.debug(f"Received thought: {thought}")
        if not thought or not thought.strip():
            logger.debug("Empty or invalid thought provided.")
            return ""

        query = thought.strip()
        search_api = "https://en.wikipedia.org/w/api.php"
        session_timeout = aiohttp.ClientTimeout(total=10)

        headers = {
            "User-Agent": "WikipediaThinker/1.0 (https://github.com/your-repo)"
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            # 1) Search for relevant pages
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "utf8": 1,
                "srlimit": 10,
            }
            try:
                async with session.get(search_api, params=params, timeout=session_timeout) as resp:
                    search_json = await resp.json()
                    logger.debug(f"Search API response: {search_json}")
            except Exception as e:
                logger.error(f"Error during search API call: {e}")
                return ""

            results = search_json.get("query", {}).get("search", [])
            title = None
            qlower = query.lower()

            # prefer exact or containing-title match
            for r in results:
                t = r.get("title", "")
                if t and (t.lower() == qlower or qlower in t.lower()):
                    title = t
                    break

            # 2) if not found, try intitle: search
            if not title:
                params_intitle = params.copy()
                params_intitle["srsearch"] = f'intitle:"{query}"'
                try:
                    async with session.get(search_api, params=params_intitle, timeout=session_timeout) as resp2:
                        js2 = await resp2.json()
                        logger.debug(f"Intitle search API response: {js2}")
                        res2 = js2.get("query", {}).get("search", [])
                        if res2:
                            title = res2[0].get("title")
                except Exception as e:
                    logger.error(f"Error during intitle search API call: {e}")

            # 3) fallback to first search result
            if not title and results:
                title = results[0].get("title")

            if not title:
                logger.debug("No title found for the query.")
                return ""

            # 4) Get page summary (first paragraph / extract)
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title, safe='')}"
            extract = ""
            try:
                async with session.get(summary_url, timeout=session_timeout) as resp3:
                    if resp3.status == 200:
                        js3 = await resp3.json()
                        logger.debug(f"Summary API response: {js3}")
                        extract = js3.get("extract", "") or js3.get("description", "") or ""
            except Exception as e:
                logger.error(f"Error during summary API call: {e}")
                extract = ""

            # fallback to extracts API if summary empty
            if not extract:
                params_extract = {
                    "action": "query",
                    "prop": "extracts",
                    "explaintext": 1,
                    "exintro": 1,
                    "titles": title,
                    "format": "json",
                    "utf8": 1,
                }
                try:
                    async with session.get(search_api, params=params_extract, timeout=session_timeout) as resp4:
                        js4 = await resp4.json()
                        logger.debug(f"Extracts API response: {js4}")
                        pages = js4.get("query", {}).get("pages", {})
                        for p in pages.values():
                            extract = p.get("extract", "") or extract
                            break
                except Exception as e:
                    logger.error(f"Error during extracts API call: {e}")

            if not extract:
                logger.debug("No extract found for the title.")
                return ""

            # 5) Get the first sentence
            extract = re.sub(r"\s+", " ", extract).strip()
            sentences = re.split(r"(?<=[.!?])\s+", extract)
            first_sentence = sentences[0].strip() if sentences else extract

            # 6) Heuristic noun extraction from first sentence:
            tokens = re.findall(r"[A-Za-z][A-Za-z'-]*", first_sentence)
            articles = {"the", "a", "an", "this", "that", "these", "those"}
            for i, tok in enumerate(tokens):
                if tok.lower() in articles:
                    continue
                if tok[0].isupper():
                    name = tok
                    j = i + 1
                    while j < len(tokens) and tokens[j][0].isupper():
                        name += " " + tokens[j]
                        j += 1
                    if name.lower() != thought.lower():
                        logger.debug(f"Extracted proper noun: {name}")
                        return name

            # fallback: first non-article token longer than 2
            for tok in tokens:
                if tok.lower() in articles:
                    continue
                if len(tok) > 2 and tok.lower() != thought.lower():
                    logger.debug(f"Fallback token: {tok}")
                    return tok

            # last resort: use the first token from the page title
            title_tokens = re.findall(r"[A-Za-z][A-Za-z'-]*", title)
            fallback_title = title_tokens[0] if title_tokens and title_tokens[0].lower() != thought.lower() else ""
            logger.debug(f"Fallback title token: {fallback_title}")
            return fallback_title


if __name__ == "__main__":
    import asyncio

    async def main():
        thinker = WikipediaThinker("WikipediaThinker")

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
