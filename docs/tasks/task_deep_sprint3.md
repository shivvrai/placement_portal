# 🧑‍💻 Deep's Task Sheet (Sprint 3) — Real-Time WebSocket Engine, Security Hardening, Observability & Admin Panel

> **Role:** Infrastructure & Security Engineer
> **Priority:** 🔴 P0
> **Reference Standard:** LinkedIn Talent Insights, NIST SP 800-53, iCIMS, Taleo

---

## 📋 Industrial Context — Why This Sprint Matters

Sprint 1 built the core. Sprint 2 hardened Docker & audit trails. Sprint 3 turns CCIP into a **live, reactive, production-secure platform**:

- Students currently have no idea when they are shortlisted — they must manually refresh. Industrial portals push real-time updates.
- There is no protection against a student accessing another student's data by crafting a raw API request with someone else's UUID — a critical security vulnerability.
- There is no request tracing. If an API call takes 8 seconds, nobody knows.
- There is no admin control panel to manage users, settings, or system health.

---

## TASK 1: Full-Duplex WebSocket Real-Time Notification Engine

### Architecture Overview
```
Student Browser ──── ws://host/ws/{user_id}?token=<jwt>
                              │
                     FastAPI WebSocket Handler
                              │
                     Redis Pub/Sub  (channel: notif:{user_id})
                              │
         TPO action → NotificationService.publish() → Redis PUBLISH
```

### 1A. Database Model: `backend/app/models/notification.py`

Create SQLAlchemy model:

```python
class Notification(Base):
    __tablename__ = "notifications"
    id: UUID  PK
    user_id: UUID  FK→users.id  indexed
    type: str  # APPLICATION_STATUS | DRIVE_OPEN | OFFER_RECEIVED | DRIVE_REMINDER | ASSESSMENT_RESULT | SYSTEM
    title: str(300)
    message: str Text
    link: str(500) | None    # frontend route to navigate to on click
    priority: str default="normal"   # low | normal | high | critical
    is_read: bool default=False  indexed
    metadata: JSONB
    created_at: datetime default=utcnow  indexed
```

Add alembic migration. Import in `main.py`.

### 1B. Service: `backend/app/services/notification_service.py`

```python
class NotificationService:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis): ...

    async def publish(self, user_id, type, title, message, link=None, priority="normal", metadata={}) -> Notification:
        # 1. INSERT row into notifications table
        # 2. PUBLISH json to Redis channel "notif:{user_id}"
        # 3. If priority == "critical" → log to audit trail too
        # Returns the created Notification ORM object

    async def get_notifications(self, user_id, unread_only=False, page=1, page_size=20) -> tuple[list, int]:
        # Paginated fetch. Unread first (ORDER BY is_read ASC, created_at DESC)

    async def mark_read(self, notification_id: UUID, user_id: UUID) -> None: ...
    async def mark_all_read(self, user_id: UUID) -> None: ...
    async def get_unread_count(self, user_id: UUID) -> int: ...
    async def delete_notification(self, notification_id: UUID, user_id: UUID) -> None: ...

    async def notify_eligible_students_new_drive(self, drive, db) -> int:
        # Query all students matching drive's dept + CGPA criteria
        # Publish DRIVE_OPEN notification to each in batches of 50
        # Returns count of students notified
```

### 1C. API: `backend/app/api/v1/notifications.py`

```
GET  /notifications                    → paginated inbox (query: unread_only, page, page_size)
POST /notifications/{id}/read          → mark one read
POST /notifications/read-all           → mark all read
GET  /notifications/unread-count       → {count: N}  (fast, for badge)
DELETE /notifications/{id}             → delete notification
```

All endpoints: `current_user` via JWT. Students can only see their own notifications.

### 1D. WebSocket Endpoint: `backend/app/api/v1/websocket.py`

```python
@router.websocket("/ws/{user_id}")
async def ws_endpoint(user_id: str, websocket: WebSocket, token: str = Query(...)):
    """
    1. Validate JWT from ?token param. Close with 4001 if invalid.
    2. Verify token.sub == user_id (users can't subscribe to other users' channels). Close 4003 if mismatch.
    3. Accept connection, register with ConnectionManager
    4. Start two async tasks:
       a) redis_listener: subscribe to "notif:{user_id}", forward JSON frames to WS
       b) keepalive: send {"type":"ping"} every 25s
    5. Wait for WebSocketDisconnect, then cancel both tasks cleanly
    """
```

ConnectionManager class: thread-safe dict `user_id → list[WebSocket]`, `send_to_user()` method.

Include this router in `main.py` at root level (no `/api/v1` prefix — WS is at `/ws/{user_id}`).

### 1E. Trigger Points — Inject `notification_service.publish()` calls

| File | Trigger | Notification |
|---|---|---|
| `drives.py` PATCH status → shortlisted | After db commit | "🎉 Shortlisted for {company}" |
| `drives.py` PATCH status → selected | After db commit | "🏆 Offer: ₹{ctc}L from {company}" |
| `drives.py` PATCH status → rejected | After db commit | "Application update from {company}" |
| `drives.py` POST create drive | After db commit, background task | Notify all eligible students |
| `assessments.py` POST submit | score ≥ 85 | "🎯 Top scorer! Roadmap updated" |

### 1F. Frontend: `frontend/src/hooks/useWebSocket.js`

Custom React hook:
```js
export function useWebSocket(onMessage) {
  // Build URL: ws(s)://API_HOST/ws/{user_id}?token={jwt_from_localStorage}
  // Connect on mount, cleanup on unmount
  // Auto-reconnect with exponential backoff: 500ms → 1s → 2s → 4s → 8s → 30s cap
  // On message: parse JSON, call onMessage(payload)
  // Return: { connected: bool }
}
```

### 1G. Frontend: `frontend/src/components/NotificationBell.jsx`

Full production notification bell:
- 🔔 icon in navbar. Fetches `/notifications/unread-count` on mount.
- Red badge with count (disappears when 0). Animates (pulse) when count changes.
- Click → dropdown panel, 320px wide, max-height 480px, scrollable.
- Two tabs: "All" | "Unread (N)"
- Each item: colored left border by priority (green=normal, orange=high, red=critical), emoji icon by type, title bold, message truncated 2 lines, time-ago label.
- Click item → navigate to `notification.link`, mark as read, remove unread badge.
- "Mark all read" button. "View all →" link to `/student/notifications`.
- WebSocket integration: on new message → shake bell animation (CSS keyframes), prepend item with "● NEW" badge.
- Optimistic read marking (immediate UI update, API call in background).

### 1H. Frontend: `frontend/src/pages/student/Notifications.jsx`

Full inbox page:
- Header: "Notification Inbox" + unread count badge
- Filter bar: All / Unread / Application Updates / Drive Alerts / Assessments
- Notification list: same card style as bell dropdown but full-width
- Bulk actions: "Select all" → "Mark read" / "Delete selected"
- Infinite scroll or pagination (20 per page, Load More button)
- Empty state: 🔕 "All caught up! No notifications yet."

---

## TASK 2: Row-Level Security (RLS) Middleware

### 2A. `backend/app/middleware/rls.py`

```python
from starlette.middleware.base import BaseHTTPMiddleware

STUDENT_BLOCKED_PATH_PATTERNS = [
    r"/students/(?P<student_id>[^/]+)$",    # GET /students/{id} — TPO only
    r"/applications/(?P<app_id>[^/]+)$",
]

class RowLevelSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Try to decode JWT from Authorization header (don't raise if missing)
        # 2. If decoded and role=="student":
        #    - Extract any UUID path segments
        #    - If any path segment looks like a UUID and != current_user.id → 403
        # 3. Log blocked attempts to AuditLog as UNAUTHORIZED_ACCESS_ATTEMPT
        # 4. call_next otherwise
```

### 2B. Rate Limiting — `backend/app/middleware/rate_limit.py`

Install `slowapi`. Apply limits:

```python
# requirements.txt: add slowapi
limiter = Limiter(key_func=get_remote_address)

@router.post("/auth/login")
@limiter.limit("10/minute")
async def login(...): ...

@router.post("/auth/register")
@limiter.limit("5/minute")
async def register(...): ...

@router.post("/assessments/start")
@limiter.limit("20/hour")
async def start_assessment(...): ...

@router.post("/copilot/conversations/{id}/messages")
@limiter.limit("30/hour")
async def send_message(...): ...
```

### 2C. CORS Hardening in `backend/app/main.py`

```python
origins = settings.CORS_ORIGINS.split(",") if settings.ENVIRONMENT == "production" else ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, ...)
```

### 2D. X-Request-ID Middleware

Every response must have `X-Request-ID: <uuid8>` and `X-Response-Time: <N>ms` headers. Implement in `backend/app/middleware/timing.py`. Log every request as structured JSON.

---

## TASK 3: Structured Logging & Health Endpoints

### 3A. `backend/app/core/logging_config.py`

```python
# Install: structlog
# Every log line → JSON: {timestamp, level, message, request_id, user_id, endpoint, latency_ms}
# Replace ALL print() calls in services/ with logger.info/warning/error
```

### 3B. Enhanced Health Endpoints

```python
GET /health → {status, version, uptime_seconds, db: {connected, latency_ms}, redis: {connected, latency_ms}}
GET /health/ready → 200 OK only when DB + Redis both respond in <200ms, else 503
```

---

## TASK 4: Admin Super Panel

### 4A. Backend: `backend/app/api/v1/admin.py`

All endpoints require `role == "admin"`. All mutating endpoints write to audit log.

```
GET  /admin/users                    → paginated user list + filters (role, active, dept, created)
PATCH /admin/users/{id}/role         → change user role
PATCH /admin/users/{id}/status       → toggle active/inactive
POST  /admin/users/bulk-import       → CSV upload → create student accounts (return success/fail per row)
GET  /admin/settings                 → platform key-value settings
PATCH /admin/settings                → update settings
GET  /admin/metrics/summary          → {total_users, active_students, drives_open, applications_today, error_rate_24h}
```

### 4B. Frontend: `frontend/src/pages/admin/AdminDashboard.jsx`
- System health card (polls `/health` every 30s, shows DB/Redis latency gauges)
- KPI row: Total Users, Active Students, Open Drives, Applications Today
- Audit event live feed (last 10 events, auto-refreshes every 10s)
- Error rate sparkline chart (last 24h, from SLOW_QUERY audit events)

### 4C. Frontend: `frontend/src/pages/admin/UserManagement.jsx`
- Full user table: avatar initials, name, email, role badge, active toggle, created_at
- Actions per row: Edit role, Deactivate, Reset password
- Bulk import: drag-drop CSV upload, preview table (20 rows max), "Import N students" button, progress + error report
- Filters: role dropdown, active toggle, date range picker
- Search by name/email

### 4D. Frontend: `frontend/src/pages/admin/SystemSettings.jsx`
- Academic Year field
- CGPA floor (global default)
- Notification templates (text areas per notification type)
- Student self-registration toggle
- Institution branding: logo upload, primary color picker (updates CSS variable)
- Save → PATCH /admin/settings → show success toast

### 4E. Routing
Add `/admin/*` routes in `App.jsx` behind an `AdminRoute` guard (role === "admin" or redirect to `/`).

---

## Verification Checklist

- [ ] WebSocket tab in browser dev tools shows live connection to `/ws/{user_id}`
- [ ] TPO shortlisting a student → student bell shakes and badge increments within 2 seconds
- [ ] `GET /api/v1/students/{other_student_uuid}` as a student → 403 (not 200)
- [ ] `POST /auth/login` 11 times → 11th returns 429
- [ ] Every API response has `X-Request-ID` and `X-Response-Time` headers
- [ ] `GET /health` shows real DB and Redis latency numbers
- [ ] Admin panel shows correct user counts
- [ ] Bulk CSV import creates student accounts and returns per-row status
- [ ] Notification inbox page shows paginated history
- [ ] Mark-all-read clears badge immediately (optimistic update)
