#!/usr/bin/env python3
"""
Test Local Function - Simulates a Google Form submission to the local Azure Function

This script:
1. Loads a random attendee from mocks/attendees.json
2. Gets their event assignments from mocks/event_attendees.json
3. Formats the payload like a Google Form webhook would
4. POSTs to the local Azure Function
5. Displays the response

Usage:
    python scripts/test_local_function.py
    python scripts/test_local_function.py --attendee user_001
    python scripts/test_local_function.py --email frankievcleary@gmail.com
"""
import argparse
import json
import random
import sys
from pathlib import Path
import requests


# Configuration
LOCAL_FUNCTION_URL = "http://localhost:7072/api/process-badge"
DEFAULT_EVENT_ID = "cohatch_afterhours"


def load_attendees():
    """Load all attendees from mocks"""
    mocks_path = Path(__file__).parent.parent / "mocks" / "attendees.json"
    with open(mocks_path, 'r') as f:
        return json.load(f)


def load_event_attendees():
    """Load event-attendee mappings from mocks"""
    mocks_path = Path(__file__).parent.parent / "mocks" / "event_attendees.json"
    with open(mocks_path, 'r') as f:
        return json.load(f)


def get_attendee_tags(user_id: str, event_id: str, event_attendees: dict) -> dict:
    """Get tags for a specific attendee in an event"""
    event_list = event_attendees.get(event_id, [])
    for ea in event_list:
        if ea.get('user_id') == user_id:
            return ea.get('tags', {})
    return {}


def build_payload(attendee: dict, event_id: str, tags: dict, override_email: str = None, force_regenerate: bool = True) -> dict:
    """
    Build the payload in the format expected by the Azure Function
    (matching Google Form webhook format)
    """
    # Parse interests into comma-separated string if it's a list
    interests = attendee.get('interests', [])
    if isinstance(interests, list):
        interests_str = ', '.join(interests)
    else:
        interests_str = interests or attendee.get('raw_interests', '')

    payload = {
        "event_id": event_id,
        "name": attendee.get('name', ''),
        "email": override_email or attendee.get('email', 'test@example.com'),
        "title": attendee.get('title', ''),
        "company": attendee.get('company', ''),
        "location": attendee.get('location', ''),
        "interests": interests_str,
        "profile_url": attendee.get('profile_url', ''),
        "preferred_social_platform": attendee.get('preferred_social_platform', ''),
        "social_handle": attendee.get('social_handle', ''),
        "pronouns": attendee.get('pronouns', ''),
        "tags": tags,
        "force_regenerate": force_regenerate
    }

    return payload


def send_to_function(payload: dict) -> dict:
    """Send payload to local Azure Function"""
    print(f"\n{'='*60}")
    print(f"Sending to: {LOCAL_FUNCTION_URL}")
    print(f"{'='*60}")
    print(f"\nPayload:")
    print(json.dumps(payload, indent=2))
    print(f"\n{'='*60}")

    try:
        print(f"\n⏳ Sending request (timeout: 5 minutes)...")
        response = requests.post(
            LOCAL_FUNCTION_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5 minute timeout for image generation
        )

        print(f"\nResponse Status: {response.status_code}")

        if response.status_code == 200:
            print(f"Response Body:")
            try:
                result = response.json()
                print(json.dumps(result, indent=2))
                return result
            except json.JSONDecodeError:
                print(response.text)
                return {"status": "success", "message": response.text}
        else:
            print(f"Error Response:")
            try:
                error_body = response.json()
                print(json.dumps(error_body, indent=2))
                if 'details' in error_body and error_body['details']:
                    print(f"\n💡 Error Details:")
                    print(f"   {error_body['details']}")
                return error_body
            except:
                print(response.text)
                return {"status": "error", "code": response.status_code, "message": response.text}

    except requests.exceptions.Timeout:
        print(f"\n⚠️ Request timed out after 5 minutes")
        print(f"\nPossible causes:")
        print(f"  • AI image generation took too long (>2 min is unusual)")
        print(f"  • Azure OpenAI API is slow or unresponsive")
        print(f"  • Network connectivity issues")
        print(f"\n💡 Check the function terminal logs for more details")
        return {"status": "error", "message": "Request timed out"}
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection Error: Could not connect to {LOCAL_FUNCTION_URL}")
        print(f"Make sure the Azure Function is running:")
        print(f"  1. Press F5 with 'Azure Functions: Attach' selected")
        print(f"  2. Or run: cd function_app && func start --port 7072")
        return {"status": "error", "message": "Connection refused"}

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
        return {"status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Test local Azure Function with mock attendee data")
    parser.add_argument('--attendee', '-a', type=str, help='Specific attendee ID (e.g., user_001)')
    parser.add_argument('--email', '-e', type=str, help='Override email address for badge delivery')
    parser.add_argument('--event', type=str, default=DEFAULT_EVENT_ID, help='Event ID (default: cohatch_afterhours)')
    parser.add_argument('--no-force', action='store_true', help='Skip image regeneration if exists')

    args = parser.parse_args()

    print(f"\n🚀 Local Azure Function Test")
    print(f"{'='*60}")

    # Load data
    attendees = load_attendees()
    event_attendees = load_event_attendees()

    # Select attendee
    if args.attendee:
        # Find specific attendee
        attendee = next((a for a in attendees if a.get('id') == args.attendee), None)
        if not attendee:
            print(f"❌ Attendee '{args.attendee}' not found")
            print(f"Available attendees: {[a['id'] for a in attendees[:10]]}...")
            sys.exit(1)
    else:
        # Filter to attendees in the target event (event_attendees is keyed by event_id)
        event_list = event_attendees.get(args.event, [])
        event_user_ids = [ea['user_id'] for ea in event_list]
        event_attendee_list = [a for a in attendees if a.get('id') in event_user_ids]

        if not event_attendee_list:
            print(f"❌ No attendees found for event '{args.event}'")
            sys.exit(1)

        # Pick random attendee from event
        attendee = random.choice(event_attendee_list)

    print(f"\n📋 Selected Attendee:")
    print(f"   ID: {attendee.get('id')}")
    print(f"   Name: {attendee.get('name')}")
    print(f"   Title: {attendee.get('title')}")
    print(f"   Company: {attendee.get('company')}")
    print(f"   Location: {attendee.get('location')}")

    # Get tags for this attendee in the event
    tags = get_attendee_tags(attendee.get('id'), args.event, event_attendees)
    if tags:
        print(f"\n🏷️  Tags:")
        for key, value in tags.items():
            print(f"   {key}: {value}")

    # Build payload
    payload = build_payload(
        attendee=attendee,
        event_id=args.event,
        tags=tags,
        override_email=args.email,
        force_regenerate=not args.no_force
    )

    # Override email for testing
    if args.email:
        print(f"\n📧 Email Override: {args.email}")

    # Send to function
    result = send_to_function(payload)

    # Summary
    print(f"\n{'='*60}")
    if result.get('status') == 'error':
        print(f"❌ Test FAILED")
    else:
        print(f"✅ Test COMPLETED")
        print(f"\n📧 Badge should be sent to: {payload.get('email')}")
        print(f"Check your inbox!")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
