# TODO - Future Enhancements

## Error Handling Improvements (Post-MVP)
- [ ] Implement graceful degradation for prompt analysis failures
  - [ ] Return cached/default analysis when OpenAI is unavailable
  - [ ] Allow generation to proceed with minimal analysis when LLM fails
  - [ ] Add fallback analysis based on keyword extraction
- [ ] Add circuit breaker pattern for external service calls
- [ ] Implement progressive retry with backoff for transient failures
- [ ] Add health check endpoints for external service status
- [ ] Create user-friendly error messages for different failure scenarios

## Performance Optimizations
- [ ] Implement prompt analysis caching to avoid redundant LLM calls
- [ ] Add analysis result validation and confidence scoring
- [ ] Consider async processing for long-running analyses
- [ ] Add analysis result compression for storage efficiency
- [ ] Implement Redis locks for concurrent recomposition prevention (if concurrent edits become an issue during prototyping)
- [ ] Add Redis pub/sub for real-time recomposition progress updates (if WebSocket-only approach proves insufficient)
- [ ] **Timeline Edit Planner (PR #402) Performance**: Add Redis caching for operation plans and operation count limits IF AND ONLY IF the initial prototype has performance issues

## Monitoring & Observability
- [ ] Add structured logging for analysis performance metrics
- [ ] Implement analysis result quality tracking
- [ ] Add alerts for analysis failures or degraded performance
- [ ] Create dashboards for analysis success rates and latency

## Feature Enhancements
- [ ] Support for multi-language prompt analysis
- [ ] Add analysis result versioning for A/B testing
- [ ] Implement user feedback loop for analysis quality improvement
- [ ] Add support for custom analysis templates per industry/brand
- [ ] Multiple Replicate model support (beyond google/veo-3.1-fast)
  - [ ] Model selection logic based on video type/duration/complexity
  - [ ] Fallback model selection for rate limits/failures
  - [ ] Performance benchmarking and model comparison
  - [ ] A/B testing framework for model selection

## Non-MVP AI Backend Features (Phase 2)

# 🟣 BLOCK B: Scene Planning & Beat-Aligned Timeline (Post-MVP)
*(Beat integration and scene-time alignment)*
**Dependencies:** MVP Complete
**Parallelizable:** Yes
**Total Time:** 18–25 hours
**Status:** Phase 2 feature, not required for MVP

---

## PR #201: Audio Analysis Client (FFmpeg Consumer)  
**Time:** 4–5 hours  

### Tasks:
- [ ] Implement `AudioAnalysisService`  
- [ ] Call `/internal/v1/audio-analysis`  
- [ ] Normalize beat/downbeat/energy structure  

### Testing:
- [ ] Unit: request formatting  
- [ ] Integration: mock FFmpeg  

---

## PR #202: Beat-Aligned Scene Timing Module  
**Prerequisites:** PR #201  
**Time:** 6–7 hours  

### Tasks:
- [ ] Map scenes to downbeats  
- [ ] Snap boundaries to musical structure  
- [ ] Fallback timing if no beats  
- [ ] Add intensity/energy hints  

### Testing:
- [ ] Unit: beat snapping  
- [ ] Unit: fallback logic  
- [ ] Integration: scene plan + beat data → timeline  

---

## PR #203: Combined Ad/Music Planner Interface  
**Prerequisites:** PR #202  
**Time:** 4–6 hours  

### Tasks:
- [ ] Unified planner interface  
- [ ] Planner selection logic  
- [ ] Metrics logging and debug mode  

### Testing:
- [ ] Unit: routing logic  
- [ ] Integration: complete planner flow  

---

## BLOCK B Integration PR – PR #204  
**Time:** 3–4 hours  

### Tests:
- [ ] audio → beats → aligned scenes  
- [ ] ad planning smoke tests  

---