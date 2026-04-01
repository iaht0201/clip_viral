from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from ...database import get_db
from ...models import WaitlistEntry

router = APIRouter(prefix="/waitlist", tags=["Waitlist"])

class WaitlistRequest(BaseModel):
    email: EmailStr
    notes: str = None

@router.post("/")
async def join_waitlist(req: WaitlistRequest, db: AsyncSession = Depends(get_db)):
    # Check if exists
    existing = await db.execute(select(WaitlistEntry).where(WaitlistEntry.email == req.email))
    if existing.scalar_one_or_none():
         return {"message": "Email already on waitlist"}
    
    new_entry = WaitlistEntry(email=req.email, notes=req.notes)
    db.add(new_entry)
    await db.commit()
    return {"message": "Success", "email": req.email}

@router.get("/")
async def get_waitlist(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WaitlistEntry).order_by(WaitlistEntry.created_at.desc()))
    entries = result.scalars().all()
    return {"count": len(entries), "entries": entries}
