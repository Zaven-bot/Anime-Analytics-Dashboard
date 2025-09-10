"""
Test fixtures for unit tests.
Contains mock data and common test utilities.
"""

from datetime import date
from typing import Dict, Any

# Mock Jikan API response for testing
MOCK_JIKAN_SEARCH_RESPONSE = {
    "data": [
        {
            "mal_id": 1,
            "url": "https://myanimelist.net/anime/1/Cowboy_Bebop",
            "images": {
                "jpg": {
                    "image_url": "https://cdn.myanimelist.net/images/anime/4/19644.jpg",
                    "small_image_url": "https://cdn.myanimelist.net/images/anime/4/19644t.jpg",
                    "large_image_url": "https://cdn.myanimelist.net/images/anime/4/19644l.jpg"
                },
                "webp": {
                    "image_url": "https://cdn.myanimelist.net/images/anime/4/19644.webp",
                    "small_image_url": "https://cdn.myanimelist.net/images/anime/4/19644t.webp",
                    "large_image_url": "https://cdn.myanimelist.net/images/anime/4/19644l.webp"
                }
            },
            "trailer": {
                "youtube_id": "QCaEJZqLeTU",
                "url": "https://www.youtube.com/watch?v=QCaEJZqLeTU",
                "embed_url": "https://www.youtube.com/embed/QCaEJZqLeTU"
            },
            "approved": True,
            "titles": [
                {
                    "type": "Default",
                    "title": "Cowboy Bebop"
                },
                {
                    "type": "Japanese",
                    "title": "カウボーイビバップ"
                }
            ],
            "title": "Cowboy Bebop",
            "title_english": "Cowboy Bebop",
            "title_japanese": "カウボーイビバップ",
            "title_synonyms": [],
            "type": "TV",
            "source": "Original",
            "episodes": 26,
            "status": "Finished Airing",
            "airing": False,
            "aired": {
                "from": "1998-04-03T00:00:00+00:00",
                "to": "1999-04-24T00:00:00+00:00",
                "prop": {
                    "from": {
                        "day": 3,
                        "month": 4,
                        "year": 1998
                    },
                    "to": {
                        "day": 24,
                        "month": 4,
                        "year": 1999
                    },
                    "string": "Apr 3, 1998 to Apr 24, 1999"
                }
            },
            "duration": "24 min per ep",
            "rating": "R - 17+ (violence & profanity)",
            "score": 8.75,
            "scored_by": 793823,
            "rank": 28,
            "popularity": 43,
            "members": 1281992,
            "favorites": 63490,
            "synopsis": "Crime is timeless. By the year 2071, humanity has expanded across the galaxy...",
            "background": "When Cowboy Bebop first aired in spring of 1998 on TV Tokyo...",
            "season": "spring",
            "year": 1998,
            "broadcast": {
                "day": "Saturdays",
                "time": "01:15",
                "timezone": "Asia/Tokyo",
                "string": "Saturdays at 01:15 (JST)"
            },
            "producers": [
                {
                    "mal_id": 23,
                    "type": "anime",
                    "name": "Bandai Visual",
                    "url": "https://myanimelist.net/anime/producer/23/Bandai_Visual"
                }
            ],
            "licensors": [
                {
                    "mal_id": 102,
                    "type": "anime",
                    "name": "Funimation",
                    "url": "https://myanimelist.net/anime/producer/102/Funimation"
                }
            ],
            "studios": [
                {
                    "mal_id": 14,
                    "type": "anime",
                    "name": "Sunrise",
                    "url": "https://myanimelist.net/anime/producer/14/Sunrise"
                }
            ],
            "genres": [
                {
                    "mal_id": 1,
                    "type": "anime",
                    "name": "Action",
                    "url": "https://myanimelist.net/anime/genre/1/Action"
                },
                {
                    "mal_id": 8,
                    "type": "anime",
                    "name": "Drama",
                    "url": "https://myanimelist.net/anime/genre/8/Drama"
                }
            ],
            "explicit_genres": [],
            "themes": [
                {
                    "mal_id": 29,
                    "type": "anime",
                    "name": "Space",
                    "url": "https://myanimelist.net/anime/genre/29/Space"
                }
            ],
            "demographics": []
        },
        {
            "mal_id": 5,
            "url": "https://myanimelist.net/anime/5/Fullmetal_Alchemist",
            "images": {
                "jpg": {
                    "image_url": "https://cdn.myanimelist.net/images/anime/12/9548.jpg",
                    "small_image_url": "https://cdn.myanimelist.net/images/anime/12/9548t.jpg",
                    "large_image_url": "https://cdn.myanimelist.net/images/anime/12/9548l.jpg"
                },
                "webp": {
                    "image_url": "https://cdn.myanimelist.net/images/anime/12/9548.webp",
                    "small_image_url": "https://cdn.myanimelist.net/images/anime/12/9548t.webp",
                    "large_image_url": "https://cdn.myanimelist.net/images/anime/12/9548l.webp"
                }
            },
            "trailer": None,
            "approved": True,
            "titles": [
                {
                    "type": "Default",
                    "title": "Fullmetal Alchemist"
                }
            ],
            "title": "Fullmetal Alchemist",
            "title_english": "Fullmetal Alchemist",
            "title_japanese": "鋼の錬金術師",
            "title_synonyms": ["Hagane no Renkinjutsushi", "FMA"],
            "type": "TV",
            "source": "Manga",
            "episodes": 51,
            "status": "Finished Airing",
            "airing": False,
            "aired": {
                "from": "2003-10-04T00:00:00+00:00",
                "to": "2004-10-02T00:00:00+00:00",
                "prop": {
                    "from": {
                        "day": 4,
                        "month": 10,
                        "year": 2003
                    },
                    "to": {
                        "day": 2,
                        "month": 10,
                        "year": 2004
                    },
                    "string": "Oct 4, 2003 to Oct 2, 2004"
                }
            },
            "duration": "24 min per ep",
            "rating": "R - 17+ (violence & profanity)",
            "score": 8.12,
            "scored_by": 890000,
            "rank": 416,
            "popularity": 12,
            "members": 1500000,
            "favorites": 70000,
            "synopsis": "Edward Elric, a young, brilliant alchemist...",
            "background": "Fullmetal Alchemist was adapted...",
            "season": "fall",
            "year": 2003,
            "broadcast": {
                "day": "Saturdays",
                "time": "18:00",
                "timezone": "Asia/Tokyo",
                "string": "Saturdays at 18:00 (JST)"
            },
            "producers": [
                {
                    "mal_id": 17,
                    "type": "anime",
                    "name": "Aniplex",
                    "url": "https://myanimelist.net/anime/producer/17/Aniplex"
                }
            ],
            "licensors": [
                {
                    "mal_id": 102,
                    "type": "anime",
                    "name": "Funimation",
                    "url": "https://myanimelist.net/anime/producer/102/Funimation"
                }
            ],
            "studios": [
                {
                    "mal_id": 4,
                    "type": "anime",
                    "name": "Bones",
                    "url": "https://myanimelist.net/anime/producer/4/Bones"
                }
            ],
            "genres": [
                {
                    "mal_id": 1,
                    "type": "anime",
                    "name": "Action",
                    "url": "https://myanimelist.net/anime/genre/1/Action"
                },
                {
                    "mal_id": 2,
                    "type": "anime",
                    "name": "Adventure",
                    "url": "https://myanimelist.net/anime/genre/2/Adventure"
                }
            ],
            "explicit_genres": [],
            "themes": [
                {
                    "mal_id": 38,
                    "type": "anime",
                    "name": "Military",
                    "url": "https://myanimelist.net/anime/genre/38/Military"
                }
            ],
            "demographics": [
                {
                    "mal_id": 27,
                    "type": "anime",
                    "name": "Shounen",
                    "url": "https://myanimelist.net/anime/genre/27/Shounen"
                }
            ]
        }
    ],
    "pagination": {
        "last_visible_page": 1,
        "has_next_page": False,
        "current_page": 1,
        "items": {
            "count": 2,
            "total": 2,
            "per_page": 25
        }
    }
}

# Invalid anime data for testing validation
INVALID_JIKAN_ANIME = {
    "mal_id": "invalid",  # Should be int
    "title": "",  # Should not be empty
    "score": 15.0,  # Should be 0 <= score <= 10
    "episodes": -5,  # Should be >= 0
    "type": None
}

# Mock ETL job configuration
MOCK_ETL_JOB_CONFIG = {
    "endpoint": "/anime",
    "params": {
        "order_by": "score",
        "sort": "desc",
        "limit": 25,
        "status": "complete"
    },
    "snapshot_type": "top",
    "description": "Top-rated completed anime"
}

# Sample AnimeSnapshot for database testing
SAMPLE_ANIME_SNAPSHOT = {
    "mal_id": 1,
    "url": "https://myanimelist.net/anime/1/Cowboy_Bebop",
    "title": "Cowboy Bebop",
    "title_english": "Cowboy Bebop",
    "title_japanese": "カウボーイビバップ",
    "title_synonyms": [],
    "titles": [{"type": "Default", "title": "Cowboy Bebop"}],
    "type": "TV",
    "source": "Original",
    "episodes": 26,
    "status": "Finished Airing",
    "airing": False,
    "duration": "24 min per ep",
    "rating": "R - 17+ (violence & profanity)",
    "score": 8.75,
    "scored_by": 793823,
    "rank": 28,
    "popularity": 43,
    "members": 1281992,
    "favorites": 63490,
    "approved": True,
    "season": "spring",
    "year": 1998,
    "aired": {
        "from": "1998-04-03T00:00:00+00:00",
        "to": "1999-04-24T00:00:00+00:00"
    },
    "synopsis": "Crime is timeless...",
    "background": "When Cowboy Bebop first aired...",
    "images": {"jpg": {"image_url": "https://example.com/image.jpg"}},
    "trailer": {"youtube_id": "QCaEJZqLeTU"},
    "genres": [{"mal_id": 1, "name": "Action"}],
    "explicit_genres": [],
    "themes": [{"mal_id": 29, "name": "Space"}],
    "demographics": [],
    "studios": [{"mal_id": 14, "name": "Sunrise"}],
    "producers": [{"mal_id": 23, "name": "Bandai Visual"}],
    "licensors": [{"mal_id": 102, "name": "Funimation"}],
    "broadcast": {"day": "Saturdays", "time": "01:15"},
    "snapshot_type": "top",
    "snapshot_date": date.today()
}
