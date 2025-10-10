"""Quick API test script to verify BoondManager connection and see responses.

Run with: uv run python test_api.py
"""

import asyncio
import json
from src.integrations.boond_client import BoondManagerClient


async def test_api():
    """Test BoondManager API connection and display responses."""
    client = BoondManagerClient()

    print("=" * 80)
    print("BoondManager API Test")
    print("=" * 80)

    # Test 1: Get projects
    print("\n1. Testing get_projects()...")
    try:
        projects = await client.get_projects()
        print(f"✅ Success! Found {len(projects.get('data', []))} projects")
        print("\nFirst project sample:")
        if projects.get('data'):
            first_project = projects['data'][0]
            print(json.dumps(first_project, indent=2))
        else:
            print("No projects found")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 2: Get contacts
    print("\n" + "=" * 80)
    print("\n2. Testing get_contacts()...")
    try:
        contacts = await client.get_contacts()
        print(f"✅ Success! Found {len(contacts.get('data', []))} contacts")
        print("\nFirst contact sample:")
        if contacts.get('data'):
            first_contact = contacts['data'][0]
            print(json.dumps(first_contact, indent=2))
        else:
            print("No contacts found")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 3: Get deliveries for first project (if exists)
    print("\n" + "=" * 80)
    if projects.get('data'):
        project_id = projects['data'][0].get('id')
        print(f"\n3. Testing get_project_deliveries(project_id={project_id})...")
        try:
            deliveries = await client.get_project_deliveries(int(project_id))
            print(f"✅ Success! Found {len(deliveries.get('data', []))} deliveries")
            print("\nFirst delivery sample:")
            if deliveries.get('data'):
                first_delivery = deliveries['data'][0]
                print(json.dumps(first_delivery, indent=2))
            else:
                print("No deliveries found")
        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n" + "=" * 80)
    print("API Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_api())
