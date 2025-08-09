from pydantic import BaseModel
from typing import Optional


# Schema for a user's basic info, only sending what's needed.
class LeaderboardUser(BaseModel):
    name: str
    last_name: str

    class Config:
        from_attributes = True


# Schema for a student entry in the leaderboard.
class LeaderboardStudentEntry(BaseModel):
    rank: int
    student: LeaderboardUser
    score: int


# Schema for a project entry in the leaderboard.
class LeaderboardProjectEntry(BaseModel):
    id: int
    project_name: str
    author: LeaderboardUser
    star_count: int

    class Config:
        from_attributes = True
