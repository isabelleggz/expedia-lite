"""Thin demonstration routes for backend location capabilities."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from .postcode_lookup import (
    PostcodeConfigurationError,
    PostcodeNotFoundError,
    PostcodeProviderError,
    lookup_us_postcode,
)
from .schemas import PostcodeLocationResponse


router = APIRouter(prefix="/api/demo")


@router.get("/zip-location", response_model=PostcodeLocationResponse)
def get_demo_zip_location(
    postcode: Annotated[
        str,
        Query(pattern=r"^\d{5}$", description="Five-digit U.S. ZIP code"),
    ],
) -> PostcodeLocationResponse:
    """Resolve a five-digit U.S. ZIP without exposing provider details."""

    try:
        location = lookup_us_postcode(postcode)
    except PostcodeConfigurationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Geoapify API key is not configured",
        ) from None
    except PostcodeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ZIP code {postcode} could not be resolved",
        ) from None
    except PostcodeProviderError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Location provider request failed",
        ) from None

    return PostcodeLocationResponse.model_validate(location)
