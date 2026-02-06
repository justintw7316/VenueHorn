"""
Data validation and cleaning utilities for VenueHorn.
Handles capacity parsing, price estimation, and data quality checks.
"""
import re
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CapacityInfo:
    """Parsed capacity information."""
    min_capacity: Optional[int] = None
    max_capacity: Optional[int] = None
    seated_capacity: Optional[int] = None
    standing_capacity: Optional[int] = None
    raw_value: Optional[str] = None


@dataclass
class ValidationReport:
    """Data validation report."""
    total_rows: int = 0
    valid_rows: int = 0
    missing_name: int = 0
    missing_location: int = 0
    missing_description: int = 0
    invalid_capacity: int = 0
    duplicate_names: int = 0
    warnings: list = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class DataValidator:
    """Validates and cleans venue data."""

    # Price tier estimation based on venue type
    PRICE_TIERS = {
        'budget': ['church', 'school', 'community', 'park'],
        'mid': ['restaurant', 'brewery', 'bar', 'club'],
        'luxury': ['hotel', 'resort', 'country club', 'estate'],
        'ultra': ['ritz', 'four seasons', 'st. regis', 'waldorf']
    }

    @staticmethod
    def parse_capacity(capacity_str: str) -> CapacityInfo:
        """
        Parse capacity from various formats:
        - "Up to 120"
        - "Max Seated: 175Max Standing: 100"
        - "200 guests"
        - "150-200"
        """
        if not capacity_str or not isinstance(capacity_str, str):
            return CapacityInfo()

        capacity_str = capacity_str.strip()
        info = CapacityInfo(raw_value=capacity_str)

        # Pattern: "Max Seated: 175Max Standing: 100"
        seated_match = re.search(r'(?:max\s+)?seated[:\s]+(\d+)', capacity_str, re.IGNORECASE)
        standing_match = re.search(r'(?:max\s+)?standing[:\s]+(\d+)', capacity_str, re.IGNORECASE)

        if seated_match:
            info.seated_capacity = int(seated_match.group(1))
        if standing_match:
            info.standing_capacity = int(standing_match.group(1))

        # If we have both, max is the standing capacity
        if info.seated_capacity and info.standing_capacity:
            info.min_capacity = info.seated_capacity
            info.max_capacity = info.standing_capacity
            return info

        # Pattern: "Up to 120" or "up to 200 guests"
        up_to_match = re.search(r'up\s+to\s+(\d+)', capacity_str, re.IGNORECASE)
        if up_to_match:
            info.max_capacity = int(up_to_match.group(1))
            info.min_capacity = max(10, info.max_capacity // 2)
            return info

        # Pattern: "150-200"
        range_match = re.search(r'(\d+)\s*[-–]\s*(\d+)', capacity_str)
        if range_match:
            info.min_capacity = int(range_match.group(1))
            info.max_capacity = int(range_match.group(2))
            return info

        # Pattern: just a number "200" or "200 guests"
        number_match = re.search(r'(\d+)', capacity_str)
        if number_match:
            capacity = int(number_match.group(1))
            info.max_capacity = capacity
            info.min_capacity = max(10, capacity // 2)
            return info

        return info

    @staticmethod
    def estimate_price_tier(
        venue_type: Optional[str],
        venue_name: Optional[str],
        holding_company: Optional[str]
    ) -> str:
        """
        Estimate price tier based on venue type and name.
        Returns: 'budget', 'mid', 'luxury', or 'ultra'
        """
        # Combine all text for analysis
        text = ' '.join([
            venue_type or '',
            venue_name or '',
            holding_company or ''
        ]).lower()

        # Check for ultra-luxury indicators
        for keyword in DataValidator.PRICE_TIERS['ultra']:
            if keyword in text:
                return 'ultra'

        # Check for luxury indicators
        for keyword in DataValidator.PRICE_TIERS['luxury']:
            if keyword in text:
                return 'luxury'

        # Check for budget indicators
        for keyword in DataValidator.PRICE_TIERS['budget']:
            if keyword in text:
                return 'budget'

        # Default to mid-tier
        return 'mid'

    @staticmethod
    def clean_phone(phone: Optional[str]) -> Optional[str]:
        """Clean and format phone number."""
        if not phone:
            return None

        # Remove all non-numeric characters
        digits = re.sub(r'\D', '', phone)

        # Format as (XXX) XXX-XXXX if 10 digits
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"

        # Return original if can't parse
        return phone

    @staticmethod
    def clean_email(email: Optional[str]) -> Optional[str]:
        """Validate and clean email."""
        if not email:
            return None

        email = email.strip().lower()

        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, email):
            return email

        return None

    @staticmethod
    def clean_website(website: Optional[str]) -> Optional[str]:
        """Clean and validate website URL."""
        if not website:
            return None

        website = website.strip()

        # Add https:// if missing
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website

        # Basic URL validation
        url_pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        if re.match(url_pattern, website):
            return website

        return None

    @staticmethod
    def extract_amenities(description: str, space_description: str = '') -> list[str]:
        """Extract amenities from text descriptions."""
        text = (description + ' ' + space_description).lower()
        amenities = []

        # Common amenity keywords
        amenity_keywords = {
            'parking': ['parking', 'valet', 'garage'],
            'catering': ['catering', 'food service', 'kitchen'],
            'bar': ['bar', 'cocktail', 'drinks'],
            'outdoor': ['outdoor', 'patio', 'garden', 'terrace'],
            'pool': ['pool', 'swimming'],
            'wifi': ['wifi', 'wi-fi', 'internet'],
            'av_equipment': ['projector', 'screen', 'audio', 'video', 'av equipment'],
            'dance_floor': ['dance floor', 'dancing'],
            'stage': ['stage', 'performance'],
            'accommodation': ['hotel', 'rooms', 'overnight', 'lodging'],
            'accessible': ['wheelchair', 'accessible', 'ada'],
            'beach_access': ['beach', 'waterfront', 'ocean view'],
        }

        for amenity, keywords in amenity_keywords.items():
            if any(keyword in text for keyword in keywords):
                amenities.append(amenity)

        return amenities

    @staticmethod
    def validate_row(row: Dict[str, Any]) -> Tuple[bool, list[str]]:
        """
        Validate a single venue row.
        Returns: (is_valid, list_of_warnings)
        """
        warnings = []

        # Required fields
        if not row.get('Venue Name') or not row['Venue Name'].strip():
            warnings.append("Missing venue name")
            return False, warnings

        if not row.get('Venue City') or not row.get('Venue State'):
            warnings.append(f"Missing location for {row.get('Venue Name')}")

        if not row.get('Venue Description') or not row['Venue Description'].strip():
            warnings.append(f"Missing description for {row.get('Venue Name')}")

        if not row.get('Venue Type') or not row['Venue Type'].strip():
            warnings.append(f"Missing venue type for {row.get('Venue Name')}")

        # Validate email if present
        email = row.get('Venue Email')
        if email and not DataValidator.clean_email(email):
            warnings.append(f"Invalid email for {row.get('Venue Name')}: {email}")

        # Validate website if present
        website = row.get('Venue Website')
        if website and not DataValidator.clean_website(website):
            warnings.append(f"Invalid website for {row.get('Venue Name')}: {website}")

        return len(warnings) == 0 or all('Missing' not in w for w in warnings if 'name' not in w.lower()), warnings

    @staticmethod
    def detect_duplicates(venues: list[Dict[str, Any]]) -> list[Tuple[int, int, float]]:
        """
        Detect potential duplicate venues.
        Returns: list of (index1, index2, similarity_score)
        """
        duplicates = []

        for i, venue1 in enumerate(venues):
            for j, venue2 in enumerate(venues[i + 1:], start=i + 1):
                # Check if same name and city
                name1 = (venue1.get('Venue Name') or '').lower().strip()
                name2 = (venue2.get('Venue Name') or '').lower().strip()
                city1 = (venue1.get('Venue City') or '').lower().strip()
                city2 = (venue2.get('Venue City') or '').lower().strip()

                if name1 == name2 and city1 == city2:
                    duplicates.append((i, j, 1.0))
                elif name1 and name2 and DataValidator._string_similarity(name1, name2) > 0.85:
                    if city1 == city2:
                        duplicates.append((i, j, 0.85))

        return duplicates

    @staticmethod
    def _string_similarity(s1: str, s2: str) -> float:
        """Calculate simple string similarity (Jaccard)."""
        if not s1 or not s2:
            return 0.0

        set1 = set(s1.split())
        set2 = set(s2.split())

        intersection = set1.intersection(set2)
        union = set1.union(set2)

        return len(intersection) / len(union) if union else 0.0

    @staticmethod
    def generate_report(venues: list[Dict[str, Any]]) -> ValidationReport:
        """Generate a comprehensive validation report."""
        report = ValidationReport(total_rows=len(venues))

        for venue in venues:
            is_valid, warnings = DataValidator.validate_row(venue)

            if is_valid:
                report.valid_rows += 1

            report.warnings.extend(warnings)

            # Count specific issues
            if not venue.get('Venue Name'):
                report.missing_name += 1
            if not venue.get('Venue City') or not venue.get('Venue State'):
                report.missing_location += 1
            if not venue.get('Venue Description'):
                report.missing_description += 1

        # Detect duplicates
        duplicates = DataValidator.detect_duplicates(venues)
        report.duplicate_names = len(duplicates)

        if duplicates:
            for i, j, score in duplicates[:5]:  # Show first 5
                report.warnings.append(
                    f"Possible duplicate: {venues[i].get('Venue Name')} "
                    f"(rows {i+2} and {j+2}, similarity: {score:.2f})"
                )

        return report
