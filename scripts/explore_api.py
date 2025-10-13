"""API exploration script to document BoondManager endpoints and response structures.

This script calls various BoondManager API endpoints and saves the responses
to help create accurate documentation for the project tools.

Usage:
    python scripts/explore_api.py [--endpoint ENDPOINT] [--save]

Examples:
    # Explore all endpoints
    python scripts/explore_api.py --save

    # Explore specific endpoint
    python scripts/explore_api.py --endpoint projects

    # Just view responses (no save)
    python scripts/explore_api.py
"""

import asyncio
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from pprint import pprint

from src.integrations.boond_client import BoondManagerClient


class APIExplorer:
    """Explore and document BoondManager API endpoints."""

    def __init__(self, save_responses: bool = False):
        self.client = BoondManagerClient()
        self.save_responses = save_responses
        self.output_dir = Path("docs/api_responses")

        if save_responses:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def _save_response(self, endpoint_name: str, response: Dict[str, Any]) -> None:
        """Save API response to JSON file."""
        if not self.save_responses:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{endpoint_name}_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(response, f, indent=2, ensure_ascii=False)

        print(f"   💾 Saved response to: {filepath}")

    def _print_response_structure(self, data: Any, indent: int = 0) -> None:
        """Print the structure of the response data."""
        prefix = "  " * indent

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    print(f"{prefix}📦 {key}:")
                    self._print_response_structure(value, indent + 1)
                else:
                    value_type = type(value).__name__
                    value_preview = str(value)[:50] if value else "null"
                    print(f"{prefix}   • {key} ({value_type}): {value_preview}")
        elif isinstance(data, list):
            if data:
                print(f"{prefix}📋 Array with {len(data)} items")
                if len(data) > 0:
                    print(f"{prefix}   Sample item [0]:")
                    self._print_response_structure(data[0], indent + 1)
            else:
                print(f"{prefix}📋 Empty array")

    async def explore_projects_search(
        self,
        keywords: Optional[str] = None,
        limit: int = 3
    ) -> Dict[str, Any]:
        """Explore GET /projects (search) endpoint.

        Args:
            keywords: Optional search keywords
            limit: Number of results to fetch (default: 3)

        Returns:
            API response dictionary
        """
        print("\n" + "="*70)
        print("🔍 Exploring: GET /projects (Search Projects)")
        print("="*70)

        params = {}
        if keywords:
            params["keywords"] = keywords
            print(f"   🔎 Search keywords: {keywords}")

        try:
            response = await self.client.get_projects()

            print(f"\n   ✅ Success! Found {len(response.get('data', []))} projects")

            # Show structure
            print("\n   📊 Response Structure:")
            self._print_response_structure(response)

            # Show sample project
            if response.get("data"):
                print("\n   🎯 Sample Project (first result):")
                sample = response["data"][0]
                print(f"      ID: {sample.get('id')}")
                attrs = sample.get("attributes", {})
                print(f"      Title: {attrs.get('title')}")
                print(f"      Reference: {attrs.get('reference')}")
                print(f"      State: {attrs.get('state', {})}")

            self._save_response("projects_search", response)
            return response

        except Exception as e:
            print(f"\n   ❌ Error: {e}")
            return {"error": str(e)}

    async def explore_project_by_id(self, project_id: int) -> Dict[str, Any]:
        """Explore GET /projects/{id} endpoint.

        Args:
            project_id: Project ID to fetch

        Returns:
            API response dictionary
        """
        print("\n" + "="*70)
        print(f"🔍 Exploring: GET /projects/{project_id} (Project Profile)")
        print("="*70)

        try:
            response = await self.client._make_request(f"projects/{project_id}")

            print(f"\n   ✅ Success! Retrieved project {project_id}")

            # Show structure
            print("\n   📊 Response Structure:")
            self._print_response_structure(response)

            # Show key fields
            data = response.get("data", {})
            attrs = data.get("attributes", {})
            print("\n   🎯 Key Fields:")
            print(f"      ID: {data.get('id')}")
            print(f"      Type: {data.get('type')}")
            print(f"      Title: {attrs.get('title')}")
            print(f"      Reference: {attrs.get('reference')}")
            print(f"      State: {attrs.get('state')}")
            print(f"      Start Date: {attrs.get('startDate')}")
            print(f"      End Date: {attrs.get('endDate')}")

            self._save_response(f"project_{project_id}_profile", response)
            return response

        except Exception as e:
            print(f"\n   ❌ Error: {e}")
            return {"error": str(e)}

    async def explore_project_productivity(self, project_id: int) -> Dict[str, Any]:
        """Explore GET /projects/{id}/productivity endpoint.

        Args:
            project_id: Project ID to fetch productivity data for

        Returns:
            API response dictionary
        """
        print("\n" + "="*70)
        print(f"🔍 Exploring: GET /projects/{project_id}/productivity")
        print("="*70)
        print("   📝 This endpoint provides resource assignments and timesheets")

        try:
            response = await self.client.get_project_productivity(project_id)

            print(f"\n   ✅ Success! Found {len(response.get('data', []))} productivity records")

            # Show structure
            print("\n   📊 Response Structure:")
            self._print_response_structure(response)

            # Show resource details
            if response.get("data"):
                print("\n   👥 Resource Details:")
                for idx, record in enumerate(response["data"][:3], 1):
                    attrs = record.get("attributes", {})
                    resource = attrs.get("resource", {})
                    print(f"\n      Resource {idx}:")
                    print(f"         ID: {resource.get('id')}")
                    print(f"         Name: {resource.get('firstName')} {resource.get('lastName')}")
                    print(f"         Worked Days: {attrs.get('workedDays')}")

                    timesheet = attrs.get('timesReport', {})
                    if timesheet:
                        print(f"         Timesheet ID: {timesheet.get('id')}")

            self._save_response(f"project_{project_id}_productivity", response)
            return response

        except Exception as e:
            print(f"\n   ❌ Error: {e}")
            return {"error": str(e)}

    async def explore_project_information(self, project_id: int) -> Dict[str, Any]:
        """Explore GET /projects/{id}/information endpoint.

        Args:
            project_id: Project ID to fetch information for

        Returns:
            API response dictionary
        """
        print("\n" + "="*70)
        print(f"🔍 Exploring: GET /projects/{project_id}/information")
        print("="*70)

        try:
            response = await self.client._make_request(f"projects/{project_id}/information")

            print(f"\n   ✅ Success! Retrieved detailed information")

            # Show structure
            print("\n   📊 Response Structure:")
            self._print_response_structure(response)

            self._save_response(f"project_{project_id}_information", response)
            return response

        except Exception as e:
            print(f"\n   ❌ Error: {e}")
            return {"error": str(e)}

    async def explore_project_orders(self, project_id: int) -> Dict[str, Any]:
        """Explore GET /projects/{id}/orders endpoint.

        Args:
            project_id: Project ID to fetch orders for

        Returns:
            API response dictionary
        """
        print("\n" + "="*70)
        print(f"🔍 Exploring: GET /projects/{project_id}/orders")
        print("="*70)

        try:
            response = await self.client.get_project_orders(project_id)

            print(f"\n   ✅ Success! Found {len(response.get('data', []))} orders")

            # Show structure
            print("\n   📊 Response Structure:")
            self._print_response_structure(response)

            # Show order details
            if response.get("data"):
                print("\n   📋 Order Details:")
                for idx, order in enumerate(response["data"][:3], 1):
                    attrs = order.get("attributes", {})
                    print(f"\n      Order {idx}:")
                    print(f"         ID: {order.get('id')}")
                    print(f"         Reference: {attrs.get('reference')}")
                    print(f"         State: {attrs.get('state')}")
                    print(f"         Start Date: {attrs.get('startDate')}")
                    print(f"         End Date: {attrs.get('endDate')}")

            self._save_response(f"project_{project_id}_orders", response)
            return response

        except Exception as e:
            print(f"\n   ❌ Error: {e}")
            return {"error": str(e)}

    async def explore_project_tasks(self, project_id: int) -> Dict[str, Any]:
        """Explore GET /projects/{id}/tasks endpoint.

        Args:
            project_id: Project ID to fetch tasks for

        Returns:
            API response dictionary
        """
        print("\n" + "="*70)
        print(f"🔍 Exploring: GET /projects/{project_id}/tasks")
        print("="*70)

        try:
            response = await self.client._make_request(f"projects/{project_id}/tasks")

            print(f"\n   ✅ Success! Found {len(response.get('data', []))} tasks")

            # Show structure
            print("\n   📊 Response Structure:")
            self._print_response_structure(response)

            self._save_response(f"project_{project_id}_tasks", response)
            return response

        except Exception as e:
            print(f"\n   ❌ Error: {e}")
            return {"error": str(e)}

    async def explore_project_rights(self, project_id: int) -> Dict[str, Any]:
        """Explore GET /projects/{id}/rights endpoint.

        Args:
            project_id: Project ID to fetch rights for

        Returns:
            API response dictionary
        """
        print("\n" + "="*70)
        print(f"🔍 Exploring: GET /projects/{project_id}/rights")
        print("="*70)

        try:
            response = await self.client._make_request(f"projects/{project_id}/rights")

            print(f"\n   ✅ Success! Retrieved rights information")

            # Show structure
            print("\n   📊 Response Structure:")
            self._print_response_structure(response)

            self._save_response(f"project_{project_id}_rights", response)
            return response

        except Exception as e:
            print(f"\n   ❌ Error: {e}")
            return {"error": str(e)}

    async def explore_contacts(self) -> Dict[str, Any]:
        """Explore GET /contacts endpoint.

        Returns:
            API response dictionary
        """
        print("\n" + "="*70)
        print("🔍 Exploring: GET /contacts")
        print("="*70)

        try:
            response = await self.client.get_contacts()

            print(f"\n   ✅ Success! Found {len(response.get('data', []))} contacts")

            # Show structure
            print("\n   📊 Response Structure:")
            self._print_response_structure(response)

            # Show sample contact
            if response.get("data"):
                print("\n   👤 Sample Contact:")
                sample = response["data"][0]
                attrs = sample.get("attributes", {})
                print(f"      ID: {sample.get('id')}")
                print(f"      First Name: {attrs.get('firstName')}")
                print(f"      Last Name: {attrs.get('lastName')}")
                print(f"      Email: {attrs.get('email')}")

            self._save_response("contacts", response)
            return response

        except Exception as e:
            print(f"\n   ❌ Error: {e}")
            return {"error": str(e)}

    async def explore_all(self, project_id: Optional[int] = None) -> None:
        """Explore all available endpoints.

        Args:
            project_id: Optional project ID to use for project-specific endpoints.
                       If None, will try to find a project ID from search results.
        """
        print("\n" + "🚀 " + "="*66 + " 🚀")
        print("     BOONDMANAGER API EXPLORATION - COMPREHENSIVE SCAN")
        print("🚀 " + "="*66 + " 🚀\n")

        # 1. Search projects
        projects_response = await self.explore_projects_search()

        # Get a project ID if not provided
        if project_id is None and projects_response.get("data"):
            project_id = int(projects_response["data"][0]["id"])
            print(f"\n   🎯 Using project ID {project_id} for detailed exploration")

        if project_id:
            # 2. Project by ID
            await self.explore_project_by_id(project_id)

            # 3. Project productivity
            await self.explore_project_productivity(project_id)

            # 4. Project information
            await self.explore_project_information(project_id)

            # 5. Project orders
            await self.explore_project_orders(project_id)

            # 6. Project tasks
            await self.explore_project_tasks(project_id)

            # 7. Project rights
            await self.explore_project_rights(project_id)

        # 8. Contacts
        await self.explore_contacts()

        print("\n" + "="*70)
        print("✅ EXPLORATION COMPLETE!")
        print("="*70)

        if self.save_responses:
            print(f"\n📁 All responses saved to: {self.output_dir.absolute()}")
            print("   Use these responses to improve tool documentation!")


async def main():
    """Main entry point for API exploration script."""
    parser = argparse.ArgumentParser(
        description="Explore BoondManager API endpoints and document response structures"
    )
    parser.add_argument(
        "--endpoint",
        choices=["all", "projects", "productivity", "information", "orders", "tasks", "rights", "contacts"],
        default="all",
        help="Specific endpoint to explore (default: all)"
    )
    parser.add_argument(
        "--project-id",
        type=int,
        help="Specific project ID to use for exploration"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save API responses to JSON files in docs/api_responses/"
    )
    parser.add_argument(
        "--keywords",
        type=str,
        help="Keywords to search for when exploring projects"
    )

    args = parser.parse_args()

    explorer = APIExplorer(save_responses=args.save)

    if args.endpoint == "all":
        await explorer.explore_all(project_id=args.project_id)
    elif args.endpoint == "projects":
        await explorer.explore_projects_search(keywords=args.keywords)
    elif args.endpoint == "productivity":
        if not args.project_id:
            print("❌ Error: --project-id required for productivity endpoint")
            return
        await explorer.explore_project_productivity(args.project_id)
    elif args.endpoint == "information":
        if not args.project_id:
            print("❌ Error: --project-id required for information endpoint")
            return
        await explorer.explore_project_information(args.project_id)
    elif args.endpoint == "orders":
        if not args.project_id:
            print("❌ Error: --project-id required for orders endpoint")
            return
        await explorer.explore_project_orders(args.project_id)
    elif args.endpoint == "tasks":
        if not args.project_id:
            print("❌ Error: --project-id required for tasks endpoint")
            return
        await explorer.explore_project_tasks(args.project_id)
    elif args.endpoint == "rights":
        if not args.project_id:
            print("❌ Error: --project-id required for rights endpoint")
            return
        await explorer.explore_project_rights(args.project_id)
    elif args.endpoint == "contacts":
        await explorer.explore_contacts()


if __name__ == "__main__":
    asyncio.run(main())
