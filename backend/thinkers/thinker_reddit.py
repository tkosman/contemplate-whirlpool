from Thinker import Thinker
import aiohttp
import logging
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class RedditThinker(Thinker):
    async def think(self, thought: str) -> str:
        logger.debug(f"Received thought: {thought}")
        if not thought or not thought.strip():
            logger.debug("Empty or invalid thought provided.")
            return ""

        search_api = f"https://www.reddit.com/search.json?q={thought}"
        headers = {"User-Agent": "RedditThinker/1.0"}

        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.get(search_api) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.debug(f"Reddit API response: {data}")
                        posts = data.get("data", {}).get("children", [])
                        if posts:
                            title = posts[0].get("data", {}).get("title", "")
                            if title.lower() != thought.lower():
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
                logger.error(f"Error during Reddit API call: {e}")

        return ""
