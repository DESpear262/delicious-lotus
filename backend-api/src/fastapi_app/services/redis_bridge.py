"""
Redis Bridge - Bridges Redis Pub/Sub messages to Socket.io rooms
"""

import asyncio
import json
import logging
from typing import Optional

import redis.asyncio as aioredis
from app.config import settings
from fastapi_app.services.websocket_manager import get_websocket_manager

logger = logging.getLogger(__name__)

class RedisBridge:
    """
    Bridges Redis Pub/Sub messages to Socket.io rooms.
    Listens for 'job:progress:*' and forwards to 'generation:{id}' rooms.
    """
    
    def __init__(self):
        self.redis_url = str(settings.redis_url)
        self.pubsub = None
        self.redis = None
        self.task = None
        self.ws_manager = get_websocket_manager()
        self._running = False

    async def start(self):
        """Start the Redis listener"""
        if self._running:
            return

        try:
            self.redis = await aioredis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
            self.pubsub = self.redis.pubsub()
            
            # Subscribe to job progress updates
            await self.pubsub.psubscribe("job:progress:*")
            
            self._running = True
            self.task = asyncio.create_task(self.listen())
            logger.info("RedisBridge started listening to job:progress:*")
        except Exception as e:
            logger.error(f"Failed to start RedisBridge: {e}", exc_info=True)

    async def stop(self):
        """Stop the Redis listener"""
        self._running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        if self.pubsub:
            try:
                await self.pubsub.unsubscribe()
                await self.pubsub.close()
            except Exception:
                pass
                
        if self.redis:
            try:
                await self.redis.close()
            except Exception:
                pass
                
        logger.info("RedisBridge stopped")

    async def listen(self):
        """Main listener loop"""
        logger.info("RedisBridge listener loop started")
        while self._running:
            try:
                if not self.pubsub:
                    break
                    
                async for message in self.pubsub.listen():
                    if not self._running:
                        break
                        
                    if message["type"] == "pmessage":
                        await self.handle_message(message)
                        
            except asyncio.CancelledError:
                logger.info("RedisBridge listener cancelled")
                break
            except Exception as e:
                logger.error(f"RedisBridge listener error: {e}", exc_info=True)
                # Wait briefly before retrying loop
                await asyncio.sleep(1)
                
                # Reconnect if needed
                if self._running and (not self.redis or self.redis.connection is None):
                    try:
                        logger.info("RedisBridge reconnecting...")
                        self.redis = await aioredis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
                        self.pubsub = self.redis.pubsub()
                        await self.pubsub.psubscribe("job:progress:*")
                    except Exception as re:
                        logger.error(f"RedisBridge reconnection failed: {re}")

    async def handle_message(self, message):
        """Handle a single Redis message"""
        try:
            data_str = message.get("data")
            if not data_str:
                return
                
            data = json.loads(data_str)
            job_id = data.get("jobId")
            status = data.get("status")
            
            if not job_id:
                return

            # Look up full job metadata
            job_data = await self.get_job_data(job_id)
            if not job_data:
                logger.debug(f"No job data found for job {job_id}, skipping broadcast")
                return

            generation_id = job_data.get("generation_id")
            if not generation_id:
                logger.debug(f"No generation_id found for job {job_id}, skipping broadcast")
                return
                
            clip_index = job_data.get("clip_index", 0)
            total_clips = job_data.get("total_clips", 1)
            
            logger.debug(f"Forwarding Redis update for job {job_id} to generation {generation_id}")
            
            # Map status to Socket.io events
            if status == "succeeded":
                # Job succeeded, but we might not be "done" with the whole generation
                # For now, just emit progress 100%
                result = data.get("result", {})
                video_url = result.get("url")
                
                await self.ws_manager.emit_progress(
                    generation_id=generation_id,
                    step="completed", 
                    clip_number=clip_index,
                    total_clips=total_clips,
                    percentage=100.0,
                    message="Clip generated successfully"
                )
                
                if video_url:
                    # Also emit clip_completed
                    await self.ws_manager.emit_clip_completed(
                        generation_id=generation_id,
                        clip_id=job_id, # Use job_id as clip_id for now
                        thumbnail_url="", # No thumbnail in raw update
                        duration=0.0 # No duration in raw update
                    )

            elif status == "failed":
                error_msg = data.get("error", "Unknown error")
                await self.ws_manager.emit_error(
                    generation_id=generation_id,
                    code="GENERATION_FAILED",
                    message=error_msg,
                    recoverable=True
                )
                
            else:
                # Processing/Starting
                progress = data.get("progress", 0)
                msg = data.get("message", status)
                
                await self.ws_manager.emit_progress(
                    generation_id=generation_id,
                    step="generating",
                    clip_number=clip_index,
                    total_clips=total_clips,
                    percentage=float(progress) if progress else 0.0,
                    message=msg
                )

        except Exception as e:
            logger.error(f"Error handling Redis message: {e}", exc_info=True)

    async def get_job_data(self, job_id):
        """Retrieve full job metadata from Redis"""
        try:
            key = f"ai_job:{job_id}"
            # We use a separate connection or the existing one?
            # Using the existing one is fine for get()
            if not self.redis:
                 return None
                 
            data_str = await self.redis.get(key)
            if data_str:
                return json.loads(data_str)
        except Exception as e:
            logger.error(f"Error looking up job metadata: {e}")
        return None

# Global instance
redis_bridge = RedisBridge()

def get_redis_bridge():
    return redis_bridge
