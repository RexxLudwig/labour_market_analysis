from pydantic import BaseModel, Field
from typing import Optional, List

class RelevanceResult(BaseModel):
    relevant: bool = Field(description="Whether the document is relevant to labour policies")
    issue: Optional[str] = Field(default=None, description="The identified labour market issue if relevant")
    reason: Optional[str] = Field(default=None, description="Reason for relevance classification")

class PolicyExtractionResult(BaseModel):
    country: str = Field(description="Country the policy belongs to")
    policy_title: str = Field(description="Title of the policy")
    policy_type: str = Field(description="Type of the policy (e.g., Act, Decree, Regulation)")
    status: str = Field(description="Status of the policy (e.g., Proposed, Enacted)")
    announcement_date: str = Field(description="Date the policy was announced or Unknown")
    effective_date: str = Field(description="Date the policy takes effect or Unknown")
    target_groups: List[str] = Field(description="List of target demographic or worker groups")
    policy_objective: str = Field(description="Main objective of the policy")
    key_provisions: List[str] = Field(description="List of key provisions or rules in the policy")
    implementation_agency: str = Field(description="Agency responsible for implementation")
    labour_market_issue: str = Field(description="The primary labour market issue this addresses")

class VerificationResult(BaseModel):
    verified: bool = Field(description="Whether the extraction is verified as accurate")
    confidence: str = Field(description="Confidence level: HIGH, MEDIUM, or LOW")
    issues: List[str] = Field(description="List of identified issues or discrepancies")
