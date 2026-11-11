from datetime import datetime
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from plates import is_valid_singapore_plate

app = FastAPI(title="Visitor Log API")
singapore_timezone = ZoneInfo("Asia/Singapore")


class VisitorCreate(BaseModel):
    name: str = Field(min_length=1)
    unit_number: str = Field(min_length=1)
    vehicle_plate: str | None = None


class Visitor(VisitorCreate):
    id: UUID
    check_in_at: datetime
    check_out_at: datetime | None = None


visitors: dict[UUID, Visitor] = {}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/visitors", response_model=Visitor, status_code=201)
async def register_visitor(request: VisitorCreate):
    vehicle_plate = request.vehicle_plate
    if vehicle_plate is not None:
        vehicle_plate = "".join(vehicle_plate.split()).upper()

        if not is_valid_singapore_plate(vehicle_plate):
            raise HTTPException(
                status_code=422,
                detail="Invalid Singapore vehicle plate",
            )

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
    visitor = visitors.get(visitor_id)
    if visitor is None:
        raise HTTPException(status_code=404, detail="Visitor not found")

    if visitor.check_out_at is not None:
        raise HTTPException(status_code=409, detail="Visitor already checked out")

    visitor.check_out_at = datetime.now(singapore_timezone)
    return visitor