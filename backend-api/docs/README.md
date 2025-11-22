# FFmpeg Backend Documentation

Welcome to the FFmpeg Backend Service documentation. This comprehensive guide covers everything from getting started to advanced production deployment.

## Quick Links

- **[Main README](../README.md)** - Project overview and quick start
- **[API Reference](./api-reference.md)** - Complete API endpoint documentation
- **[Architecture](./architecture/system-architecture.md)** - System design and architecture
- **[Troubleshooting](./guides/troubleshooting.md)** - Common issues and solutions
- **[Performance Tuning](./guides/performance-tuning.md)** - Optimization guide

## Documentation Structure

### 📚 API Documentation

#### [API Reference](./api-reference.md)
Complete reference for all API endpoints including:
- Health & status endpoints
- Composition management
- WebSocket real-time updates
- Internal processing API
- Authentication and rate limiting
- Error codes and responses

#### [API Examples](./api-examples/compositions.md)
Practical code examples in multiple languages:
- Python async examples
- JavaScript/TypeScript examples
- cURL command examples
- Complete workflow examples
- WebSocket integration
- Error handling patterns

### 🏗️ Architecture

#### [System Architecture](./architecture/system-architecture.md)
In-depth system design documentation:
- High-level architecture overview
- Component architecture (API, Workers, Database)
- Data flow diagrams
- Database schema and relationships
- Storage architecture (S3, temporary files)
- Redis architecture (queues, pub/sub)
- Scaling considerations (horizontal/vertical)
- Security architecture
- Monitoring and observability
- Disaster recovery procedures

### 📖 Guides

#### [Troubleshooting Guide](./guides/troubleshooting.md)
Comprehensive troubleshooting documentation:
- Service health checks
- Common issues and solutions
- Database problems and optimization
- Redis troubleshooting
- Worker issues
- FFmpeg debugging
- S3/Storage problems
- Performance diagnostics
- Debugging tools and techniques

#### [Performance Tuning Guide](./guides/performance-tuning.md)
Production optimization guide:
- Database optimization (connection pooling, indexes, queries)
- Redis optimization (memory, caching, queues)
- Worker optimization (concurrency, memory management)
- FFmpeg optimization (presets, hardware acceleration)
- API server optimization (async operations, caching)
- Infrastructure sizing recommendations
- Monitoring and profiling tools
- Optimization checklist

## Getting Started

### For Developers

1. **Quick Start**: Read the [Main README](../README.md) for installation and setup
2. **API Basics**: Check [API Reference](./api-reference.md) for endpoint details
3. **Code Examples**: Review [API Examples](./api-examples/compositions.md) for implementation patterns
4. **Architecture**: Understand the system by reading [System Architecture](./architecture/system-architecture.md)

### For DevOps/SRE

1. **Architecture**: Start with [System Architecture](./architecture/system-architecture.md)
2. **Deployment**: Review infrastructure sizing in [Performance Tuning](./guides/performance-tuning.md)
3. **Monitoring**: Set up monitoring using the observability section in [System Architecture](./architecture/system-architecture.md)
4. **Troubleshooting**: Bookmark [Troubleshooting Guide](./guides/troubleshooting.md) for incident response

### For Product/Business

1. **Overview**: Read [Main README](../README.md) for feature overview
2. **API Capabilities**: Review [API Reference](./api-reference.md) for available features
3. **Scaling**: Check scaling considerations in [System Architecture](./architecture/system-architecture.md)
4. **Performance**: Understand limits and performance characteristics in [Performance Tuning](./guides/performance-tuning.md)

## Key Features

### Video Composition
- **Multi-clip Editing**: Combine multiple video clips with precise timing
- **Audio Mixing**: Background music, voiceovers, and original audio blending
- **Text Overlays**: Add text with customizable position, timing, and styling
- **Multiple Output Formats**: Support for MP4, MOV, and WebM
- **Quality Presets**: Low, medium, and high quality encoding options
- **Resolution Support**: 720p, 1080p, and 4K output

### Processing Capabilities
- **Asynchronous Processing**: Non-blocking job queue with Redis
- **Progress Tracking**: Real-time progress updates via WebSocket
- **Hardware Acceleration**: NVIDIA NVENC and Intel QSV support
- **Concurrent Processing**: Handle multiple compositions simultaneously
- **Automatic Retry**: Failed jobs automatically retry with exponential backoff

### API Features
- **RESTful API**: Clean, intuitive API design
- **WebSocket Support**: Real-time status updates
- **Rate Limiting**: Protect against abuse
- **OpenAPI Documentation**: Auto-generated Swagger/ReDoc docs
- **Structured Error Responses**: Detailed error information with field-level validation

### Infrastructure
- **Docker Support**: Complete containerization with Docker Compose
- **Database Migrations**: Alembic for schema version management
- **S3 Integration**: Scalable media storage
- **Health Checks**: Comprehensive service health monitoring
- **Metrics & Logging**: Structured logging and Prometheus metrics

## Common Use Cases

### 1. Simple Video Concatenation
Combine multiple video clips into a single video:
```bash
POST /api/v1/compositions
{
  "title": "My Concatenated Video",
  "clips": [
    {"video_url": "clip1.mp4", "start_time": 0, "end_time": 10},
    {"video_url": "clip2.mp4", "start_time": 10, "end_time": 20}
  ],
  ...
}
```

### 2. Video with Background Music
Add background music to a video composition:
```bash
POST /api/v1/compositions
{
  "clips": [...],
  "audio": {
    "music_url": "background.mp3",
    "music_volume": 0.3,
    "original_audio_volume": 0.7
  },
  ...
}
```

### 3. Video with Text Overlays
Add text overlays to specific time ranges:
```bash
POST /api/v1/compositions
{
  "clips": [...],
  "overlays": [
    {
      "text": "Welcome!",
      "position": "center",
      "start_time": 0,
      "end_time": 3,
      "font_size": 48,
      "font_color": "#FFFFFF"
    }
  ],
  ...
}
```

### 4. Clip Normalization (Internal API)
Process and normalize video clips for AI processing:
```bash
POST /internal/v1/process-clips
{
  "clips": [
    {
      "clip_url": "raw_clip.mp4",
      "operations": ["normalize", "thumbnail"]
    }
  ],
  "callback_url": "https://ai-backend/callbacks/clips"
}
```

## API Rate Limits

| Endpoint Type | Requests/Minute | Burst |
|---------------|-----------------|-------|
| Public API (v1) | 60 | 10 |
| Internal API | 1000 | 100 |
| WebSocket Connections | 10 | 2 |

## Performance Characteristics

| Metric | Target | Notes |
|--------|--------|-------|
| API Latency (P95) | < 100ms | GET requests |
| Composition Creation | < 200ms | Including DB write and job enqueue |
| Video Processing | 1-5 min | Depends on length and complexity |
| Concurrent Jobs | 5-10 | Per worker instance |
| Throughput | 1000+ req/s | With horizontal scaling |

## Support & Contributing

### Getting Help

1. **Documentation**: Check this documentation first
2. **Troubleshooting**: Review [Troubleshooting Guide](./guides/troubleshooting.md)
3. **Issues**: Search [GitHub Issues](https://github.com/your-org/ffmpeg-backend/issues)
4. **Create Issue**: Open a new issue with detailed information

### Contributing

1. Read the [Main README](../README.md) for development setup
2. Review the [Architecture](./architecture/system-architecture.md) to understand the system
3. Follow code quality guidelines (Black, Ruff, mypy)
4. Write tests for new features
5. Update documentation as needed

## Additional Resources

### External Documentation

- **FFmpeg**: https://ffmpeg.org/documentation.html
- **FastAPI**: https://fastapi.tiangolo.com/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Redis**: https://redis.io/docs/
- **RQ**: https://python-rq.org/docs/
- **SQLAlchemy**: https://docs.sqlalchemy.org/

### Tools & Libraries

- **Swagger UI**: http://localhost:8000/docs (when running locally)
- **ReDoc**: http://localhost:8000/redoc (when running locally)
- **Health Endpoint**: http://localhost:8000/api/v1/health

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2024-01 | Initial release |

---

**Last Updated**: January 2024
**Maintainer**: Delicious Lotus Team
**License**: MIT
