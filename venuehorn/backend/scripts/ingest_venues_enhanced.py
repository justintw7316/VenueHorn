"""
Enhanced venue data ingestion pipeline for VenueHorn.

Features:
- Data validation and cleaning
- Capacity parsing (handles various formats)
- Geocoding with caching
- Price tier estimation
- Amenity extraction
- Duplicate detection
- Progress tracking
- Batch embedding generation
- Comprehensive reporting
"""
import argparse
import csv
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import asdict

# Add parent directory to path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.vector_store import vector_store
from app.data_validator import DataValidator, ValidationReport
from app.geocoder import Geocoder

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/ingestion.log')
    ]
)
logger = logging.getLogger(__name__)


class VenueIngestionPipeline:
    """Enhanced pipeline for ingesting venue data."""

    def __init__(self, enable_geocoding: bool = True, enable_embedding: bool = True):
        self.validator = DataValidator()
        self.geocoder = Geocoder() if enable_geocoding else None
        self.enable_embedding = enable_embedding
        self.stats = {
            'total': 0,
            'valid': 0,
            'geocoded': 0,
            'embedded': 0,
            'skipped': 0,
            'errors': 0
        }

    def read_csv(self, csv_path: Path) -> List[Dict[str, Any]]:
        """Read and parse CSV file."""
        logger.info(f"Reading CSV from: {csv_path}")

        venues = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                venues.append(row)

        logger.info(f"Read {len(venues)} venues from CSV")
        return venues

    def validate_data(self, venues: List[Dict[str, Any]]) -> ValidationReport:
        """Validate all venue data and generate report."""
        logger.info("Validating venue data...")
        report = self.validator.generate_report(venues)

        logger.info(f"Validation complete:")
        logger.info(f"  Total rows: {report.total_rows}")
        logger.info(f"  Valid rows: {report.valid_rows}")
        logger.info(f"  Missing names: {report.missing_name}")
        logger.info(f"  Missing locations: {report.missing_location}")
        logger.info(f"  Missing descriptions: {report.missing_description}")
        logger.info(f"  Potential duplicates: {report.duplicate_names}")

        if report.warnings:
            logger.warning(f"Found {len(report.warnings)} warnings")
            for warning in report.warnings[:10]:  # Show first 10
                logger.warning(f"  {warning}")

        return report

    def process_venue(self, row: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Process a single venue row with cleaning and enrichment."""
        venue_name = row.get('Venue Name', '').strip()

        logger.debug(f"Processing [{index}]: {venue_name}")

        # Clean basic fields
        venue = {
            'name': venue_name,
            'holding_company': row.get('Venue Holding Company', '').strip() or None,
            'brand': row.get('Venue Brand', '').strip() or None,
            'website': self.validator.clean_website(row.get('Venue Website')),
            'description': row.get('Venue Description', '').strip() or None,
            'venue_type': row.get('Venue Type', '').strip() or None,
            'space_name': row.get('Space Name', '').strip() or None,
            'space_description': row.get('Space Description', '').strip() or None,
            'num_spaces': self._parse_int(row.get('Number of Spaces')),
            'email': self.validator.clean_email(row.get('Venue Email')),
            'phone': self.validator.clean_phone(row.get('Venue Phone')),
            'address': row.get('Venue Address', '').strip() or None,
            'city': row.get('Venue City', '').strip() or None,
            'state': row.get('Venue State', '').strip() or None,
            'zip_code': row.get('Venue Zip Code', '').strip() or None,
        }

        # Parse capacity
        capacity_str = row.get('Total Number of Attendees', '')
        capacity_info = self.validator.parse_capacity(capacity_str)
        venue['min_capacity'] = capacity_info.min_capacity
        venue['max_capacity'] = capacity_info.max_capacity
        venue['seated_capacity'] = capacity_info.seated_capacity
        venue['standing_capacity'] = capacity_info.standing_capacity

        # Estimate price tier
        venue['price_tier'] = self.validator.estimate_price_tier(
            venue['venue_type'],
            venue['name'],
            venue['holding_company']
        )

        # Extract amenities
        venue['amenities'] = self.validator.extract_amenities(
            venue['description'] or '',
            venue['space_description'] or ''
        )

        # Geocode
        if self.geocoder and venue['city'] and venue['state']:
            try:
                location = self.geocoder.geocode(
                    venue['address'],
                    venue['city'],
                    venue['state'],
                    venue['zip_code']
                )
                if location:
                    venue['latitude'] = location.latitude
                    venue['longitude'] = location.longitude
                    venue['formatted_address'] = location.formatted_address
                    self.stats['geocoded'] += 1
            except Exception as e:
                logger.warning(f"Geocoding failed for {venue_name}: {e}")

        return venue

    def _parse_int(self, value: Any) -> int | None:
        """Safely parse integer."""
        if not value:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def create_search_documents(self, venues: List[Dict[str, Any]]) -> List[tuple]:
        """
        Create search-optimized documents for vector indexing.
        Each document combines all searchable fields.
        """
        documents = []

        for venue in venues:
            # Build comprehensive search text
            parts = []

            # Basic info
            if venue['name']:
                parts.append(f"Venue: {venue['name']}")

            if venue['venue_type']:
                parts.append(f"Type: {venue['venue_type']}")

            # Location
            if venue['city'] and venue['state']:
                parts.append(f"Location: {venue['city']}, {venue['state']}")

            # Capacity
            if venue['max_capacity']:
                parts.append(f"Capacity: up to {venue['max_capacity']} guests")

            # Price tier
            if venue['price_tier']:
                price_desc = {
                    'budget': 'Budget-friendly',
                    'mid': 'Mid-range pricing',
                    'luxury': 'Luxury venue',
                    'ultra': 'Ultra-luxury venue'
                }
                parts.append(price_desc.get(venue['price_tier'], ''))

            # Amenities
            if venue['amenities']:
                parts.append(f"Amenities: {', '.join(venue['amenities'])}")

            # Description
            if venue['description']:
                parts.append(f"Description: {venue['description']}")

            if venue['space_description']:
                parts.append(f"Space: {venue['space_description']}")

            # Combine into searchable document
            document_text = '\n'.join(parts)

            # Create source identifier
            source = f"{venue['name']}"
            if venue['city'] and venue['state']:
                source += f" - {venue['city']}, {venue['state']}"

            documents.append((document_text, source))

        return documents

    def ingest(self, csv_path: Path, skip_validation: bool = False) -> Dict[str, Any]:
        """
        Run the complete ingestion pipeline.

        Args:
            csv_path: Path to CSV file
            skip_validation: Skip validation step (not recommended)

        Returns:
            Dictionary with ingestion statistics
        """
        logger.info("=" * 60)
        logger.info("VenueHorn Data Ingestion Pipeline")
        logger.info("=" * 60)

        # Step 1: Read CSV
        raw_venues = self.read_csv(csv_path)
        self.stats['total'] = len(raw_venues)

        # Step 2: Validate data
        if not skip_validation:
            validation_report = self.validate_data(raw_venues)
        else:
            logger.warning("Skipping validation (not recommended)")

        # Step 3: Process each venue
        logger.info("Processing and enriching venue data...")
        processed_venues = []

        for idx, row in enumerate(raw_venues, start=1):
            # Validate row
            is_valid, warnings = self.validator.validate_row(row)

            if not is_valid:
                logger.warning(f"Skipping invalid venue at row {idx}")
                self.stats['skipped'] += 1
                continue

            try:
                venue = self.process_venue(row, idx)
                processed_venues.append(venue)
                self.stats['valid'] += 1

                # Progress indicator
                if idx % 10 == 0:
                    logger.info(f"Processed {idx}/{len(raw_venues)} venues...")

            except Exception as e:
                logger.error(f"Error processing row {idx}: {e}")
                self.stats['errors'] += 1

        logger.info(f"Processed {len(processed_venues)} venues successfully")

        # Step 4: Create search documents
        logger.info("Creating search documents...")
        documents = self.create_search_documents(processed_venues)

        # Step 5: Generate embeddings and index
        if self.enable_embedding:
            logger.info("Generating embeddings and indexing...")
            chunks_added = vector_store.add_documents(documents)
            self.stats['embedded'] = chunks_added
            logger.info(f"Added {chunks_added} chunks to vector index")
        else:
            logger.warning("Embedding generation disabled")

        # Step 6: Generate final report
        logger.info("=" * 60)
        logger.info("Ingestion Complete!")
        logger.info("=" * 60)
        logger.info(f"Total venues in CSV: {self.stats['total']}")
        logger.info(f"Successfully processed: {self.stats['valid']}")
        logger.info(f"Geocoded: {self.stats['geocoded']}")
        logger.info(f"Indexed chunks: {self.stats['embedded']}")
        logger.info(f"Skipped (invalid): {self.stats['skipped']}")
        logger.info(f"Errors: {self.stats['errors']}")

        if self.geocoder:
            geo_stats = self.geocoder.get_stats()
            logger.info(f"Geocoding stats: {geo_stats}")

        # Save processed venues to JSON for inspection
        import json
        output_path = Path('data/processed_venues.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_venues, f, indent=2, default=str)
        logger.info(f"Saved processed venues to: {output_path}")

        return self.stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Enhanced venue data ingestion for VenueHorn"
    )
    parser.add_argument(
        'csv_path',
        type=Path,
        help='Path to the venues CSV file'
    )
    parser.add_argument(
        '--no-geocoding',
        action='store_true',
        help='Disable geocoding (faster but no location data)'
    )
    parser.add_argument(
        '--no-embedding',
        action='store_true',
        help='Disable embedding generation (for testing)'
    )
    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='Skip validation step (not recommended)'
    )

    args = parser.parse_args()

    # Validate CSV exists
    if not args.csv_path.exists():
        logger.error(f"CSV file not found: {args.csv_path}")
        sys.exit(1)

    # Create pipeline
    pipeline = VenueIngestionPipeline(
        enable_geocoding=not args.no_geocoding,
        enable_embedding=not args.no_embedding
    )

    # Run ingestion
    try:
        stats = pipeline.ingest(args.csv_path, skip_validation=args.skip_validation)

        # Exit code based on results
        if stats['errors'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        logger.exception(f"Fatal error during ingestion: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
