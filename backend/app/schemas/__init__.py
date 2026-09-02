"""
schemas/__init__.py — re-exports for convenience.
"""
from .auth import (  # noqa: F401
    RegisterRequest, LoginRequest, RefreshRequest,
    TokenResponse, UserResponse, StudentResponse, MessageResponse,
)
from .common import PaginationMeta, PaginatedResponse, IDResponse  # noqa: F401
from .student import (  # noqa: F401
    DepartmentResponse, StudentSummary, StudentProfile,
    StudentUpdateRequest, ConsentUpdateRequest,
    SubjectResponse, AcademicRecordResponse,
)
from .skill import (  # noqa: F401
    SkillResponse, StudentSkillResponse, SkillGapItem,
    SkillGapResponse, CurriculumSkillResponse, SubjectWithSkillsResponse,
)
from .drive import (  # noqa: F401
    CompanyBrief, DriveResponse, DriveCreateRequest, DriveUpdateRequest,
    InterviewStageResponse, ApplicationResponse, ApplicationStudentRow,
)
from .roadmap import (  # noqa: F401
    RoadmapTaskResponse, RoadmapResponse,
    RoadmapGenerateRequest, TaskStatusUpdateRequest,
)
from .analytics import (  # noqa: F401
    PlacementStatsResponse, DeptPlacementRow, MonthlyTrendRow,
    RecruiterRow, PackageBandRow, SkillDemandRow, CurriculumGapRow,
)
from .copilot import (  # noqa: F401
    ChatMessage, ConversationResponse, ConversationSummary,
    NewMessageRequest, NewConversationRequest,
)
from .matching import JobMatchResponse, SkillMatchDetail  # noqa: F401
