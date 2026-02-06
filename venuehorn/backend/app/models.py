"""
SQLAlchemy models for VenueHorn database.
Future enhancement: Replace FAISS with PostgreSQL + pgvector
"""
from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    Text,
    DECIMAL,
    TIMESTAMP,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Venue(Base):
    """Main venue model with structured data."""

    __tablename__ = "venues"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Basic Info
    name = Column(String(255), nullable=False)
    holding_company = Column(String(255))
    brand = Column(String(255))
    website = Column(String(500))

    # Contact
    email = Column(String(255))
    phone = Column(String(50))

    # Location
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    # location = Column(Geography("POINT", srid=4326))  # For PostGIS

    # Capacity & Pricing
    min_capacity = Column(Integer)
    max_capacity = Column(Integer)
    num_spaces = Column(Integer, default=1)
    base_price = Column(DECIMAL(10, 2))
    price_tier = Column(String(20))  # 'budget', 'mid', 'luxury', 'ultra'

    # Venue Details
    venue_type = Column(String(50))
    venue_category = Column(String(50))  # 'indoor', 'outdoor', 'hybrid'

    # Features
    has_catering = Column(Boolean, default=False)
    has_parking = Column(Boolean, default=False)
    has_accommodation = Column(Boolean, default=False)
    is_accessible = Column(Boolean, default=False)
    allows_outside_vendors = Column(Boolean, default=False)

    # Availability
    available = Column(Boolean, default=True)
    blackout_dates = Column(JSONB)  # Array of date ranges

    # Description & Embedding (for vector search)
    description = Column(Text)
    # description_embedding = Column(Vector(1536))  # For pgvector

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    reviews = relationship("Review", back_populates="venue")

    # Constraints
    __table_args__ = (
        UniqueConstraint("name", "city", "state", name="uq_venue_location"),
    )

    def __repr__(self):
        return f"<Venue(id={self.id}, name='{self.name}', city='{self.city}')>"


class EventType(Base):
    """Event types (wedding, corporate, etc.)."""

    __tablename__ = "event_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)

    def __repr__(self):
        return f"<EventType(name='{self.name}')>"


class Amenity(Base):
    """Venue amenities (pool, dance floor, etc.)."""

    __tablename__ = "amenities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50))  # 'facility', 'service', 'feature'

    def __repr__(self):
        return f"<Amenity(name='{self.name}', category='{self.category}')>"


class Review(Base):
    """Venue reviews and ratings."""

    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    venue_id = Column(Integer, ForeignKey("venues.id", ondelete="CASCADE"))
    rating = Column(DECIMAL(3, 2))  # 0.00 to 5.00
    review_text = Column(Text)
    event_type = Column(String(50))
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationship
    venue = relationship("Venue", back_populates="reviews")

    def __repr__(self):
        return f"<Review(venue_id={self.venue_id}, rating={self.rating})>"


# Future: Add many-to-many relationships for event types and amenities
# class VenueEventType(Base):
#     __tablename__ = "venue_event_types"
#     venue_id = Column(Integer, ForeignKey("venues.id"), primary_key=True)
#     event_type_id = Column(Integer, ForeignKey("event_types.id"), primary_key=True)

# class VenueAmenity(Base):
#     __tablename__ = "venue_amenities"
#     venue_id = Column(Integer, ForeignKey("venues.id"), primary_key=True)
#     amenity_id = Column(Integer, ForeignKey("amenities.id"), primary_key=True)
