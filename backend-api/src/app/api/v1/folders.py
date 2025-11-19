"""Folder management endpoints."""

import logging
import uuid
from typing import Annotated

from db.models.folder import Folder
from db.models.media import MediaAsset
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.folder import (
    FolderContentsResponse,
    FolderCreate,
    FolderDeleteResponse,
    FolderLightResponse,
    FolderListResponse,
    FolderResponse,
    FolderTreeNode,
    FolderUpdate,
    MediaAssetLight,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def build_folder_tree(folders: list[Folder], asset_counts: dict[uuid.UUID, int]) -> list[FolderTreeNode]:
    """Build a hierarchical tree structure from a flat list of folders.

    Args:
        folders: List of folders sorted by path
        asset_counts: Dictionary mapping folder IDs to asset counts

    Returns:
        list[FolderTreeNode]: Root-level folders with nested children
    """
    # Create a mapping of folder ID to tree node
    folder_map: dict[uuid.UUID, FolderTreeNode] = {}

    # First pass: create all nodes
    for folder in folders:
        folder_map[folder.id] = FolderTreeNode(
            id=folder.id,
            name=folder.name,
            path=folder.path,
            parent_id=folder.parent_id,
            asset_count=asset_counts.get(folder.id, 0),
            children=[],
            created_at=folder.created_at,
            updated_at=folder.updated_at,
        )

    # Second pass: build tree structure
    root_nodes: list[FolderTreeNode] = []

    for folder in folders:
        node = folder_map[folder.id]

        if folder.parent_id is None:
            # Root level folder
            root_nodes.append(node)
        else:
            # Child folder - add to parent's children
            parent_node = folder_map.get(folder.parent_id)
            if parent_node:
                parent_node.children.append(node)

    return root_nodes


async def get_folder_by_id(
    folder_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Folder:
    """Get folder by ID and verify ownership.

    Args:
        folder_id: Folder UUID
        user_id: Owner user UUID
        db: Database session

    Returns:
        Folder: The folder if found and owned by user

    Raises:
        HTTPException: 404 if folder not found or not owned by user
    """
    result = await db.execute(
        select(Folder).where(
            and_(
                Folder.id == folder_id,
                Folder.owner_user_id == user_id,
            )
        )
    )
    folder = result.scalar_one_or_none()

    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Folder {folder_id} not found",
        )

    return folder


async def check_circular_reference(
    folder_id: uuid.UUID,
    new_parent_id: uuid.UUID,
    db: AsyncSession,
) -> bool:
    """Check if moving a folder would create a circular reference.

    Args:
        folder_id: Folder being moved
        new_parent_id: Proposed new parent
        db: Database session

    Returns:
        bool: True if circular reference would be created, False otherwise
    """
    # Get the path of the folder being moved
    result = await db.execute(select(Folder).where(Folder.id == folder_id))
    folder = result.scalar_one_or_none()

    if not folder:
        return False

    # Get the path of the new parent
    result = await db.execute(select(Folder).where(Folder.id == new_parent_id))
    parent = result.scalar_one_or_none()

    if not parent:
        return False

    # Check if the parent's path starts with the folder's path
    # This would mean the parent is a descendant of the folder
    if parent.path.startswith(f"{folder.path}/") or parent.path == folder.path:
        return True

    return False


async def recalculate_descendant_paths(
    folder: Folder,
    old_path: str,
    new_path: str,
    db: AsyncSession,
) -> int:
    """Recalculate paths for all descendants when a folder is moved.

    Args:
        folder: The folder that was moved
        old_path: Previous path of the folder
        new_path: New path of the folder
        db: Database session

    Returns:
        int: Number of descendants updated
    """
    # Find all descendants using the old path prefix
    result = await db.execute(
        select(Folder).where(Folder.path.like(f"{old_path}/%"))
    )
    descendants = result.scalars().all()

    # Update each descendant's path
    for descendant in descendants:
        # Replace the old path prefix with the new one
        descendant.path = descendant.path.replace(old_path, new_path, 1)

    return len(descendants)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=FolderResponse)
async def create_folder(
    request: FolderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FolderResponse:
    """Create a new folder with optional parent.

    Creates a folder in the hierarchical tree structure. If parent_id is provided,
    the folder becomes a child of that folder and the materialized path is computed
    from the parent hierarchy.

    Args:
        request: Folder creation request
        db: Database session (injected)

    Returns:
        FolderResponse: Created folder with computed path

    Raises:
        HTTPException: 400 for validation errors
        HTTPException: 404 if parent folder not found
        HTTPException: 409 if folder with same name exists in parent
        HTTPException: 500 for server errors
    """
    # TODO: Get user_id from authenticated session
    user_id = uuid.uuid4()  # Placeholder

    logger.info(
        "Creating folder",
        extra={
            "user_id": str(user_id),
            "name": request.name,
            "parent_id": str(request.parent_id) if request.parent_id else None,
        },
    )

    try:
        parent_path = None

        # If parent_id provided, verify parent exists and get its path
        if request.parent_id:
            parent = await get_folder_by_id(request.parent_id, user_id, db)
            parent_path = parent.path

        # Compute the new folder's path
        folder_id = uuid.uuid4()
        temp_folder = Folder(
            id=folder_id,
            name=request.name,
            parent_id=request.parent_id,
            owner_user_id=user_id,
            path="",  # Will be computed below
        )
        computed_path = temp_folder.compute_path(parent_path)

        # Check for duplicate folder name in same parent
        existing_check = await db.execute(
            select(Folder).where(
                and_(
                    Folder.owner_user_id == user_id,
                    Folder.parent_id == request.parent_id if request.parent_id else Folder.parent_id.is_(None),
                    Folder.name == request.name,
                )
            )
        )
        existing = existing_check.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Folder '{request.name}' already exists in this location",
            )

        # Create the folder
        folder = Folder(
            id=folder_id,
            name=request.name,
            parent_id=request.parent_id,
            path=computed_path,
            owner_user_id=user_id,
        )

        db.add(folder)
        await db.commit()
        await db.refresh(folder)

        # Get asset count (will be 0 for new folder)
        count_result = await db.execute(
            select(func.count(MediaAsset.id)).where(MediaAsset.folder_id == folder.id)
        )
        asset_count = count_result.scalar() or 0

        logger.info(
            "Folder created",
            extra={
                "folder_id": str(folder.id),
                "path": folder.path,
            },
        )

        # Build response
        response_data = FolderResponse.model_validate(folder)
        response_data.asset_count = asset_count

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Failed to create folder",
            extra={"error": str(e), "name": request.name},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create folder",
        ) from e


@router.get("/", response_model=FolderListResponse)
async def list_folders(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FolderListResponse:
    """List all folders as a hierarchical tree structure.

    Returns all folders owned by the authenticated user organized in a tree structure
    with parent-child relationships. Folders are sorted by their materialized path
    for efficient tree construction.

    Args:
        db: Database session (injected)

    Returns:
        FolderListResponse: Tree structure of all folders with asset counts

    Raises:
        HTTPException: 500 for server errors
    """
    # TODO: Get user_id from authenticated session
    user_id = uuid.uuid4()  # Placeholder

    logger.info(
        "Listing folders",
        extra={"user_id": str(user_id)},
    )

    try:
        # Query all folders for the user, sorted by path
        result = await db.execute(
            select(Folder)
            .where(Folder.owner_user_id == user_id)
            .order_by(Folder.path)
        )
        folders = result.scalars().all()

        # Get asset counts for all folders
        # Using a subquery to count non-deleted assets per folder
        asset_count_query = (
            select(
                MediaAsset.folder_id,
                func.count(MediaAsset.id).label("count"),
            )
            .where(
                and_(
                    MediaAsset.folder_id.in_([f.id for f in folders]),
                    MediaAsset.is_deleted == False,  # noqa: E712
                )
            )
            .group_by(MediaAsset.folder_id)
        )

        asset_count_result = await db.execute(asset_count_query)
        asset_counts = {row.folder_id: row.count for row in asset_count_result}

        # Build tree structure
        tree = build_folder_tree(list(folders), asset_counts)

        logger.info(
            "Folders listed",
            extra={
                "user_id": str(user_id),
                "total_folders": len(folders),
                "root_folders": len(tree),
            },
        )

        return FolderListResponse(
            folders=tree,
            total=len(folders),
        )

    except Exception as e:
        logger.exception(
            "Failed to list folders",
            extra={"error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list folders",
        ) from e


@router.get("/{folder_id}", response_model=FolderResponse)
async def get_folder(
    folder_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FolderResponse:
    """Get a single folder by ID with asset count.

    Args:
        folder_id: Folder UUID
        db: Database session (injected)

    Returns:
        FolderResponse: Folder details with asset count

    Raises:
        HTTPException: 404 if folder not found
        HTTPException: 500 for server errors
    """
    # TODO: Get user_id from authenticated session
    user_id = uuid.uuid4()  # Placeholder

    try:
        folder = await get_folder_by_id(folder_id, user_id, db)

        # Get asset count
        count_result = await db.execute(
            select(func.count(MediaAsset.id)).where(
                and_(
                    MediaAsset.folder_id == folder.id,
                    MediaAsset.is_deleted == False,  # noqa: E712
                )
            )
        )
        asset_count = count_result.scalar() or 0

        # Build response
        response_data = FolderResponse.model_validate(folder)
        response_data.asset_count = asset_count

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Failed to get folder",
            extra={"error": str(e), "folder_id": str(folder_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get folder",
        ) from e


@router.patch("/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: uuid.UUID,
    request: FolderUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FolderResponse:
    """Update folder (rename or move to new parent).

    Supports renaming a folder (name change) or moving it to a different parent
    (parent_id change). When moving, validates no circular references are created
    and recalculates paths for all descendants.

    Args:
        folder_id: Folder UUID
        request: Update request with name and/or parent_id
        db: Database session (injected)

    Returns:
        FolderResponse: Updated folder

    Raises:
        HTTPException: 400 for validation errors or circular references
        HTTPException: 404 if folder or parent not found
        HTTPException: 409 if renamed folder conflicts with sibling
        HTTPException: 500 for server errors
    """
    # TODO: Get user_id from authenticated session
    user_id = uuid.uuid4()  # Placeholder

    logger.info(
        "Updating folder",
        extra={
            "folder_id": str(folder_id),
            "new_name": request.name,
            "new_parent_id": str(request.parent_id) if request.parent_id else None,
        },
    )

    try:
        folder = await get_folder_by_id(folder_id, user_id, db)
        old_path = folder.path
        path_changed = False

        # Handle rename
        if request.name is not None and request.name != folder.name:
            # Check for duplicate name in same parent
            existing_check = await db.execute(
                select(Folder).where(
                    and_(
                        Folder.owner_user_id == user_id,
                        Folder.parent_id == folder.parent_id if folder.parent_id else Folder.parent_id.is_(None),
                        Folder.name == request.name,
                        Folder.id != folder_id,
                    )
                )
            )
            existing = existing_check.scalar_one_or_none()

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Folder '{request.name}' already exists in this location",
                )

            folder.name = request.name
            path_changed = True

        # Handle move (parent change)
        if request.parent_id is not None and request.parent_id != folder.parent_id:
            # Prevent moving folder to itself
            if request.parent_id == folder_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot move folder to itself",
                )

            # Check for circular reference
            is_circular = await check_circular_reference(folder_id, request.parent_id, db)
            if is_circular:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot move folder to its own descendant (circular reference)",
                )

            # Verify new parent exists
            new_parent = await get_folder_by_id(request.parent_id, user_id, db)

            folder.parent_id = request.parent_id
            path_changed = True

        # Recalculate path if name or parent changed
        if path_changed:
            # Get new parent path if needed
            new_parent_path = None
            if folder.parent_id:
                parent_result = await db.execute(
                    select(Folder).where(Folder.id == folder.parent_id)
                )
                parent = parent_result.scalar_one()
                new_parent_path = parent.path

            # Compute new path
            new_path = folder.compute_path(new_parent_path)
            folder.path = new_path

            # Recalculate paths for all descendants
            descendants_updated = await recalculate_descendant_paths(
                folder, old_path, new_path, db
            )

            logger.info(
                "Folder paths recalculated",
                extra={
                    "folder_id": str(folder_id),
                    "old_path": old_path,
                    "new_path": new_path,
                    "descendants_updated": descendants_updated,
                },
            )

        await db.commit()
        await db.refresh(folder)

        # Get asset count
        count_result = await db.execute(
            select(func.count(MediaAsset.id)).where(
                and_(
                    MediaAsset.folder_id == folder.id,
                    MediaAsset.is_deleted == False,  # noqa: E712
                )
            )
        )
        asset_count = count_result.scalar() or 0

        # Build response
        response_data = FolderResponse.model_validate(folder)
        response_data.asset_count = asset_count

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Failed to update folder",
            extra={"error": str(e), "folder_id": str(folder_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update folder",
        ) from e


@router.get("/{folder_id}/contents", response_model=FolderContentsResponse)
async def get_folder_contents(
    folder_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = 1,
    per_page: int = 20,
    include_subfolders: bool = False,
) -> FolderContentsResponse:
    """Get folder contents with media assets and subfolders (paginated).

    Returns media assets and immediate subfolders in the specified folder.
    Supports pagination for assets and optionally includes assets from all
    descendant folders when include_subfolders=true.

    Args:
        folder_id: Folder UUID
        db: Database session (injected)
        page: Page number (1-indexed)
        per_page: Items per page (max 100)
        include_subfolders: Include assets from descendant folders

    Returns:
        FolderContentsResponse: Paginated folder contents

    Raises:
        HTTPException: 404 if folder not found
        HTTPException: 500 for server errors
    """
    # TODO: Get user_id from authenticated session
    user_id = uuid.uuid4()  # Placeholder

    # Validate pagination
    per_page = min(per_page, 100)
    offset = (page - 1) * per_page

    logger.info(
        "Getting folder contents",
        extra={
            "folder_id": str(folder_id),
            "page": page,
            "per_page": per_page,
            "include_subfolders": include_subfolders,
        },
    )

    try:
        folder = await get_folder_by_id(folder_id, user_id, db)

        # Get immediate subfolders
        subfolders_result = await db.execute(
            select(Folder)
            .where(Folder.parent_id == folder_id)
            .order_by(Folder.name)
        )
        subfolders = subfolders_result.scalars().all()

        # Get asset counts for subfolders
        if subfolders:
            subfolder_ids = [sf.id for sf in subfolders]
            asset_count_query = (
                select(
                    MediaAsset.folder_id,
                    func.count(MediaAsset.id).label("count"),
                )
                .where(
                    and_(
                        MediaAsset.folder_id.in_(subfolder_ids),
                        MediaAsset.is_deleted == False,  # noqa: E712
                    )
                )
                .group_by(MediaAsset.folder_id)
            )
            asset_count_result = await db.execute(asset_count_query)
            subfolder_asset_counts = {row.folder_id: row.count for row in asset_count_result}
        else:
            subfolder_asset_counts = {}

        # Build subfolder responses
        subfolder_responses = [
            FolderLightResponse(
                id=sf.id,
                name=sf.name,
                path=sf.path,
                asset_count=subfolder_asset_counts.get(sf.id, 0),
            )
            for sf in subfolders
        ]

        # Build assets query
        if include_subfolders:
            # Include assets from this folder and all descendants
            # Use path pattern matching
            assets_query = select(MediaAsset).where(
                and_(
                    MediaAsset.is_deleted == False,  # noqa: E712
                    or_(
                        MediaAsset.folder_id == folder_id,
                        MediaAsset.folder_id.in_(
                            select(Folder.id).where(Folder.path.like(f"{folder.path}/%"))
                        ),
                    ),
                )
            )
        else:
            # Only assets in this specific folder
            assets_query = select(MediaAsset).where(
                and_(
                    MediaAsset.folder_id == folder_id,
                    MediaAsset.is_deleted == False,  # noqa: E712
                )
            )

        # Count total assets
        count_query = select(func.count()).select_from(assets_query.subquery())
        total_result = await db.execute(count_query)
        total_assets = total_result.scalar() or 0

        # Apply pagination and ordering
        assets_query = (
            assets_query
            .order_by(MediaAsset.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )

        # Execute assets query
        assets_result = await db.execute(assets_query)
        assets = assets_result.scalars().all()

        # Build asset responses
        asset_responses = [
            MediaAssetLight(
                id=asset.id,
                name=asset.name,
                file_type=asset.file_type.value,
                file_size=asset.file_size,
                thumbnail_s3_key=asset.thumbnail_s3_key,
                created_at=asset.created_at,
            )
            for asset in assets
        ]

        total_pages = (total_assets + per_page - 1) // per_page if total_assets > 0 else 0

        logger.info(
            "Folder contents retrieved",
            extra={
                "folder_id": str(folder_id),
                "subfolders_count": len(subfolders),
                "assets_count": len(assets),
                "total_assets": total_assets,
            },
        )

        return FolderContentsResponse(
            folder_id=folder_id,
            folder_path=folder.path,
            subfolders=subfolder_responses,
            assets=asset_responses,
            total_assets=total_assets,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Failed to get folder contents",
            extra={"error": str(e), "folder_id": str(folder_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get folder contents",
        ) from e


@router.delete("/{folder_id}", response_model=FolderDeleteResponse)
async def delete_folder(
    folder_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    cascade: bool = False,
) -> FolderDeleteResponse:
    """Delete a folder and optionally cascade to children.

    By default, requires folder to be empty (no subfolders or assets).
    If cascade=true, deletes all subfolders and sets media assets' folder_id to None.

    Args:
        folder_id: Folder UUID
        cascade: Whether to cascade delete to children (default: False)
        db: Database session (injected)

    Returns:
        FolderDeleteResponse: Deletion result with affected counts

    Raises:
        HTTPException: 400 if folder not empty and cascade=false
        HTTPException: 404 if folder not found
        HTTPException: 500 for server errors
    """
    # TODO: Get user_id from authenticated session
    user_id = uuid.uuid4()  # Placeholder

    logger.info(
        "Deleting folder",
        extra={
            "folder_id": str(folder_id),
            "cascade": cascade,
        },
    )

    try:
        folder = await get_folder_by_id(folder_id, user_id, db)

        # Count children and assets
        children_result = await db.execute(
            select(func.count(Folder.id)).where(Folder.parent_id == folder_id)
        )
        children_count = children_result.scalar() or 0

        assets_result = await db.execute(
            select(func.count(MediaAsset.id)).where(MediaAsset.folder_id == folder_id)
        )
        assets_count = assets_result.scalar() or 0

        # If not empty and not cascading, reject deletion
        if (children_count > 0 or assets_count > 0) and not cascade:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Folder is not empty ({children_count} subfolders, {assets_count} assets). Use cascade=true to force delete.",
            )

        affected_subfolders = 0
        affected_assets = 0

        if cascade:
            # Find all descendants using path pattern
            descendants_result = await db.execute(
                select(Folder).where(Folder.path.like(f"{folder.path}/%"))
            )
            descendants = descendants_result.scalars().all()
            affected_subfolders = len(descendants)

            # Delete all descendants
            for descendant in descendants:
                await db.delete(descendant)

            # Update media assets in this folder and descendants to have null folder_id
            # Find all assets in the folder and its descendants
            assets_to_update = await db.execute(
                select(MediaAsset).where(
                    or_(
                        MediaAsset.folder_id == folder_id,
                        MediaAsset.folder_id.in_([d.id for d in descendants]),
                    )
                )
            )
            assets_list = assets_to_update.scalars().all()
            affected_assets = len(assets_list)

            for asset in assets_list:
                asset.folder_id = None

        # Delete the folder itself
        await db.delete(folder)
        await db.commit()

        logger.info(
            "Folder deleted",
            extra={
                "folder_id": str(folder_id),
                "affected_subfolders": affected_subfolders,
                "affected_assets": affected_assets,
            },
        )

        return FolderDeleteResponse(
            deleted=True,
            folder_id=folder_id,
            affected_subfolders=affected_subfolders,
            affected_assets=affected_assets,
            message=f"Folder deleted successfully. {affected_subfolders} subfolders and {affected_assets} assets affected.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Failed to delete folder",
            extra={"error": str(e), "folder_id": str(folder_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete folder",
        ) from e
