"""
Quick test script for the enhanced ingestion pipeline.
Tests data validation, capacity parsing, and geocoding without full ingestion.
"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.data_validator import DataValidator, CapacityInfo


def test_capacity_parsing():
    """Test various capacity string formats."""
    print("=" * 60)
    print("Testing Capacity Parsing")
    print("=" * 60)

    test_cases = [
        "Up to 120",
        "Max Seated: 175Max Standing: 100",
        "200 guests",
        "150-200",
        "500",
        "50 to 75 people",
        "",
        None,
    ]

    validator = DataValidator()

    for test_str in test_cases:
        result = validator.parse_capacity(test_str)
        print(f"\nInput: {test_str!r}")
        print(f"  Min: {result.min_capacity}")
        print(f"  Max: {result.max_capacity}")
        if result.seated_capacity:
            print(f"  Seated: {result.seated_capacity}")
        if result.standing_capacity:
            print(f"  Standing: {result.standing_capacity}")


def test_price_estimation():
    """Test price tier estimation."""
    print("\n" + "=" * 60)
    print("Testing Price Tier Estimation")
    print("=" * 60)

    test_cases = [
        ("Hotel", "Ritz-Carlton Miami", "Marriott", "ultra"),
        ("Hotel", "Holiday Inn", None, "luxury"),
        ("Restaurant", "Joe's Diner", None, "mid"),
        ("Church", "St. Mary's Chapel", None, "budget"),
        ("Brewery", "Local Craft Beer Co", None, "mid"),
        ("Resort", "Four Seasons", "Four Seasons Hotels", "ultra"),
    ]

    validator = DataValidator()

    for venue_type, name, company, expected in test_cases:
        result = validator.estimate_price_tier(venue_type, name, company)
        status = "✅" if result == expected else f"❌ (expected {expected})"
        print(f"\n{status} {name}")
        print(f"  Type: {venue_type}, Result: {result}")


def test_amenity_extraction():
    """Test amenity extraction from descriptions."""
    print("\n" + "=" * 60)
    print("Testing Amenity Extraction")
    print("=" * 60)

    test_descriptions = [
        (
            "Beautiful beachfront resort with ocean views, outdoor pool, and free parking. "
            "Full catering available. WiFi throughout. Wheelchair accessible.",
            ["parking", "catering", "outdoor", "pool", "wifi", "accessible", "beach_access"]
        ),
        (
            "Modern event space with professional AV equipment, stage for performances, "
            "and spacious dance floor. Full bar service available.",
            ["av_equipment", "stage", "dance_floor", "bar"]
        ),
    ]

    validator = DataValidator()

    for description, expected_amenities in test_descriptions:
        result = validator.extract_amenities(description)
        print(f"\nDescription: {description[:80]}...")
        print(f"Found amenities: {result}")
        print(f"Expected: {expected_amenities}")

        # Check if we found all expected
        found_all = all(a in result for a in expected_amenities)
        status = "✅" if found_all else "⚠️"
        print(f"{status} Match: {found_all}")


def test_data_cleaning():
    """Test phone, email, and website cleaning."""
    print("\n" + "=" * 60)
    print("Testing Data Cleaning")
    print("=" * 60)

    validator = DataValidator()

    # Test phone cleaning
    print("\nPhone Numbers:")
    phones = ["(305) 555-1234", "305-555-1234", "3055551234", "1-305-555-1234", "invalid"]
    for phone in phones:
        cleaned = validator.clean_phone(phone)
        print(f"  {phone:20} → {cleaned}")

    # Test email cleaning
    print("\nEmails:")
    emails = ["INFO@VENUE.COM", "  info@venue.com  ", "invalid-email", "user@domain"]
    for email in emails:
        cleaned = validator.clean_email(email)
        print(f"  {email:30} → {cleaned}")

    # Test website cleaning
    print("\nWebsites:")
    websites = ["venue.com", "http://venue.com", "https://venue.com", "invalid"]
    for website in websites:
        cleaned = validator.clean_website(website)
        print(f"  {website:25} → {cleaned}")


def test_row_validation():
    """Test venue row validation."""
    print("\n" + "=" * 60)
    print("Testing Row Validation")
    print("=" * 60)

    validator = DataValidator()

    test_rows = [
        {
            "Venue Name": "Ocean Pearl Resort",
            "Venue City": "Miami",
            "Venue State": "Florida",
            "Venue Description": "Beautiful beachfront resort",
            "Venue Type": "Hotel",
            "Venue Email": "info@oceanpearl.com",
            "Venue Website": "https://oceanpearl.com"
        },
        {
            "Venue Name": "",  # Missing name - should fail
            "Venue City": "Miami",
            "Venue State": "Florida",
        },
        {
            "Venue Name": "Test Venue",
            "Venue City": "",  # Missing location - warning but passes
            "Venue State": "",
            "Venue Description": "Test description"
        }
    ]

    for idx, row in enumerate(test_rows, 1):
        is_valid, warnings = validator.validate_row(row)
        status = "✅ VALID" if is_valid else "❌ INVALID"
        print(f"\nTest {idx}: {status}")
        print(f"  Name: {row.get('Venue Name') or '(missing)'}")
        if warnings:
            for warning in warnings:
                print(f"  ⚠️  {warning}")


def main():
    """Run all tests."""
    try:
        test_capacity_parsing()
        test_price_estimation()
        test_amenity_extraction()
        test_data_cleaning()
        test_row_validation()

        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
