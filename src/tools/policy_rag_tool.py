"""
Policy RAG Tool - Retrieves relevant policy documentation for orchestrator guidance.

This tool enables the main orchestrator to search through organizational policies,
process documentation, and best practices to make informed delegation decisions.
"""

from langchain.tools import tool
from langchain_core.vectorstores import InMemoryVectorStore


def create_policy_retrieval_tool(vectorstore: InMemoryVectorStore):
    """Create a policy retrieval tool bound to a specific vectorstore.

    Args:
        vectorstore: InMemoryVectorStore instance with indexed policy documents

    Returns:
        Configured policy retrieval tool ready to use
    """

    @tool(response_format="content_and_artifact")
    def retrieve_policy(query: str, top_k: int = 10):
        """Retrieve relevant policy documentation and process guidelines.

        Use this tool to look up:
        - Standard operating procedures for common workflows
        - Best practices for task delegation
        - Error handling protocols
        - Validation processes
        - Email communication guidelines
        - Data query patterns

        This helps you make informed decisions about:
        - How to structure delegations
        - What information to include in prompts
        - How to handle errors and edge cases
        - When to escalate to humans
        - Standard workflow patterns to follow

        Args:
            query: Natural language query describing what policy/process you need guidance on.
                   Examples:
                   - "How should I handle timesheet validation discrepancies?"
                   - "What's the standard process for emailing workers?"
                   - "Best practices for delegating to query agent"
                   - "How to handle API errors?"
            top_k: Number of relevant policy sections to retrieve (min: 2, max: 10)

        Returns:
            Tuple of (serialized policy content, raw Document objects)
            The content includes relevant excerpts from policy documents with source metadata.
        """
        top_k = max(top_k, 2)
        top_k = min(top_k, 10)

        # Perform similarity search
        retrieved_docs = vectorstore.similarity_search(query, k=top_k)

        # Serialize for LLM consumption
        serialized = "\n\n" + "=" * 80 + "\n\n"

        for idx, doc in enumerate(retrieved_docs, 1):
            source = doc.metadata.get("source", "Unknown")
            section = doc.metadata.get("section", "")

            serialized += f"📋 POLICY REFERENCE {idx}\n"
            serialized += f"Source: {source}\n"
            if section:
                serialized += f"Section: {section}\n"
            serialized += f"\n{doc.page_content}\n"
            serialized += "\n" + "=" * 80 + "\n\n"

        # Return both serialized content and raw documents (as artifacts)
        return serialized, retrieved_docs

    return retrieve_policy


def create_policy_listing_tool(vectorstore: InMemoryVectorStore):
    """Create a policy category listing tool bound to a specific vectorstore.

    Args:
        vectorstore: InMemoryVectorStore instance with indexed policy documents

    Returns:
        Configured policy listing tool ready to use
    """

    @tool
    def list_policy_categories():
        """List all available policy categories and documents.

        Use this to discover what policy documentation is available in the system.
        Helps you understand what types of guidance you can retrieve.

        Returns:
            String listing all policy categories, sources, and topics covered
        """
        # Get representative documents from vectorstore
        # Use a broad search to get diverse results
        all_docs = vectorstore.similarity_search("policy process workflow", k=100)

        # Extract unique sources and sections
        sources = set()
        sections_by_source: dict[str, set[str]] = {}

        for doc in all_docs:
            source = doc.metadata.get("source", "Unknown")
            section = doc.metadata.get("section", "")

            sources.add(source)

            if source not in sections_by_source:
                sections_by_source[source] = set()

            if section:
                sections_by_source[source].add(section)

        # Build summary
        summary = "📚 AVAILABLE POLICY DOCUMENTATION\n\n"

        for source in sorted(sources):
            summary += f"📄 {source}\n"

            if source in sections_by_source and sections_by_source[source]:
                for section in sorted(sections_by_source[source]):
                    summary += f"   └─ {section}\n"

            summary += "\n"

        summary += "\n💡 TIP: Use retrieve_policy(query) to search for specific guidance\n"
        summary += "Example: retrieve_policy('How to handle timesheet discrepancies?')\n"

        return summary

    return list_policy_categories
