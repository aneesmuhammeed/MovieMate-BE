from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MediaType(str, Enum):
    MOVIE = "movie"
    TV = "tv"


class WatchStatus(str, Enum):
    NOT_STARTED = "not_started"
    WATCHING = "watching"
    COMPLETED = "completed"


class MovieShow(Base):
    __tablename__ = "movie_shows"
    __table_args__ = (
        UniqueConstraint("tmdb_id", "media_type", name="uq_tmdb_media_type"),
        Index("ix_movie_shows_title", "title"),
        Index("ix_movie_shows_genre", "genre"),
        Index("ix_movie_shows_platform", "platform"),
        Index("ix_movie_shows_date_added", "date_added"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tmdb_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    media_type: Mapped[MediaType] = mapped_column(SQLEnum(MediaType), nullable=False, index=True)
    genre: Mapped[str] = mapped_column(String(120), nullable=False)
    platform: Mapped[str] = mapped_column(String(120), nullable=False)
    date_added: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    progress: Mapped["Progress"] = relationship(
        "Progress",
        back_populates="item",
        uselist=False,
        cascade="all, delete-orphan",
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review",
        back_populates="item",
        cascade="all, delete-orphan",
    )


class Progress(Base):
    __tablename__ = "progress"
    __table_args__ = (
        Index("ix_progress_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("movie_shows.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    total_episodes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    watched_episodes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[WatchStatus] = mapped_column(SQLEnum(WatchStatus), nullable=False, default=WatchStatus.NOT_STARTED)

    item: Mapped[MovieShow] = relationship("MovieShow", back_populates="progress")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        Index("ix_reviews_item_id", "item_id"),
        Index("ix_reviews_rating", "rating"),
        Index("ix_reviews_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("movie_shows.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    item: Mapped[MovieShow] = relationship("MovieShow", back_populates="reviews")