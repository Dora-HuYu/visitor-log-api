from datetime import datetime
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from plates import is_valid_singapore_plate

app = FastAPI(title="Visitor Log API")
singapore_timezone = ZoneInfo("Asia/Singapore")


class VisitorCreate(BaseModel):
    """Fields supplied when registering a visitor."""

    name: str = Field(min_length=1)
    unit_number: str = Field(min_length=1)
    vehicle_plate: str | None = None


class Visitor(VisitorCreate):
    """Visitor record with a system-generated ID and timestamps."""

    id: UUID
    check_in_at: datetime
    check_out_at: datetime | None = None


# Store records in memory by ID for direct lookup during checkout.
# Records are cleared when the server restarts.
visitors: dict[UUID, Visitor] = {}


@app.get("/health")
def health_check():
    """Check that the API is running."""
    return {"status": "ok"}


@app.post("/visitors", response_model=Visitor, status_code=201)
async def register_visitor(request: VisitorCreate):
    """Register a visitor and record their check-in time."""
    if not request.unit_number.startswith("#"):
        raise HTTPException(
            status_code=422,
            detail="Unit number must start with #",
        )

    vehicle_plate = request.vehicle_plate
    if vehicle_plate is not None:
        # Treat inputs such as "sba 1234 g" and "SBA1234G" as the same plate.
        vehicle_plate = "".join(vehicle_plate.split()).upper()

        # Validate both the plate format and its final check letter.
        if not is_valid_singapore_plate(vehicle_plate):
            raise HTTPException(
                status_code=422,
                detail="Invalid Singapore vehicle plate",
            )

        # A missing checkout timestamp means the vehicle is still on site.
        if any(
            visitor.vehicle_plate == vehicle_plate
            and visitor.check_out_at is None
            for visitor in visitors.values()
        ):
            raise HTTPException(
                status_code=409,
                detail="Vehicle is already checked in",
            )

    visitor = Visitor(
        id=uuid4(),
        name=request.name,
        unit_number=request.unit_number,
        vehicle_plate=vehicle_plate,
        check_in_at=datetime.now(singapore_timezone),
    )
    visitors[visitor.id] = visitor
    return visitor


@app.post("/visitors/{visitor_id}/checkout", response_model=Visitor)
async def checkout_visitor(visitor_id: UUID):
    """Record a visitor's checkout time using their visit ID."""
    visitor = visitors.get(visitor_id)
    if visitor is None:
        raise HTTPException(status_code=404, detail="Visitor not found")

    # Keep the original checkout time if the same request is submitted again.
    if visitor.check_out_at is not None:
        raise HTTPException(status_code=409, detail="Visitor already checked out")

    visitor.check_out_at = datetime.now(singapore_timezone)
    return visitor


@app.get("/visitors", response_model=list[Visitor])
async def list_today_visitors(
    unit_number: str | None = None,
    vehicle_plate: str | None = None,
):
    """List visits that overlap today, with optional exact-match filters."""
    # Use midnight in Singapore to define the start of the local day.
    today_start = datetime.now(singapore_timezone).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    if unit_number is not None:
        unit_number = unit_number.strip()

    if vehicle_plate is not None:
        # Apply the same formatting used when storing the plate.
        vehicle_plate = "".join(vehicle_plate.split()).upper()

    results = []
    for visitor in visitors.values():
        # Exclude visits that ended by midnight. Overnight visits appear
        # in today's results if the visitor is still on site or left today.
        if visitor.check_out_at is not None and visitor.check_out_at <= today_start:
            continue
        if unit_number is not None and visitor.unit_number != unit_number:
            continue
        if vehicle_plate is not None and visitor.vehicle_plate != vehicle_plate:
            continue
        results.append(visitor)

    return sorted(results, key=lambda visitor: visitor.check_in_at, reverse=True)