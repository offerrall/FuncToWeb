# 1.0.0:
- Real-time Output Streaming: Capture print() statements and stream them to the UI via WebSockets/SSE, so users see progress logs instead of a static loading spinner during long tasks.
- Update `FileResponse` to accept a `path` argument (e.g., `FileResponse(path="/tmp/video.mp4")`).