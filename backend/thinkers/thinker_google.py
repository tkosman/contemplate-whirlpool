from Thinker import Thinker
import aiohttp
import logging
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class GoogleSearchThinker(Thinker):
    async def think(self, thought: str) -> str:
        logger.debug(f"Received thought: {thought}")
        if not thought or not thought.strip():
            logger.debug("Empty or invalid thought provided.")
            return ""

        search_api = "https://serpapi.com/search"
        api_key = "your-serpapi-key"
        params = {
            "q": thought,
            "api_key": api_key
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(search_api, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.debug(f"Google Search API response: {data}")
                        results = data.get("organic_results", [])
                        if results:
                            title = results[0].get("title", "")
                            if title.lower() != thought.lower():
                                # Extract the first sentence or significant token
                                title = re.sub(r"\s+", " ", title).strip()
                                sentences = re.split(r"(?<=[.!?])\s+", title)
                                first_sentence = sentences[0].strip() if sentences else title

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

                                for tok in tokens:
                                    if tok.lower() in articles:
                                        continue
                                    if len(tok) > 2 and tok.lower() != thought.lower():
                                        logger.debug(f"Fallback token: {tok}")
                                        return tok

                                title_tokens = re.findall(r"[A-Za-z][A-Za-z'-]*", title)
                                fallback_title = title_tokens[0] if title_tokens and title_tokens[0].lower() != thought.lower() else ""
                                logger.debug(f"Fallback title token: {fallback_title}")
                                return fallback_title
            except Exception as e:
                logger.error(f"Error during Google Search API call: {e}")

        return ""
