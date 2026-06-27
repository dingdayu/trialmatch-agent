"""全局枚举定义 — 对应技术设计文档第 3.7 节"""

from enum import Enum


class UserRole(str, Enum):
    """用户角色"""
    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    CRC = "crc"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    """用户状态"""
    ACTIVE = "active"
    DISABLED = "disabled"


class ProjectStatus(str, Enum):
    """项目状态"""
    DRAFT = "draft"
    CONFIGURING = "configuring"
    SCREENING = "screening"
    PAUSED = "paused"
    COMPLETED = "completed"


class CriterionType(str, Enum):
    """入排标准类型"""
    INCLUSION = "inclusion"
    EXCLUSION = "exclusion"


class ScreeningStatus(str, Enum):
    """受试者筛选状态"""
    PENDING = "pending"
    SCREENING = "screening"
    COMPLETED = "completed"
    FAILED = "failed"


class OverallResult(str, Enum):
    """总体结论"""
    RECOMMENDED = "recommended"
    EXCLUDED = "excluded"
    MANUAL_REVIEW = "manual_review"
    INSUFFICIENT_DATA = "insufficient_data"


class AIResult(str, Enum):
    """单条标准 AI 匹配结果"""
    PASS = "pass"
    FAIL = "fail"
    EXCLUSION_HIT = "exclusion_hit"
    EXCLUSION_NOT_HIT = "exclusion_not_hit"
    INSUFFICIENT_DATA = "insufficient_data"
    MANUAL_REVIEW = "manual_review"


class ReviewStatus(str, Enum):
    """人工复核状态"""
    PENDING = "pending"
    REVIEWED = "reviewed"
    MODIFIED = "modified"


class FileType(str, Enum):
    """文件类型"""
    PROTOCOL = "protocol"
    ICF = "icf"
    MEDICAL_RECORD = "medical_record"
    LAB_REPORT = "lab_report"
    IMAGING = "imaging"
    OTHER = "other"


class FileScope(str, Enum):
    """文件所属范围"""
    PROJECT_PROTOCOL = "project_protocol"
    SUBJECT_DATA = "subject_data"


class ParseStatus(str, Enum):
    """文件解析状态"""
    PENDING = "pending"
    PARSING = "parsing"
    COMPLETED = "completed"
    FAILED = "failed"


class RunStatus(str, Enum):
    """AI 分析任务状态"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ActionType(str, Enum):
    """审计操作类型"""
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    SCREENING_START = "screening_start"
    SCREENING_COMPLETE = "screening_complete"
    MANUAL_REVIEW = "manual_review"
    BATCH_REVIEW = "batch_review"
    CONFIRM_ALL = "confirm_all"
    EXPORT = "export"


class TargetType(str, Enum):
    """审计目标类型"""
    PROJECT = "project"
    CRITERION = "criterion"
    SUBJECT = "subject"
    FILE = "file"
    EVALUATION = "evaluation"
    SCREENING_RUN = "screening_run"
    USER = "user"
