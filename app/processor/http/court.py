import random
from datetime import date, datetime
from typing import Optional, Sequence

from fastapi import APIRouter, Depends, responses
from pydantic import BaseModel, NaiveDatetime

import app.const as const
import app.exceptions as exc
import app.persistence.database as db
from app.base import do, enums, vo
from app.middleware.headers import get_auth_token
from app.utils import Response, context, invitation_code

router = APIRouter(
    tags=['Court'],
    default_response_class=responses.JSONResponse,
)


class BrowseReservationParameters(BaseModel):
    time_ranges: Sequence[vo.DateTimeRange] | None = None
    start_date: date | None = None


class BrowseReservationOutput(BaseModel):
    start_date: date
    reservations: Sequence[do.Reservation]


@router.post('/court/{court_id}/reservation/browse')
async def browse_reservation_by_court_id(court_id: int, params: BrowseReservationParameters) -> Response:
    """
    這隻 func 如果給了 start_date 會直接 return start_date ~ start_date + 7 的資料，
    要透過 time range 搜尋的話要給 start_date = null

    time format 要給 naive datetime, e.g. `2023-11-11T11:11:11`
    """
    court = await db.court.read(court_id=court_id)
    business_hours = await db.business_hour.browse(
        place_type=enums.PlaceType.venue,
        place_id=court.venue_id,
    )
    if not business_hours:
        raise exc.NotFound

    if not params.start_date and not params.time_ranges:
        params.start_date = datetime.now().date()

    reservations = await db.reservation.browse(
        court_id=court_id,
        time_ranges=params.time_ranges,
        start_date=params.start_date,
    )
    if params.start_date:
        return Response(
            data=BrowseReservationOutput(
                reservations=reservations,
                start_date=params.start_date,
            ),
        )

    available_date = None
    is_available = True

    for time_range in params.time_ranges:
        for reservation in reservations:
            if reservation.start_time <= time_range.start_time \
                    and reservation.end_time >= time_range.end_time\
                    and not reservation.vacancy:
                is_available = False
        if is_available:
            available_date = time_range.start_time.date()
            break

    if not available_date:
        raise exc.NotFound  # TODO: ask pm/designer not found's behavior

    reservations = await db.reservation.browse(
        court_id=court_id,
        start_date=available_date,
    )
    return Response(
        data=BrowseReservationOutput(
            reservations=reservations,
            start_date=available_date,
        ),
    )


class AddReservationInput(BaseModel):
    court_id: int
    start_time: NaiveDatetime
    end_time: NaiveDatetime
    technical_level: Sequence[enums.TechnicalType] = []
    remark: Optional[str]
    member_count: int
    vacancy: int = -1
    member_id: Sequence[int] = []


class AddReservationOutput(BaseModel):
    id: int


@router.post('/court/{court_id}/reservation')
async def add_reservation(data: AddReservationInput, _=Depends(get_auth_token)) -> Response[AddReservationOutput]:
    if context.account.id not in data.member_id:
        raise exc.NoPermission

    reservations = await db.reservation.browse(
        court_id=data.court_id,
        time_ranges=[vo.DateTimeRange(
            start_time=data.start_time,
            end_time=data.end_time,
        )],
    )

    if reservations:
        raise exc.CourtReserved

    if data.start_time < datetime.now() or data.start_time >= data.end_time:
        raise exc.IllegalInput

    invite_code = invitation_code.generate()
    court = await db.court.read(court_id=data.court_id)
    venue = await db.venue.read(venue_id=court.venue_id)

    reservation_id = await db.reservation.add(
        court_id=data.court_id,
        venue_id=venue.id,
        stadium_id=venue.stadium_id,
        start_time=data.start_time,
        end_time=data.end_time,
        technical_level=data.technical_level,
        invitation_code=invite_code,
        remark=data.remark,
        member_count=data.member_count,
        vacancy=data.vacancy,
    )
    return Response(data=AddReservationOutput(id=reservation_id))