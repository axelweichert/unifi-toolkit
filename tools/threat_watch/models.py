"""
Pydantic models for Threat Watch API requests and responses
"""
from pydantic import BaseModel, Field, field_serializer
from typing import Optional, List
from datetime import datetime, timezone


def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Serialize datetime to ISO format string with UTC timezone indicator"""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt_utc = dt.astimezone(timezone.utc)
        return dt_utc.isoformat().replace('+00:00', 'Z')
    return dt.isoformat() + 'Z'


# Threat Event Models

class ThreatEventResponse(BaseModel):
    """Response model for a single threat event"""
    id: int
    unifi_event_id: str
    timestamp: datetime
    signature: Optional[str]
    signature_id: Optional[int]
    severity: Optional[int]
    category: Optional[str]
    action: Optional[str]
    message: Optional[str]

    # Network
    src_ip: Optional[str]
    src_port: Optional[int]
    dest_ip: Optional[str]
    dest_port: Optional[int]
    protocol: Optional[str]
    app_protocol: Optional[str]

    # Geo - Source
    src_country: Optional[str]
    src_city: Optional[str]
    src_org: Optional[str]

    # Geo - Destination
    dest_country: Optional[str]
    dest_city: Optional[str]
    dest_org: Optional[str]

    @field_serializer('timestamp')
    def serialize_dt(self, dt: Optional[datetime], _info) -> Optional[str]:
        return serialize_datetime(dt)

    class Config:
        from_attributes = True


class ThreatEventDetail(BaseModel):
    """Detailed response model for a single threat event (includes all fields)"""
    id: int
    unifi_event_id: str
    flow_id: Optional[str]
    timestamp: datetime

    # Alert info
    signature: Optional[str]
    signature_id: Optional[int]
    severity: Optional[int]
    category: Optional[str]
    action: Optional[str]
    message: Optional[str]

    # Network
    src_ip: Optional[str]
    src_port: Optional[int]
    src_mac: Optional[str]
    dest_ip: Optional[str]
    dest_port: Optional[int]
    dest_mac: Optional[str]
    protocol: Optional[str]
    app_protocol: Optional[str]
    interface: Optional[str]

    # Geo - Source
    src_country: Optional[str]
    src_city: Optional[str]
    src_latitude: Optional[float]
    src_longitude: Optional[float]
    src_asn: Optional[str]
    src_org: Optional[str]

    # Geo - Destination
    dest_country: Optional[str]
    dest_city: Optional[str]
    dest_latitude: Optional[float]
    dest_longitude: Optional[float]
    dest_asn: Optional[str]
    dest_org: Optional[str]

    # Meta
    site_id: Optional[str]
    archived: bool
    fetched_at: datetime

    @field_serializer('timestamp', 'fetched_at')
    def serialize_dt(self, dt: Optional[datetime], _info) -> Optional[str]:
        return serialize_datetime(dt)

    class Config:
        from_attributes = True


class ThreatEventsListResponse(BaseModel):
    """Response model for list of threat events"""
    events: List[ThreatEventResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# Statistics Models

class CategoryCount(BaseModel):
    """Count of events by category"""
    category: str
    count: int


class CountryCount(BaseModel):
    """Count of events by country"""
    country: str
    country_code: Optional[str]
    count: int


class TopAttacker(BaseModel):
    """Top attacking IP with stats"""
    ip: str
    count: int
    country: Optional[str]
    org: Optional[str]
    last_seen: datetime

    @field_serializer('last_seen')
    def serialize_dt(self, dt: Optional[datetime], _info) -> Optional[str]:
        return serialize_datetime(dt)


class SeverityCount(BaseModel):
    """Count of events by severity"""
    severity: int
    label: str
    count: int


class ThreatStatsResponse(BaseModel):
    """Response model for threat statistics"""
    total_events: int
    events_24h: int
    events_7d: int
    blocked_count: int
    alert_count: int

    by_severity: List[SeverityCount]
    by_category: List[CategoryCount]
    by_country: List[CountryCount]
    top_attackers: List[TopAttacker]


class TimelinePoint(BaseModel):
    """Single point in time series"""
    timestamp: datetime
    count: int

    @field_serializer('timestamp')
    def serialize_dt(self, dt: Optional[datetime], _info) -> Optional[str]:
        return serialize_datetime(dt)


class ThreatTimelineResponse(BaseModel):
    """Response model for threat timeline"""
    interval: str  # 'hour', 'day'
    data: List[TimelinePoint]


# Filter Models

class ThreatEventFilters(BaseModel):
    """Query parameters for filtering threat events"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    severity: Optional[int] = None
    category: Optional[str] = None
    action: Optional[str] = None
    src_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    search: Optional[str] = None  # Search in signature/message
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=500)


# Status Models

class SystemStatus(BaseModel):
    """Response model for system status"""
    last_refresh: Optional[datetime]
    total_events: int
    events_24h: int
    refresh_interval_seconds: int

    @field_serializer('last_refresh')
    def serialize_dt(self, dt: Optional[datetime], _info) -> Optional[str]:
        return serialize_datetime(dt)


# Webhook Models

class WebhookCreate(BaseModel):
    """Request model for creating a webhook"""
    name: str
    webhook_type: str  # 'slack', 'discord', 'n8n'
    url: str
    min_severity: int = Field(default=2, ge=1, le=3)
    event_alert: bool = True
    event_block: bool = True
    enabled: bool = True


class WebhookUpdate(BaseModel):
    """Request model for updating a webhook"""
    name: Optional[str] = None
    url: Optional[str] = None
    min_severity: Optional[int] = Field(default=None, ge=1, le=3)
    event_alert: Optional[bool] = None
    event_block: Optional[bool] = None
    enabled: Optional[bool] = None


class WebhookResponse(BaseModel):
    """Response model for webhook information"""
    id: int
    name: str
    webhook_type: str
    url: str
    min_severity: int
    event_alert: bool
    event_block: bool
    enabled: bool
    created_at: datetime
    last_triggered: Optional[datetime] = None

    @field_serializer('created_at', 'last_triggered')
    def serialize_dt(self, dt: Optional[datetime], _info) -> Optional[str]:
        return serialize_datetime(dt)

    class Config:
        from_attributes = True


class WebhooksListResponse(BaseModel):
    """Response model for list of webhooks"""
    webhooks: List[WebhookResponse]
    total: int


# Generic Response Models

class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Generic error response"""
    error: str
    details: Optional[str] = None
