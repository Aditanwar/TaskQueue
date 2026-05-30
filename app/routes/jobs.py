from fastapi import APIRouter, HTTPException, status
from redis.exceptions import ConnectionError as RedisConnectionError
from app.schemas.job import (
    JobSubmissionRequest,
    JobSubmissionResponse,
    JobStatusResponse,
    JobResultResponse,
)
from app.services.queue_service import QueueService

router = APIRouter(prefix="/jobs", tags=["Jobs Management"])


@router.post(
    "",
    response_model=JobSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a background processing job",
    description="Validates the payload and queues the job in Redis for asynchronous worker execution."
)
async def submit_job(request: JobSubmissionRequest):
    try:
        job_id = QueueService.submit_job(request.job_type, request.payload)
        return JobSubmissionResponse(job_id=job_id, status="queued")
    except RedisConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Queue broker (Redis) is currently unreachable. Error: {str(e)}"
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while scheduling: {str(ex)}"
        )


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get job execution status and progress",
    description="Polls the Celery backend database to fetch the job state and real-time execution progress."
)
async def get_job_status(job_id: str):
    try:
        status_info = QueueService.get_job_status(job_id)
        return JobStatusResponse(**status_info)
    except RedisConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Queue backend (Redis) is unreachable. Error: {str(e)}"
        )
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query job state: {str(ex)}"
        )


@router.get(
    "/{job_id}/result",
    response_model=JobResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the final output result of a completed job",
    description="Returns the processed metadata and outputs if the job has successfully finished execution."
)
async def get_job_result(job_id: str):
    try:
        status_info = QueueService.get_job_status(job_id)
        
        if status_info["status"] == "failed":
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=f"Job failed during execution. Error metadata: {status_info['result']}"
            )
        
        if status_info["status"] != "completed":
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail="Job is still executing or queued. Please poll status endpoint first."
            )

        result_data = QueueService.get_job_result(job_id)
        return JobResultResponse(job_id=job_id, result=result_data)
    except HTTPException:
        raise
    except RedisConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Result store (Redis) is unreachable. Error: {str(e)}"
        )
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve task result: {str(ex)}"
        )
