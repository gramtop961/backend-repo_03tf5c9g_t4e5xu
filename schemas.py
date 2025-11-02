"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name
(e.g., Generation -> "generation").
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Literal

class Generation(BaseModel):
    """
    Stores code generations performed by the SaaS
    Collection name: "generation"
    """
    source_type: Literal['spline', 'three'] = Field('spline', description="Kind of asset used for generation")
    input_url: Optional[HttpUrl] = Field(None, description="Source URL for Spline or model JSON, if applicable")
    animation: Literal['framer', 'gsap'] = Field('framer', description="Animation library to scaffold")
    name: str = Field(..., description="Component name to generate")
    options: Optional[Dict] = Field(default_factory=dict, description="Additional generation options")
    code: str = Field(..., description="Generated component source code")
