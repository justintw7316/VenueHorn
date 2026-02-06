"""
Simple test script to verify the VenueHorn API is working correctly.
Run this after starting the server with: uvicorn app.main:app --reload
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """Test the health endpoint"""
    print("Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
    return response.status_code == 200


def test_ingest():
    """Test ingesting sample venue data"""
    print("Testing /ingest endpoint...")
    sample_data = {
        "documents": [
            {
                "text": "The Grand Ballroom is a luxurious wedding venue in Miami, Florida. "
                       "It can accommodate up to 300 guests and features elegant chandeliers, "
                       "a spacious dance floor, and stunning ocean views. Perfect for weddings "
                       "and corporate events. Contact: info@grandballroom.com",
                "source": "Grand Ballroom - Miami, FL"
            },
            {
                "text": "Rustic Barn Venue in Nashville, Tennessee. A charming countryside venue "
                       "with exposed wooden beams and string lights. Capacity: 150 guests. "
                       "Ideal for intimate weddings and rehearsal dinners. Includes catering kitchen.",
                "source": "Rustic Barn - Nashville, TN"
            }
        ]
    }

    response = requests.post(f"{BASE_URL}/ingest", json=sample_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
    return response.status_code == 200


def test_search():
    """Test the search endpoint"""
    print("Testing /search endpoint...")
    search_query = {
        "query": "wedding venue with ocean views",
        "k": 3
    }

    response = requests.post(f"{BASE_URL}/search", json=search_query)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    return response.status_code == 200


def test_chat():
    """Test the chat endpoint"""
    print("Testing /chat endpoint...")
    chat_query = {
        "query": "I'm looking for a romantic venue for my wedding with about 200 guests",
        "k": 3
    }

    response = requests.post(f"{BASE_URL}/chat", json=chat_query)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"AI Response: {result.get('answer')}\n")
    print(f"Retrieved {len(result.get('hits', []))} venue matches\n")
    return response.status_code == 200


if __name__ == "__main__":
    print("=" * 60)
    print("VenueHorn API Test Suite")
    print("=" * 60)
    print("Make sure the server is running on http://localhost:8000\n")

    tests = [
        ("Health Check", test_health),
        ("Ingest Data", test_ingest),
        ("Search", test_search),
        ("Chat", test_chat),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, "PASSED" if passed else "FAILED"))
        except Exception as e:
            print(f"ERROR: {e}\n")
            results.append((test_name, "ERROR"))

    print("=" * 60)
    print("Test Results:")
    print("=" * 60)
    for test_name, result in results:
        print(f"{test_name}: {result}")
