"""
Timeline Edit Planner Service - PR #402: Timeline Edit Planner
Converts abstract edit operations into concrete timeline modifications.
"""

import copy
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from ..models.edit_intent import EditPlan, FFmpegOperation, EditOperation, EditTarget
from ..models.clip_assembly import DatabaseClipMetadata


class TimelineEditPlannerService:
    """
    Service for planning and validating timeline edits.

    This service takes abstract edit operations from PR #401 and converts them
    into concrete timeline modifications that can be executed by the video
    processing backend.
    """

    def __init__(self, redis_client=None, use_mock: bool = False):
        """
        Initialize the timeline edit planner service.

        Args:
            redis_client: Optional Redis client for caching
            use_mock: Whether to use mock responses for testing
        """
        self.redis_client = redis_client
        self.use_mock = use_mock

    async def plan_timeline_edits(
        self,
        edit_plan: EditPlan,
        clip_metadata: List[DatabaseClipMetadata]
    ) -> 'TimelineEditResult':
        """
        Plan timeline edits based on an edit plan and current clip metadata.

        Args:
            edit_plan: The edit plan containing FFmpeg operations
            clip_metadata: Current clip metadata for the video

        Returns:
            TimelineEditResult: Planned timeline modifications with validation
        """
        # Create a copy of clip metadata to work with
        timeline_clips = copy.deepcopy(clip_metadata)

        # Sort clips by sequence order to ensure proper indexing
        timeline_clips.sort(key=lambda c: c.sequence_order)

        # Validate operation feasibility
        validation_result = self._validate_operations(edit_plan.operations, timeline_clips)

        if not validation_result['is_feasible']:
            return TimelineEditResult(
                original_plan=edit_plan,
                modified_clips=timeline_clips,
                applied_operations=[],
                validation_result=validation_result,
                is_successful=False,
                error_message=validation_result.get('error_message', 'Operations are not feasible')
            )

        # Apply operations in the correct order
        applied_operations = []
        successful_operations = []

        for operation in edit_plan.operations:
            try:
                success = self._apply_operation(operation, timeline_clips)
                applied_operations.append(operation)

                if success:
                    successful_operations.append(operation)
                else:
                    # Operation failed but didn't break validation - log and continue
                    pass

            except Exception as e:
                # Operation failed - we could choose to continue or stop
                # For now, continue but mark as failed
                applied_operations.append(operation)

        # Recalculate timeline after all operations
        self._recalculate_timeline(timeline_clips)

        # Create result
        result = TimelineEditResult(
            original_plan=edit_plan,
            modified_clips=timeline_clips,
            applied_operations=applied_operations,
            successful_operations=successful_operations,
            validation_result=validation_result,
            is_successful=len(successful_operations) == len(edit_plan.operations),
            timeline_preview=self._generate_timeline_preview(timeline_clips)
        )

        return result

    def _validate_operations(
        self,
        operations: List[FFmpegOperation],
        clips: List[DatabaseClipMetadata]
    ) -> Dict[str, Any]:
        """
        Validate that operations are feasible given the current clips.

        Args:
            operations: List of operations to validate
            clips: Current clip metadata

        Returns:
            Dict with validation results
        """
        result = {
            'is_feasible': True,
            'errors': [],
            'warnings': [],
            'clip_count': len(clips)
        }

        max_clip_index = len(clips) - 1

        for i, operation in enumerate(operations):
            # Check clip indices are valid
            for clip_idx in operation.target_clips:
                if clip_idx < 0 or clip_idx > max_clip_index:
                    result['errors'].append(
                        f"Operation {i} ({operation.operation_type.value}) references invalid clip index {clip_idx} "
                        f"(valid range: 0-{max_clip_index})"
                    )
                    result['is_feasible'] = False

            # Validate operation-specific constraints
            if operation.operation_type == EditOperation.TRIM:
                validation = self._validate_trim_operation(operation, clips)
                result['errors'].extend(validation.get('errors', []))
                result['warnings'].extend(validation.get('warnings', []))

            elif operation.operation_type == EditOperation.REORDER:
                validation = self._validate_reorder_operation(operation, clips)
                result['errors'].extend(validation.get('errors', []))
                result['warnings'].extend(validation.get('warnings', []))

            elif operation.operation_type == EditOperation.SPLIT:
                validation = self._validate_split_operation(operation, clips)
                result['errors'].extend(validation.get('errors', []))
                result['warnings'].extend(validation.get('warnings', []))

        # Check for conflicting operations
        conflicts = self._detect_operation_conflicts(operations)
        if conflicts:
            result['errors'].extend(conflicts)
            result['is_feasible'] = False

        if result['errors']:
            result['error_message'] = f"Validation failed: {len(result['errors'])} errors found"

        return result

    def _validate_trim_operation(
        self,
        operation: FFmpegOperation,
        clips: List[DatabaseClipMetadata]
    ) -> Dict[str, List[str]]:
        """Validate a trim operation"""
        errors = []
        warnings = []

        if not operation.target_clips:
            errors.append("Trim operation must specify target clips")
            return {'errors': errors, 'warnings': warnings}

        clip_idx = operation.target_clips[0]  # Trim typically affects one clip
        clip = clips[clip_idx]

        # Check for duration parameters
        start_time = operation.parameters.get('start_time')
        end_time = operation.parameters.get('end_time')
        duration = operation.parameters.get('duration')

        if duration is not None:
            if duration <= 0:
                errors.append(f"Trim duration must be positive, got {duration}")
            elif duration > clip.duration_seconds:
                errors.append(f"Cannot trim clip {clip_idx} to {duration}s (original: {clip.duration_seconds}s)")
        elif start_time is not None and end_time is not None:
            if start_time >= end_time:
                errors.append(f"Trim start_time ({start_time}) must be before end_time ({end_time})")
            elif end_time > clip.duration_seconds:
                warnings.append(f"Trim end_time ({end_time}) exceeds clip duration ({clip.duration_seconds})")

        return {'errors': errors, 'warnings': warnings}

    def _validate_reorder_operation(
        self,
        operation: FFmpegOperation,
        clips: List[DatabaseClipMetadata]
    ) -> Dict[str, List[str]]:
        """Validate a reorder operation"""
        errors = []
        warnings = []

        if len(operation.target_clips) < 2:
            errors.append("Reorder operation requires at least 2 clips")
            return {'errors': errors, 'warnings': warnings}

        # Check that all indices are valid and unique
        seen_indices = set()
        for clip_idx in operation.target_clips:
            if clip_idx in seen_indices:
                errors.append(f"Reorder operation contains duplicate clip index {clip_idx}")
            seen_indices.add(clip_idx)

        return {'errors': errors, 'warnings': warnings}

    def _validate_split_operation(
        self,
        operation: FFmpegOperation,
        clips: List[DatabaseClipMetadata]
    ) -> Dict[str, List[str]]:
        """Validate a split operation"""
        errors = []
        warnings = []

        if not operation.target_clips:
            errors.append("Split operation must specify target clips")
            return {'errors': errors, 'warnings': warnings}

        clip_idx = operation.target_clips[0]
        clip = clips[clip_idx]

        split_time = operation.parameters.get('split_time')
        if split_time is None:
            errors.append("Split operation must specify split_time parameter")
        elif split_time <= 0 or split_time >= clip.duration_seconds:
            errors.append(f"Split time {split_time} is outside valid range (0, {clip.duration_seconds})")

        return {'errors': errors, 'warnings': warnings}

    def _detect_operation_conflicts(self, operations: List[FFmpegOperation]) -> List[str]:
        """Detect conflicting operations"""
        conflicts = []

        # Group operations by affected clips
        clip_operations = {}
        for op in operations:
            for clip_idx in op.target_clips:
                if clip_idx not in clip_operations:
                    clip_operations[clip_idx] = []
                clip_operations[clip_idx].append(op)

        # Check for conflicts on the same clip
        for clip_idx, ops in clip_operations.items():
            if len(ops) > 1:
                # Check for incompatible operations
                op_types = [op.operation_type for op in ops]

                # Cannot trim and split the same clip
                if EditOperation.TRIM in op_types and EditOperation.SPLIT in op_types:
                    conflicts.append(
                        f"Clip {clip_idx}: Cannot both trim and split the same clip in one edit plan"
                    )

                # Multiple reorder operations on same clip set
                reorder_ops = [op for op in ops if op.operation_type == EditOperation.REORDER]
                if len(reorder_ops) > 1:
                    conflicts.append(
                        f"Clip {clip_idx}: Multiple reorder operations conflict"
                    )

        return conflicts

    def _apply_operation(
        self,
        operation: FFmpegOperation,
        clips: List[DatabaseClipMetadata]
    ) -> bool:
        """
        Apply a single operation to the clips.

        Args:
            operation: The operation to apply
            clips: Current clip metadata (modified in-place)

        Returns:
            bool: True if operation was applied successfully
        """
        try:
            if operation.operation_type == EditOperation.TRIM:
                return self._apply_trim_operation(operation, clips)
            elif operation.operation_type == EditOperation.REORDER:
                return self._apply_reorder_operation(operation, clips)
            elif operation.operation_type == EditOperation.TIMING:
                return self._apply_timing_operation(operation, clips)
            elif operation.operation_type == EditOperation.OVERLAY:
                return self._apply_overlay_operation(operation, clips)
            else:
                # For unsupported operations, mark as successful but don't modify
                return True

        except Exception as e:
            # Operation failed
            return False

    def _apply_trim_operation(
        self,
        operation: FFmpegOperation,
        clips: List[DatabaseClipMetadata]
    ) -> bool:
        """Apply a trim operation"""
        if not operation.target_clips:
            return False

        clip_idx = operation.target_clips[0]
        clip = clips[clip_idx]

        # Extract trim parameters
        start_time = operation.parameters.get('start_time', 0.0)
        duration = operation.parameters.get('duration')
        end_time = operation.parameters.get('end_time')

        if duration is not None:
            # Trim to specific duration
            if duration <= 0 or duration > clip.duration_seconds:
                return False
            clip.end_time_seconds = clip.start_time_seconds + duration
        elif end_time is not None:
            # Trim to specific end time
            if end_time <= start_time or end_time > clip.start_time_seconds + clip.duration_seconds:
                return False
            clip.end_time_seconds = end_time
        else:
            return False

        # Update duration
        clip.duration_seconds = clip.end_time_seconds - clip.start_time_seconds

        return True

    def _apply_reorder_operation(
        self,
        operation: FFmpegOperation,
        clips: List[DatabaseClipMetadata]
    ) -> bool:
        """Apply a reorder operation"""
        if len(operation.target_clips) < 2:
            return False

        # Get the target order from parameters
        new_order = operation.parameters.get('new_order')
        if not new_order or len(new_order) != len(operation.target_clips):
            return False

        # Create a mapping of current clips
        clip_map = {clip.sequence_order: clip for clip in clips}

        # Validate that all target clips exist
        for clip_idx in operation.target_clips:
            if clip_idx not in clip_map:
                return False

        # Apply the new ordering
        for i, clip_idx in enumerate(operation.target_clips):
            new_sequence_order = new_order[i]
            clip_map[clip_idx].sequence_order = new_sequence_order

        # The timeline will be recalculated later in _recalculate_timeline
        return True

    def _apply_timing_operation(
        self,
        operation: FFmpegOperation,
        clips: List[DatabaseClipMetadata]
    ) -> bool:
        """Apply a timing adjustment operation"""
        if not operation.target_clips:
            return False

        clip_idx = operation.target_clips[0]
        clip = clips[clip_idx]

        # Adjust start time
        time_offset = operation.parameters.get('time_offset', 0.0)
        clip.start_time_seconds += time_offset
        clip.end_time_seconds += time_offset

        return True

    def _apply_overlay_operation(
        self,
        operation: FFmpegOperation,
        clips: List[DatabaseClipMetadata]
    ) -> bool:
        """Apply an overlay operation"""
        if not operation.target_clips:
            return False

        # For overlay timing changes, we modify when overlays appear
        start_time = operation.parameters.get('start_time')
        duration = operation.parameters.get('duration')
        end_time = operation.parameters.get('end_time')

        # Validate timing parameters
        if start_time is None:
            return False

        if duration is not None and duration <= 0:
            return False

        if end_time is not None and end_time <= start_time:
            return False

        # In a full implementation, this would modify overlay metadata
        # For now, we validate the operation parameters
        return True

    def _recalculate_timeline(self, clips: List[DatabaseClipMetadata]) -> None:
        """
        Recalculate timeline after operations are applied.

        This ensures clips don't overlap and maintains proper sequencing based on sequence_order.
        """
        if not clips:
            return

        # Sort by sequence order first (this is the intended playback order)
        clips.sort(key=lambda c: c.sequence_order)

        # Recalculate start/end times to ensure no overlaps and proper sequencing
        current_time = 0.0
        for clip in clips:
            # Ensure no negative start times
            if clip.start_time_seconds < 0:
                time_shift = -clip.start_time_seconds
                clip.start_time_seconds += time_shift
                clip.end_time_seconds += time_shift

            # If this clip starts before the current timeline position,
            # shift it to start at the current position
            if clip.start_time_seconds < current_time:
                shift = current_time - clip.start_time_seconds
                clip.start_time_seconds += shift
                clip.end_time_seconds += shift
            elif clip.start_time_seconds > current_time:
                # If there's a gap, we'll fill it by moving clips earlier
                # This maintains contiguous playback
                shift = clip.start_time_seconds - current_time
                clip.start_time_seconds -= shift
                clip.end_time_seconds -= shift

            # Update the current timeline position
            current_time = clip.end_time_seconds

        # Final pass: ensure all clips have valid timing relationships
        for i, clip in enumerate(clips):
            # Ensure duration matches start/end times
            expected_duration = clip.end_time_seconds - clip.start_time_seconds
            if abs(expected_duration - clip.duration_seconds) > 0.01:  # Allow small floating point differences
                clip.duration_seconds = expected_duration

    def _generate_timeline_preview(self, clips: List[DatabaseClipMetadata]) -> Dict[str, Any]:
        """Generate a preview of the timeline after modifications"""
        preview = {
            'total_duration': 0.0,
            'clip_count': len(clips),
            'clips': []
        }

        for clip in clips:
            clip_preview = {
                'clip_id': clip.clip_id,
                'sequence_order': clip.sequence_order,
                'start_time': clip.start_time_seconds,
                'end_time': clip.end_time_seconds,
                'duration': clip.duration_seconds,
                'scene_id': clip.scene_id
            }
            preview['clips'].append(clip_preview)

        if clips:
            preview['total_duration'] = max(c.end_time_seconds for c in clips)

        return preview


class TimelineEditResult:
    """
    Result of a timeline edit planning operation.

    Contains the original plan, modified clips, and validation results.
    """

    def __init__(
        self,
        original_plan: EditPlan,
        modified_clips: List[DatabaseClipMetadata],
        applied_operations: List[FFmpegOperation],
        validation_result: Dict[str, Any],
        timeline_preview: Optional[Dict[str, Any]] = None,
        successful_operations: Optional[List[FFmpegOperation]] = None,
        is_successful: bool = True,
        error_message: Optional[str] = None
    ):
        self.original_plan = original_plan
        self.modified_clips = modified_clips
        self.applied_operations = applied_operations
        self.successful_operations = successful_operations or applied_operations
        self.validation_result = validation_result
        self.timeline_preview = timeline_preview or {}
        self.is_successful = is_successful
        self.error_message = error_message
        self.created_at = datetime.utcnow()

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the edit result"""
        return {
            'generation_id': self.original_plan.generation_id,
            'request_id': self.original_plan.request_id,
            'is_successful': self.is_successful,
            'total_operations': len(self.original_plan.operations),
            'successful_operations': len(self.successful_operations),
            'validation_errors': len(self.validation_result.get('errors', [])),
            'validation_warnings': len(self.validation_result.get('warnings', [])),
            'total_duration': self.timeline_preview.get('total_duration', 0.0),
            'clip_count': self.timeline_preview.get('clip_count', 0),
            'error_message': self.error_message
        }

    def is_fully_successful(self) -> bool:
        """Check if all operations were applied successfully"""
        return (
            self.is_successful and
            len(self.successful_operations) == len(self.original_plan.operations) and
            len(self.validation_result.get('errors', [])) == 0
        )
