"""Pydantic request/response models for the API"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    pending = "pending"
    downloading = "downloading"
    completed = "completed"
    failed = "failed"
    paused = "paused"


# --- Search ---

class MangaResult(BaseModel):
    id: str
    title: str
    englishTitle: Optional[str] = None
    coverUrl: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    author: list[str] = []
    tags: list[str] = []


class ChapterInfo(BaseModel):
    id: str
    number: str
    type: str = "Chapter"


class SearchResponse(BaseModel):
    results: list[MangaResult]


class ChapterListResponse(BaseModel):
    seriesId: str
    chapters: list[ChapterInfo]


# --- Download Queue ---

class AddToQueueRequest(BaseModel):
    seriesId: str
    mangaTitle: str
    chapters: list[str]  # chapter IDs to download


class DownloadTaskResponse(BaseModel):
    id: str
    mangaId: str
    mangaTitle: str
    chapterId: str
    chapterNumber: str
    status: TaskStatus
    progress: float = 0
    totalPages: int = 0
    downloadedPages: int = 0
    error: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime


class QueueResponse(BaseModel):
    tasks: list[DownloadTaskResponse]
    isRunning: bool
    totalTasks: int
    completedTasks: int
    failedTasks: int


# --- Library ---

class LibrarySeriesResponse(BaseModel):
    id: str
    title: str
    coverUrl: Optional[str] = None
    totalChapters: int
    path: str


class LibraryChapterResponse(BaseModel):
    id: str
    number: str
    filename: str
    totalPages: int
    path: str


class PageListResponse(BaseModel):
    pages: list[str]
    totalPages: int


# --- Config ---

class ConfigResponse(BaseModel):
    outputDir: str
    latest: bool
    sequence: bool
    zip: bool
    verbose: bool
    useEnglishTitle: bool
    comicinfo: bool
    rlc: int
    maxSleep: int
    maxRetries: int
    parallelWorkers: int
    libraryPaths: list[str]
    checkInterval: int


class ConfigUpdateRequest(BaseModel):
    outputDir: Optional[str] = Field(None, description="Output directory for downloads")
    latest: Optional[bool] = None
    sequence: Optional[bool] = None
    zip: Optional[bool] = None
    verbose: Optional[bool] = None
    useEnglishTitle: Optional[bool] = None
    comicinfo: Optional[bool] = None
    rlc: Optional[int] = Field(None, ge=1, le=1000, description="Rate limit count (chapters)")
    maxSleep: Optional[int] = Field(None, ge=0, le=3600, description="Max sleep time (seconds)")
    maxRetries: Optional[int] = Field(None, ge=0, le=100, description="Max retries per image")
    parallelWorkers: Optional[int] = Field(None, ge=1, le=200, description="Parallel download workers")
    libraryPaths: Optional[list[str]] = Field(None, description="Additional library directories to scan")
    checkInterval: Optional[int] = Field(None, ge=0, le=1440, description="Auto-check interval for tracked manga (minutes, 0=disabled)")

    @field_validator("outputDir")
    @classmethod
    def validate_output_dir(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        
        # Prevent absolute paths to sensitive areas or obvious traversal
        # We can't easily use resolve_safe_path here without knowing the root, 
        # but we can prevent some obvious bad ones.
        v = v.strip()
        if not v:
            raise ValueError("outputDir cannot be empty")
            
        # Basic traversal check
        if ".." in v:
            raise ValueError("outputDir cannot contain path traversal sequences")
            
        return v


# --- Stats ---

# --- External Server ---

class ExternalServerConfigResponse(BaseModel):
    url: str
    apiKey: str
    libraryId: str


class ExternalServerConfigUpdateRequest(BaseModel):
    url: Optional[str] = None
    apiKey: Optional[str] = None
    libraryId: Optional[str] = None


class StatsResponse(BaseModel):
    totalSeries: int
    totalChapters: int
    storageUsed: str
    queueActive: int
    queueCompleted: int
    queueFailed: int


# --- Logs ---

class LogEntryResponse(BaseModel):
    id: str
    timestamp: datetime
    level: str
    message: str
    source: Optional[str] = None
