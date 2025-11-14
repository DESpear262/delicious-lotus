"""Composition endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_compositions() -> dict[str, str]:
    """List all compositions.

    Returns:
        dict: Placeholder response
    """
    # TODO: Implement composition listing
    return {"message": "Compositions endpoint - to be implemented"}


@router.post("/")
async def create_composition() -> dict[str, str]:
    """Create a new composition.

    Returns:
        dict: Placeholder response
    """
    # TODO: Implement composition creation
    return {"message": "Create composition endpoint - to be implemented"}


@router.get("/{composition_id}")
async def get_composition(composition_id: str) -> dict[str, str]:
    """Get a specific composition.

    Args:
        composition_id: Composition identifier

    Returns:
        dict: Placeholder response
    """
    # TODO: Implement composition retrieval
    return {"message": f"Get composition {composition_id} endpoint - to be implemented"}
