from __future__ import annotations

import json
import os
from urllib.parse import urlparse

import scrapy

from my_spider_project.items import VideoCandidateItem


class VideoCandidatesSpider(scrapy.Spider):
    name = "video_candidates"
    allowed_video_hosts = {
        "youtube.com": "youtube",
        "www.youtube.com": "youtube",
        "youtu.be": "youtube",
        "reddit.com": "reddit",
        "www.reddit.com": "reddit",
        "redd.it": "reddit",
        "v.redd.it": "reddit",
        "tiktok.com": "tiktok",
        "www.tiktok.com": "tiktok",
        "instagram.com": "instagram",
        "www.instagram.com": "instagram",
        "x.com": "x",
        "www.x.com": "x",
        "twitter.com": "x",
        "www.twitter.com": "x",
    }

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "FEED_EXPORT_FIELDS": [
            "url",
            "platform",
            "title",
            "summary",
            "publishedAt",
            "buzzScore",
            "saturationLevel",
            "rationale",
            "sourcePage",
            "topic",
        ],
    }

    def __init__(self, topic: str | None = None, seed_url: str | None = None, seed_urls: str | None = None, max_pages: int = 20, max_items: int = 25, *args, **kwargs):
        super().__init__(*args, **kwargs)
        env_topic = os.getenv("SPIDER_TOPIC", "").strip()
        self.topic = (topic or env_topic or "viral video").strip()
        raw_seeds = []
        env_seed_url = os.getenv("SPIDER_SEED_URL", "").strip()
        env_seed_urls = os.getenv("SPIDER_SEED_URLS", "").strip()
        if seed_url or env_seed_url:
            raw_seeds.append((seed_url or env_seed_url).strip())
        if seed_urls or env_seed_urls:
            raw_seeds.extend(part.strip() for part in (seed_urls or env_seed_urls).split(",") if part.strip())
        self.start_urls = raw_seeds
        self.max_pages = int(max_pages)
        self.max_items = int(max_items)
        self.visited_pages = 0
        self.found_items = 0
        self.seen_video_urls: set[str] = set()
        self.seen_pages: set[str] = set()

    async def start(self):
        if not self.start_urls:
            raise RuntimeError(
                "Pass at least one feed-like seed via -a seed_url=... or -a seed_urls=... . "
                "Recommended: RSS/Atom/JSON endpoints that contain video links."
            )
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)

    def parse(self, response: scrapy.http.Response):
        if response.url in self.seen_pages:
            return
        self.seen_pages.add(response.url)
        self.visited_pages += 1

        content_type = (response.headers.get("Content-Type") or b"").decode("utf-8", errors="ignore").lower()
        body_start = response.text.lstrip()[:64].lower()
        if any(token in content_type for token in ["xml", "rss", "atom"]) or body_start.startswith("<?xml") or body_start.startswith("<rss") or body_start.startswith("<feed"):
            yield from self._parse_xml_feed(response)
            return

        if "json" in content_type or body_start.startswith("{") or body_start.startswith("["):
            yield from self._parse_json_feed(response)
            return

        yield from self._parse_html(response)

    def _parse_xml_feed(self, response: scrapy.http.Response):
        entries = response.xpath("//*[local-name()='item' or local-name()='entry']")
        for entry in entries:
            url = self._extract_entry_url(response, entry)
            if not url:
                continue
            item = self._build_item(
                url=url,
                title=self._extract_first(entry, ["./title/text()", ".//*[local-name()='title']/text()"]),
                summary=self._extract_first(entry, ["./description/text()", ".//*[local-name()='summary']/text()", ".//*[local-name()='content']/text()"]),
                published_at=self._extract_first(entry, ["./pubDate/text()", ".//*[local-name()='published']/text()", ".//*[local-name()='updated']/text()"]),
                source_page=response.url,
                rationale=f'Found in feed {response.url} for topic "{self.topic}".',
                buzz_text=" ".join(entry.xpath(".//text()").getall()),
            )
            if item:
                yield item
            if self.found_items >= self.max_items:
                return

    def _parse_json_feed(self, response: scrapy.http.Response):
        try:
            payload = json.loads(response.text)
        except json.JSONDecodeError:
            return

        if isinstance(payload, dict):
            records = payload.get("items") or payload.get("results") or payload.get("data") or []
        elif isinstance(payload, list):
            records = payload
        else:
            records = []

        for record in records:
            if not isinstance(record, dict):
                continue
            url = self._first_nonempty(record.get(key) for key in ["url", "link", "videoUrl", "sourceUrl"])
            item = self._build_item(
                url=url,
                title=self._clean_text(self._first_nonempty(record.get(key) for key in ["title", "headline", "name"])),
                summary=self._clean_text(self._first_nonempty(record.get(key) for key in ["summary", "description", "excerpt"])),
                published_at=self._clean_text(self._first_nonempty(record.get(key) for key in ["publishedAt", "published_at", "createdAt", "timestamp"])),
                source_page=response.url,
                rationale=f'Found in JSON feed {response.url} for topic "{self.topic}".',
                buzz_text=json.dumps(record, ensure_ascii=False),
            )
            if item:
                yield item
            if self.found_items >= self.max_items:
                return

    def _parse_html(self, response: scrapy.http.Response):
        page_title = self._first_text(response.css("title::text").get())
        page_summary = self._first_text(
            response.css("meta[name='description']::attr(content), meta[property='og:description']::attr(content)").get()
        )
        published_at = self._first_text(
            response.css(
                "meta[property='article:published_time']::attr(content), meta[name='pubdate']::attr(content), time::attr(datetime)"
            ).get()
        )

        for href in response.css("a::attr(href)").getall():
            item = self._build_item(
                url=response.urljoin(href),
                title=page_title,
                summary=page_summary,
                published_at=published_at,
                source_page=response.url,
                rationale=f'Found on {response.url} for topic "{self.topic}".',
                buzz_text=response.text,
            )
            if item:
                yield item
            if self.found_items >= self.max_items:
                return

        if self.visited_pages >= self.max_pages or self.found_items >= self.max_items:
            return

        current_host = urlparse(response.url).netloc
        for href in response.css("a::attr(href)").getall():
            next_url = response.urljoin(href)
            next_host = urlparse(next_url).netloc
            if next_url in self.seen_pages or next_host != current_host:
                continue
            if any(part in next_url.lower() for part in ["login", "signup", "account", "submit"]):
                continue
            yield response.follow(next_url, callback=self.parse)

    def _extract_entry_url(self, response: scrapy.http.Response, entry) -> str:
        link_candidates = entry.xpath("./link/text()").getall()
        if not link_candidates:
            link_candidates = entry.xpath(".//*[local-name()='link']/@href").getall()
        if not link_candidates:
            link_candidates = entry.xpath(".//*[local-name()='guid']/text()").getall()
        first = self._first_nonempty(link_candidates)
        return response.urljoin(first) if first else ""

    def _extract_first(self, selector, queries: list[str]) -> str:
        for query in queries:
            value = selector.xpath(query).get()
            if value and value.strip():
                return self._clean_text(value)
        return ""

    def _build_item(self, url: str | None, title: str, summary: str, published_at: str, source_page: str, rationale: str, buzz_text: str):
        clean_url = (url or "").strip()
        platform = self._detect_platform(clean_url)
        if not platform or clean_url in self.seen_video_urls:
            return None

        self.seen_video_urls.add(clean_url)
        self.found_items += 1
        return VideoCandidateItem(
            url=clean_url,
            platform=platform,
            title=self._clean_text(title),
            summary=self._clean_text(summary),
            publishedAt=self._clean_text(published_at),
            buzzScore=self._estimate_buzz_score(buzz_text),
            saturationLevel="medium",
            rationale=rationale,
            sourcePage=source_page,
            topic=self.topic,
        )

    def _detect_platform(self, url: str) -> str | None:
        host = urlparse(url).netloc.lower()
        return self.allowed_video_hosts.get(host)

    def _estimate_buzz_score(self, text: str) -> int:
        lower = text.lower()
        score = 10
        for token, delta in [("views", 3), ("likes", 2), ("shares", 2), ("comments", 1), ("viral", 3), ("trend", 2)]:
            if token in lower:
                score += delta
        return min(score, 25)

    def _first_nonempty(self, values):
        for value in values:
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def _clean_text(self, value: str | None) -> str:
        return (value or "").replace("\n", " ").replace("\r", " ").strip()

    def _first_text(self, value: str | None) -> str:
        return self._clean_text(value)
