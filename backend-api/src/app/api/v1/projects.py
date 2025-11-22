"""Project API endpoints."""

import logging
import uuid
from datetime import datetime
from typing import Annotated

from db.models.composition import Composition, CompositionStatus
from db.models.project import Project
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.schemas.project import (
    ProjectCreateRequest,
    ProjectDeleteResponse,
    ProjectDuplicateResponse,
    ProjectListItemResponse,
    ProjectListResponse,
    ProjectResponse,
    ProjectRestoreResponse,
    ProjectUpdateRequest,
    ProjectVersionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProjectResponse)
async def create_project(
    request: ProjectCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectResponse:
    """Create a new project with linked composition.

    This endpoint creates a project and automatically creates a linked Composition
    with matching settings in the same transaction.

    Args:
        request: Project creation request with name, aspect_ratio, timebase_fps, user_id
        db: Database session (injected)

    Returns:
        ProjectResponse: Created project with nested composition

    Raises:
        HTTPException: 400 for validation errors, 500 for server errors
    """
    logger.info(
        "Creating new project",
        extra={
            "name": request.name,
            "user_id": str(request.user_id),
            "aspect_ratio": request.aspect_ratio,
            "timebase_fps": request.timebase_fps,
        },
    )

    try:
        async with db.begin_nested():
            # Create composition first (it's referenced by the project)
            composition = Composition(
                id=uuid.uuid4(),
                title=f"{request.name} - Composition",
                status=CompositionStatus.PENDING,
                composition_config={
                    "aspect_ratio": request.aspect_ratio,
                    "timebase_fps": request.timebase_fps,
                    "tracks": [],
                    "clips": [],
                    "transitions": [],
                },
            )
            db.add(composition)
            await db.flush()  # Flush to get the composition ID

            # Create project with reference to composition
            project = Project(
                id=uuid.uuid4(),
                name=request.name,
                user_id=request.user_id,
                aspect_ratio=request.aspect_ratio,
                timebase_fps=request.timebase_fps,
                composition_id=composition.id,
                is_deleted=False,
            )
            db.add(project)

        await db.commit()
        await db.refresh(project)
        await db.refresh(composition)

        # Manually attach composition to project for response
        project.composition = composition

        logger.info(
            "Project created successfully",
            extra={
                "project_id": str(project.id),
                "composition_id": str(composition.id),
            },
        )

        return ProjectResponse.model_validate(project)

    except Exception as e:
        await db.rollback()
        logger.exception(
            "Failed to create project",
            extra={
                "error": str(e),
                "name": request.name,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project",
        ) from e


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    name: str | None = Query(None, description="Filter by project name (case-insensitive search)"),
    sort_by: str = Query(
        "last_modified_at",
        regex="^(last_modified_at|created_at)$",
        description="Sort field",
    ),
    user_id: uuid.UUID | None = Query(None, description="Filter by user ID"),
) -> ProjectListResponse:
    """List projects with pagination and filtering.

    Returns lightweight project list without full composition data for performance.

    Args:
        db: Database session (injected)
        page: Page number (1-indexed)
        per_page: Number of items per page
        name: Optional name filter (case-insensitive LIKE search)
        sort_by: Sort field (last_modified_at or created_at)
        user_id: Optional user ID filter

    Returns:
        ProjectListResponse: Paginated list of projects

    Raises:
        HTTPException: 500 for server errors
    """
    try:
        # Build filters
        filters = [Project.is_deleted == False]  # noqa: E712
        if name:
            filters.append(Project.name.ilike(f"%{name}%"))
        if user_id:
            filters.append(Project.user_id == user_id)

        # Build query for total count
        count_query = select(func.count()).select_from(Project).where(and_(*filters))
        total = await db.scalar(count_query) or 0

        # Build query for projects
        sort_column = Project.last_modified_at if sort_by == "last_modified_at" else Project.created_at
        query = (
            select(Project)
            .where(and_(*filters))
            .order_by(desc(sort_column))
            .offset((page - 1) * per_page)
            .limit(per_page)
        )

        result = await db.execute(query)
        projects = result.scalars().all()

        logger.info(
            "Listed projects",
            extra={
                "page": page,
                "per_page": per_page,
                "total": total,
                "count": len(projects),
            },
        )

        return ProjectListResponse(
            items=[ProjectListItemResponse.model_validate(p) for p in projects],
            total=total,
            page=page,
            per_page=per_page,
        )

    except Exception as e:
        logger.exception("Failed to list projects", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list projects",
        ) from e


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectResponse:
    """Get a single project with full composition data.

    Args:
        project_id: Project UUID
        db: Database session (injected)

    Returns:
        ProjectResponse: Project with nested composition

    Raises:
        HTTPException: 404 if project not found or deleted, 500 for server errors
    """
    try:
        query = (
            select(Project)
            .where(and_(Project.id == project_id, Project.is_deleted == False))  # noqa: E712
            .options(selectinload(Project.composition))
        )

        result = await db.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )

        logger.info("Retrieved project", extra={"project_id": str(project_id)})

        return ProjectResponse.model_validate(project)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Failed to get project",
            extra={"error": str(e), "project_id": str(project_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get project",
        ) from e


@router.delete("/{project_id}", response_model=ProjectDeleteResponse)
async def delete_project(
    project_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectDeleteResponse:
    """Soft delete a project.

    Sets is_deleted flag to True, preserving data for recovery.

    Args:
        project_id: Project UUID
        db: Database session (injected)

    Returns:
        ProjectDeleteResponse: Deletion confirmation

    Raises:
        HTTPException: 404 if project not found, 500 for server errors
    """
    try:
        query = select(Project).where(
            and_(Project.id == project_id, Project.is_deleted == False)  # noqa: E712
        )

        result = await db.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )

        # Soft delete
        project.is_deleted = True
        project.last_modified_at = datetime.utcnow()

        await db.commit()

        logger.info("Project soft deleted", extra={"project_id": str(project_id)})

        return ProjectDeleteResponse(
            id=project_id,
            message="Project successfully deleted",
            deleted_at=project.last_modified_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(
            "Failed to delete project",
            extra={"error": str(e), "project_id": str(project_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project",
        ) from e


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    request: ProjectUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectResponse:
    """Update project (autosave) with optimistic locking.

    Implements optimistic locking using updated_at timestamp to prevent
    concurrent edit conflicts.

    Args:
        project_id: Project UUID
        request: Project update request (name, thumbnail_url, composition)
        db: Database session (injected)

    Returns:
        ProjectResponse: Updated project with fresh updated_at

    Raises:
        HTTPException: 404 if not found, 409 for conflict, 500 for server errors
    """
    try:
        # Fetch project with composition
        query = (
            select(Project)
            .where(and_(Project.id == project_id, Project.is_deleted == False))  # noqa: E712
            .options(selectinload(Project.composition))
        )

        result = await db.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )

        # Optimistic locking check
        if request.updated_at and project.updated_at != request.updated_at:
            logger.warning(
                "Optimistic lock conflict detected",
                extra={
                    "project_id": str(project_id),
                    "client_timestamp": request.updated_at.isoformat(),
                    "server_timestamp": project.updated_at.isoformat(),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Project has been modified by another user. Please refresh and try again.",
            )

        # Update project fields
        if request.name is not None:
            project.name = request.name
        if request.thumbnail_url is not None:
            project.thumbnail_url = request.thumbnail_url

        # Update composition if provided
        if request.composition is not None and project.composition:
            # Update composition_config with new tracks/clips/transitions structure
            project.composition.composition_config = request.composition

        # Update timestamp
        project.last_modified_at = datetime.utcnow()

        await db.commit()
        await db.refresh(project)
        await db.refresh(project.composition)

        logger.info(
            "Project updated (autosave)",
            extra={
                "project_id": str(project_id),
                "updated_fields": {
                    "name": request.name is not None,
                    "thumbnail": request.thumbnail_url is not None,
                    "composition": request.composition is not None,
                },
            },
        )

        return ProjectResponse.model_validate(project)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(
            "Failed to update project",
            extra={"error": str(e), "project_id": str(project_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project",
        ) from e


@router.post("/{project_id}/duplicate", response_model=ProjectDuplicateResponse)
async def duplicate_project(
    project_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectDuplicateResponse:
    """Duplicate a project with deep copy of composition.

    Creates a new project and composition with new UUIDs, appending 'Copy' to the name.

    Args:
        project_id: Project UUID to duplicate
        db: Database session (injected)

    Returns:
        ProjectDuplicateResponse: New duplicated project info

    Raises:
        HTTPException: 404 if project not found, 500 for server errors
    """
    try:
        # Fetch original project with composition
        query = (
            select(Project)
            .where(and_(Project.id == project_id, Project.is_deleted == False))  # noqa: E712
            .options(selectinload(Project.composition))
        )

        result = await db.execute(query)
        original_project = result.scalar_one_or_none()

        if not original_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )

        # Generate new name with 'Copy' suffix
        base_name = original_project.name
        new_name = f"{base_name} (Copy)"

        # Check if name already exists and increment
        counter = 1
        while True:
            check_query = select(func.count()).select_from(Project).where(Project.name == new_name)
            exists = await db.scalar(check_query)
            if not exists:
                break
            counter += 1
            new_name = f"{base_name} (Copy {counter})"

        async with db.begin_nested():
            # Create new composition (deep copy)
            new_composition = Composition(
                id=uuid.uuid4(),
                title=f"{new_name} - Composition",
                status=CompositionStatus.PENDING,
                composition_config=original_project.composition.composition_config.copy()
                if original_project.composition
                else {},
            )
            db.add(new_composition)
            await db.flush()

            # Create new project
            new_project = Project(
                id=uuid.uuid4(),
                name=new_name,
                user_id=original_project.user_id,
                aspect_ratio=original_project.aspect_ratio,
                timebase_fps=original_project.timebase_fps,
                composition_id=new_composition.id,
                is_deleted=False,
                # Don't copy thumbnail_url or output_url - these are specific to original
            )
            db.add(new_project)

        await db.commit()
        await db.refresh(new_project)

        logger.info(
            "Project duplicated",
            extra={
                "original_project_id": str(project_id),
                "new_project_id": str(new_project.id),
                "new_name": new_name,
            },
        )

        return ProjectDuplicateResponse(
            id=new_project.id,
            name=new_name,
            original_project_id=project_id,
            composition_id=new_composition.id,
            created_at=new_project.created_at,
            message="Project duplicated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(
            "Failed to duplicate project",
            extra={"error": str(e), "project_id": str(project_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to duplicate project",
        ) from e


@router.get("/{project_id}/versions", response_model=ProjectVersionResponse)
async def get_project_versions(
    project_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectVersionResponse:
    """Get project version history (future feature).

    This endpoint is a placeholder for future versioning functionality.

    Args:
        project_id: Project UUID
        db: Database session (injected)

    Returns:
        ProjectVersionResponse: Version history (empty for now)

    Raises:
        HTTPException: 501 Not Implemented
    """
    logger.info(
        "Version history requested (not implemented)",
        extra={"project_id": str(project_id)},
    )

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Version history feature not yet implemented. This endpoint will provide version tracking in a future release.",
    )


@router.post("/{project_id}/versions/{version_id}/restore", response_model=ProjectRestoreResponse)
async def restore_project_version(
    project_id: uuid.UUID,
    version_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectRestoreResponse:
    """Restore project to a previous version (future feature).

    This endpoint is a placeholder for future version restoration functionality.

    Args:
        project_id: Project UUID
        version_id: Version UUID to restore
        db: Database session (injected)

    Returns:
        ProjectRestoreResponse: Restoration result (not implemented)

    Raises:
        HTTPException: 501 Not Implemented
    """
    logger.info(
        "Version restoration requested (not implemented)",
        extra={
            "project_id": str(project_id),
            "version_id": str(version_id),
        },
    )

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Version restoration feature not yet implemented. This endpoint will provide version rollback in a future release.",
    )
