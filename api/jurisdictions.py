from enum import Enum
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from .db import SessionLocal, get_db, models
from .schemas import Jurisdiction, JurisdictionClassification
from .pagination import Pagination
from .auth import apikey_auth
from .utils import joined_or_noload


class JurisdictionSegment(str, Enum):
    organizations = "organizations"


router = APIRouter()


@router.get(
    "/jurisdictions",
    response_model=Pagination.of(Jurisdiction),
    response_model_exclude_none=True,
)
async def jurisdictions(
    classification: Optional[JurisdictionClassification] = None,
    segments: List[JurisdictionSegment] = Query([]),
    db: SessionLocal = Depends(get_db),
    pagination: Pagination = Depends(Pagination),
    auth: str = Depends(apikey_auth),
):
    # TODO: remove this conversion once database is updated
    if classification == "state":
        classification = "government"
    query = db.query(models.Jurisdiction).order_by(models.Jurisdiction.name)

    # handle segments
    query = joined_or_noload(query, JurisdictionSegment.organizations, segments)

    # handle parameters
    if classification:
        query = query.filter(models.Jurisdiction.classification == classification)
    resp = pagination.paginate(query)

    # TODO: this should be removed too (see above note)
    for result in resp["results"]:
        if result.classification == "government":
            result.classification = "state"
    resp["results"] = [Jurisdiction.with_segments(r, segments) for r in resp["results"]]

    return resp