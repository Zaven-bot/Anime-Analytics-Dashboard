"""
Data Transformer
Transforms Jikan API data into database-ready format with validation.
"""

from datetime import date
from typing import Any, Dict, List, Optional

from logging_config import setup_logging
from pydantic import ValidationError

from ..models.jikan import AnimeSnapshot, JikanAnime

logger = setup_logging("etl-transformers-anime")


class DataTransformationError(Exception):
    """Custom exception for data transformation errors"""

    pass


class AnimeTransformer:
    """
    Transforms Jikan API anime data into database-ready snapshots.
    Handles data cleaning, validation, and type conversion.
    """

    def __init__(self):
        self.validation_errors = []
        self.transformation_stats = {
            "total_processed": 0,
            "successful_transforms": 0,
            "validation_errors": 0,
            "dropped_invalid": 0,
        }

    def transform_anime_list(
        self,
        anime_list: List[JikanAnime],
        snapshot_type: str,
        snapshot_date: Optional[date] = None,
    ) -> List[AnimeSnapshot]:
        """
        Transform a list of Jikan anime into database snapshots.

        Args:
            anime_list: List of JikanAnime objects from API
            snapshot_type: Type of snapshot (e.g., 'top', 'seasonal', 'upcoming')
            snapshot_date: Date of the snapshot (defaults to today)

        Returns:
            List of validated AnimeSnapshot objects ready for database insertion
        """
        if snapshot_date is None:
            snapshot_date = date.today()

        transformed_snapshots = []
        self.validation_errors = []

        logger.info(
            "Starting anime transformation",
            total_anime=len(anime_list),
            snapshot_type=snapshot_type,
            snapshot_date=snapshot_date,
        )

        for anime in anime_list:
            self.transformation_stats["total_processed"] += 1

            try:
                snapshot = self._transform_single_anime(anime, snapshot_type, snapshot_date)
                transformed_snapshots.append(snapshot)
                self.transformation_stats["successful_transforms"] += 1

            except ValidationError as e:
                self.validation_errors.append(
                    {
                        "mal_id": getattr(anime, "mal_id", "unknown"),
                        "title": getattr(anime, "title", "unknown"),
                        "error": str(e),
                    }
                )
                self.transformation_stats["validation_errors"] += 1
                logger.warning(
                    "Validation error during transformation",
                    mal_id=anime.mal_id,
                    title=anime.title,
                    error=str(e),
                )

            except Exception as e:
                self.validation_errors.append(
                    {
                        "mal_id": getattr(anime, "mal_id", "unknown"),
                        "title": getattr(anime, "title", "unknown"),
                        "error": f"Transformation error: {str(e)}",
                    }
                )
                self.transformation_stats["dropped_invalid"] += 1
                logger.error(
                    "Unexpected error during transformation",
                    mal_id=anime.mal_id,
                    title=anime.title,
                    error=str(e),
                )

        logger.info(
            "Transformation completed",
            **self.transformation_stats,
            validation_errors_count=len(self.validation_errors),
        )

        return transformed_snapshots

    def _transform_single_anime(self, anime: JikanAnime, snapshot_type: str, snapshot_date: date) -> AnimeSnapshot:
        """
        Transform a single anime object into a database snapshot.
        """
        # Convert complex objects to dictionaries for JSON storage
        titles_dict = None
        if anime.titles:
            titles_dict = [{"type": t.type, "title": t.title} for t in anime.titles]

        aired_dict = None
        if anime.aired:
            aired_dict = {
                "from": anime.aired.from_,
                "to": anime.aired.to,
                "prop": anime.aired.prop.model_dump() if anime.aired.prop else None,
            }

        images_dict = None
        if anime.images:
            images_dict = anime.images.model_dump()

        trailer_dict = None
        if anime.trailer:
            trailer_dict = anime.trailer.model_dump()

        broadcast_dict = None
        if anime.broadcast:
            broadcast_dict = anime.broadcast.model_dump()

        # Convert entity lists to dictionaries
        genres_dict = self._convert_entities_to_dict(anime.genres)
        explicit_genres_dict = self._convert_entities_to_dict(anime.explicit_genres)
        themes_dict = self._convert_entities_to_dict(anime.themes)
        demographics_dict = self._convert_entities_to_dict(anime.demographics)
        studios_dict = self._convert_entities_to_dict(anime.studios)
        producers_dict = self._convert_entities_to_dict(anime.producers)
        licensors_dict = self._convert_entities_to_dict(anime.licensors)

        # Create the snapshot
        snapshot = AnimeSnapshot(
            mal_id=anime.mal_id,
            url=anime.url,
            title=anime.title,
            title_english=anime.title_english,
            title_japanese=anime.title_japanese,
            title_synonyms=anime.title_synonyms,
            titles=titles_dict,
            type=anime.type,
            source=anime.source,
            episodes=anime.episodes,
            status=anime.status,
            airing=anime.airing,
            duration=anime.duration,
            rating=anime.rating,
            score=anime.score,
            scored_by=anime.scored_by,
            rank=anime.rank,
            popularity=anime.popularity,
            members=anime.members,
            favorites=anime.favorites,
            approved=anime.approved,
            season=anime.season,
            year=anime.year,
            aired=aired_dict,
            synopsis=self._clean_text(anime.synopsis),
            background=self._clean_text(anime.background),
            images=images_dict,
            trailer=trailer_dict,
            genres=genres_dict,
            explicit_genres=explicit_genres_dict,
            themes=themes_dict,
            demographics=demographics_dict,
            studios=studios_dict,
            producers=producers_dict,
            licensors=licensors_dict,
            broadcast=broadcast_dict,
            snapshot_type=snapshot_type,
            snapshot_date=snapshot_date,
        )

        return snapshot

    def _convert_entities_to_dict(self, entities: Optional[List]) -> Optional[List[Dict[str, Any]]]:
        """Convert a list of Jikan entities to dictionary format"""
        if not entities:
            return None

        return [
            {
                "mal_id": entity.mal_id,
                "type": entity.type,
                "name": entity.name,
                "url": entity.url,
            }
            for entity in entities
        ]

    def _clean_text(self, text: Optional[str]) -> Optional[str]:
        """Clean and normalize text fields"""
        if not text:
            return None

        # Remove excessive whitespace and normalize
        cleaned = " ".join(text.split())

        # Truncate if too long (database field limits)
        if len(cleaned) > 5000:  # Reasonable limit for synopsis/background
            cleaned = cleaned[:4997] + "..."
            logger.debug(
                "Text truncated due to length",
                original_length=len(text),
                truncated_length=len(cleaned),
            )

        return cleaned

    def get_transformation_summary(self) -> Dict[str, Any]:
        """Get summary of transformation results"""
        return {
            "stats": self.transformation_stats,
            "validation_errors": self.validation_errors,
            "success_rate": (
                self.transformation_stats["successful_transforms"]
                / max(self.transformation_stats["total_processed"], 1)
            )
            * 100,
        }

    def reset_stats(self):
        """Reset transformation statistics"""
        self.transformation_stats = {
            "total_processed": 0,
            "successful_transforms": 0,
            "validation_errors": 0,
            "dropped_invalid": 0,
        }
        self.validation_errors = []


def create_transformer() -> AnimeTransformer:
    """Create a new AnimeTransformer instance"""
    return AnimeTransformer()
