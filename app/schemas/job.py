from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator

# Allowed job types
ALLOWED_JOB_TYPES = {"send_email", "resize_image", "process_data", "generate_report"}


class JobSubmissionRequest(BaseModel):
    job_type: str = Field(..., description="The type of job to execute")
    payload: Dict[str, Any] = Field(..., description="Key-value arguments for the job")

    @field_validator("job_type")
    @classmethod
    def validate_job_type(cls, value: str) -> str:
        if value not in ALLOWED_JOB_TYPES:
            raise ValueError(
                f"Invalid job_type '{value}'. Allowed types: {', '.join(ALLOWED_JOB_TYPES)}"
            )
        return value

    @field_validator("payload")
    @classmethod
    def validate_payload(cls, value: Dict[str, Any], info) -> Dict[str, Any]:
        # Validate based on the job_type if it is available and valid
        job_type = info.data.get("job_type")
        if not job_type:
            return value

        if job_type == "send_email":
            if "email" not in value:
                raise ValueError("Payload must contain 'email' key for send_email job.")
            if not isinstance(value["email"], str) or "@" not in value["email"]:
                raise ValueError("Payload key 'email' must be a valid email string.")

        elif job_type == "resize_image":
            # Can be simulated url or width/height
            if "width" in value and not isinstance(value["width"], int):
                raise ValueError("Payload key 'width' must be an integer.")
            if "height" in value and not isinstance(value["height"], int):
                raise ValueError("Payload key 'height' must be an integer.")

        elif job_type == "process_data":
            if "dataset_size" in value and not isinstance(value["dataset_size"], int):
                raise ValueError("Payload key 'dataset_size' must be an integer.")

        elif job_type == "generate_report":
            if "report_id" in value and not isinstance(value["report_id"], str):
                raise ValueError("Payload key 'report_id' must be a string.")

        return value


class JobSubmissionResponse(BaseModel):
    job_id: str = Field(..., description="The unique UUID assigned to the submitted job")
    status: str = Field("queued", description="Initial status of the job in queue")


class JobStatusResponse(BaseModel):
    job_id: str = Field(..., description="The unique UUID assigned to the job")
    status: str = Field(..., description="Current state: queued, processing, completed, failed")
    progress: int = Field(0, description="Execution progress percentage (0-100)")
    result: Optional[Any] = Field(None, description="Output payload of the completed task, if done")


class JobResultResponse(BaseModel):
    job_id: str = Field(..., description="The unique UUID assigned to the job")
    result: Optional[Any] = Field(None, description="The final result returned by the job execution")
