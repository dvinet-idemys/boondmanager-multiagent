"""
Policy Indexing Script

Loads markdown policy documents from the policies/ directory and indexes them
into an InMemoryVectorStore for semantic search.

Usage:
    python -m src.indexing.index_policies
"""

from pathlib import Path

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import MarkdownHeaderTextSplitter

from src.llm_config import get_embedding_model


def load_markdown_policies(policies_dir: Path) -> list[Document]:
    """Load all markdown files from policies directory.

    Args:
        policies_dir: Path to directory containing policy markdown files

    Returns:
        List of Document objects with metadata
    """
    documents = []

    for md_file in policies_dir.glob("*.md"):
        print(f"📄 Loading: {md_file.name}")

        # Read the markdown content
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Split by markdown headers to create logical sections
        headers_to_split_on = [
            ("#", "title"),
            ("##", "section"),
        ]

        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

        md_header_splits = markdown_splitter.split_text(content)

        # Add source metadata to each split and filter empty content
        for split in md_header_splits:
            # Skip documents with empty or whitespace-only content
            if not split.page_content or not split.page_content.strip():
                continue

            split.metadata["source"] = md_file.stem  # filename without extension
            split.metadata["file"] = md_file.name
            documents.append(split)

    print(
        f"\n✅ Loaded {len(documents)} document sections from {len(list(policies_dir.glob('*.md')))} files"
    )

    return documents


def create_policy_vectorstore(documents: list[Document]) -> InMemoryVectorStore:
    """Create and populate an InMemoryVectorStore with policy documents.

    Args:
        documents: List of Document objects to index

    Returns:
        Initialized InMemoryVectorStore with embedded documents
    """
    print("\n🔄 Creating embeddings and building vector store...")

    # Initialize embeddings
    embeddings = get_embedding_model()

    # Create vector store
    vectorstore = InMemoryVectorStore(embeddings)

    # Add documents
    vectorstore.add_documents(documents=documents)

    print(f"✅ Vector store created with {len(documents)} embedded sections")

    return vectorstore


def index_policies(policies_dir: Path | str = "policies") -> InMemoryVectorStore:
    """Main indexing function - load and index all policy documents.

    Args:
        policies_dir: Path to policies directory (default: "policies")

    Returns:
        Initialized InMemoryVectorStore ready for use
    """
    policies_path = Path(policies_dir)

    if not policies_path.exists():
        raise FileNotFoundError(
            f"Policies directory not found: {policies_path}\n"
            "Create it and add markdown policy documents first."
        )

    print(f"📚 Indexing policies from: {policies_path.absolute()}\n")

    # Load documents
    documents = load_markdown_policies(policies_path)

    if not documents:
        raise ValueError(
            f"No policy documents found in {policies_path}\n"
            "Add .md files to the policies/ directory."
        )

    # Create vector store
    vectorstore = create_policy_vectorstore(documents)

    print("\n🎉 Policy indexing complete!")

    return vectorstore


if __name__ == "__main__":
    # Run indexing
    try:
        vectorstore = index_policies()

        # Test retrieval
        print("\n🧪 Testing retrieval...")
        test_query = "How should I handle timesheet validation discrepancies?"
        results = vectorstore.similarity_search(test_query, k=2)

        print(f"\nQuery: {test_query}")
        print(f"Found {len(results)} relevant sections:\n")

        for idx, doc in enumerate(results, 1):
            source = doc.metadata.get("source", "Unknown")
            section = doc.metadata.get("section", "N/A")
            content_preview = doc.page_content[:200].replace("\n", " ")

            print(f"{idx}. {source} - {section}")
            print(f"   Preview: {content_preview}...\n")

        print("✅ Indexing and retrieval test successful!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
