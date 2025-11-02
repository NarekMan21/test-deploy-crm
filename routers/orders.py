from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import List, Optional
from datetime import datetime, timezone
import json
import os
import urllib.parse
import aiofiles
from pathlib import Path

from database import get_db
from models import Order, OrderStatus, OrderEditHistory, User
from routers.auth import get_current_admin_user, get_current_logist_user, get_current_work_user, get_current_user

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Helper functions
async def log_order_change(db: AsyncSession, order_id: int, user_id: int, action: str, field_changes = None):
    history_entry = OrderEditHistory(
        order_id=order_id,
        user_id=user_id,
        action=action,
        field_changes=json.dumps(field_changes) if field_changes else None
    )
    db.add(history_entry)
    await db.commit()

async def get_next_order_number(db: AsyncSession) -> int:
    result = await db.execute(select(func.max(Order.order_number)))
    max_number = result.scalar() or 0
    return min(max_number + 1, 9999)

# Admin endpoints
@router.post("/")
async def create_order(
    customer_name: str = Form(...),
    customer_phone: str = Form(...),
    customer_address: str = Form(...),
    phone_agreement_notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    # Validate input
    customer_name = customer_name.strip()
    customer_phone = customer_phone.strip()
    customer_address = customer_address.strip()
    
    if not customer_name:
        raise HTTPException(status_code=400, detail="Customer name is required")
    if not customer_phone:
        raise HTTPException(status_code=400, detail="Customer phone is required")
    if not customer_address:
        raise HTTPException(status_code=400, detail="Customer address is required")
    
    order = Order(
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_address=customer_address,
        phone_agreement_notes=phone_agreement_notes.strip() if phone_agreement_notes else None,
        created_by=current_user.id,
        status=OrderStatus.draft
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    await log_order_change(db, order.id, current_user.id, "created")

    return {"id": order.id, "message": "Order created successfully"}

@router.get("/")
async def get_orders(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Order)

    # Filter based on user role
    if current_user.role.value == "logist":
        query = query.where(Order.status.in_([OrderStatus.confirmed, OrderStatus.ready]))
    elif current_user.role.value == "work":
        query = query.where(Order.status.in_([OrderStatus.in_progress, OrderStatus.ready]))

    if status_filter:
        query = query.where(Order.status == status_filter)

    result = await db.execute(query)
    orders = result.scalars().all()

    # Filter sensitive information for work role
    orders_data = []
    for order in orders:
        order_dict = {
            "id": order.id,
            "order_number": order.order_number,
            "customer_name": order.customer_name,
            "customer_requirements": order.customer_requirements,
            "deadline": order.deadline.isoformat() if order.deadline else None,
            "furniture_photo": order.furniture_photo,
            "material_photo": order.material_photo,
            "status": order.status.value,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
        }

        if current_user.role.value == "admin":
            order_dict.update({
                "customer_phone": order.customer_phone,
                "customer_address": order.customer_address,
                "phone_agreement_notes": order.phone_agreement_notes,
                "price": order.price,
            })
        elif current_user.role.value == "logist":
            order_dict.update({
                "customer_phone": order.customer_phone,
                "customer_address": order.customer_address,
                "phone_agreement_notes": order.phone_agreement_notes,
                "price": order.price,
            })
        # work role gets only basic info

        orders_data.append(order_dict)

    return orders_data

@router.get("/{order_id}")
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Check permissions
    if current_user.role.value == "logist" and order.status == OrderStatus.draft:
        raise HTTPException(status_code=403, detail="Access denied")
    if current_user.role.value == "work" and order.status not in [OrderStatus.in_progress, OrderStatus.ready]:
        raise HTTPException(status_code=403, detail="Access denied")

    order_dict = {
        "id": order.id,
        "order_number": order.order_number,
        "customer_name": order.customer_name,
        "customer_requirements": order.customer_requirements,
        "deadline": order.deadline.isoformat() if order.deadline else None,
        "furniture_photo": order.furniture_photo,
        "material_photo": order.material_photo,
        "status": order.status.value,
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
    }

    if current_user.role.value == "admin":
        order_dict.update({
            "customer_phone": order.customer_phone,
            "customer_address": order.customer_address,
            "phone_agreement_notes": order.phone_agreement_notes,
            "price": order.price,
        })
    elif current_user.role.value == "logist":
        order_dict.update({
            "customer_phone": order.customer_phone,
            "customer_address": order.customer_address,
            "phone_agreement_notes": order.phone_agreement_notes,
            "price": order.price,
        })
    # work role gets only basic info

    return order_dict

@router.put("/{order_id}")
async def update_order(
    order_id: int,
    customer_name: Optional[str] = Form(None),
    customer_phone: Optional[str] = Form(None),
    customer_address: Optional[str] = Form(None),
    phone_agreement_notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Admins can edit orders at any stage

    old_values = {
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "customer_address": order.customer_address,
        "phone_agreement_notes": order.phone_agreement_notes,
    }

    if customer_name is not None:
        order.customer_name = customer_name
    if customer_phone is not None:
        order.customer_phone = customer_phone
    if customer_address is not None:
        order.customer_address = customer_address
    if phone_agreement_notes is not None:
        order.phone_agreement_notes = phone_agreement_notes
    order.updated_by = current_user.id
    order.updated_at = datetime.now(timezone.utc)

    await db.commit()

    new_values = {
        "customer_name": customer_name if customer_name is not None else order.customer_name,
        "customer_phone": customer_phone if customer_phone is not None else order.customer_phone,
        "customer_address": customer_address if customer_address is not None else order.customer_address,
        "phone_agreement_notes": phone_agreement_notes if phone_agreement_notes is not None else order.phone_agreement_notes,
    }

    field_changes = {}
    for key in old_values:
        if old_values[key] != new_values[key]:
            field_changes[key] = {"old": old_values[key], "new": new_values[key]}

    if field_changes:
        await log_order_change(db, order_id, current_user.id, "updated", field_changes)

    return {"message": "Order updated successfully"}

@router.post("/{order_id}/submit")
async def submit_order_for_confirmation(
    order_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.draft:
        raise HTTPException(status_code=400, detail="Order already submitted")

    order.status = OrderStatus.pending_confirmation
    order.updated_by = current_user.id
    order.updated_at = datetime.now(timezone.utc)
    await db.commit()

    await log_order_change(db, order_id, current_user.id, "submitted_for_confirmation")

    return {"message": "Order submitted for confirmation"}

@router.post("/{order_id}/confirm")
async def confirm_order(
    order_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.pending_confirmation:
        raise HTTPException(status_code=400, detail="Order not pending confirmation")

    next_number = await get_next_order_number(db)
    order.status = OrderStatus.confirmed
    order.order_number = next_number
    order.updated_by = current_user.id
    order.updated_at = datetime.now(timezone.utc)
    await db.commit()

    await log_order_change(db, order_id, current_user.id, "confirmed", {"order_number": next_number})

    return {"message": f"Order confirmed with number {next_number}"}

# Logistics endpoints
@router.put("/{order_id}/details")
async def add_order_details(
    order_id: int,
    customer_requirements: str = Form(...),
    deadline: str = Form(...),
    price: int = Form(...),
    material_photo: UploadFile = File(None),
    furniture_photo: UploadFile = File(None),
    current_user: User = Depends(get_current_logist_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.confirmed:
        raise HTTPException(status_code=400, detail="Can only add details to confirmed orders")

    # Validate price
    if price <= 0:
        raise HTTPException(status_code=400, detail="Price must be positive")

    # Validate deadline
    try:
        # Normalize deadline format
        deadline_str = deadline.replace('Z', '+00:00') if 'Z' in deadline else deadline
        if '+' not in deadline_str and '-' not in deadline_str[-6:]:
            deadline_str += '+00:00'
        deadline_dt = datetime.fromisoformat(deadline_str)
        if deadline_dt.tzinfo is None:
            deadline_dt = deadline_dt.replace(tzinfo=timezone.utc)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid deadline format: {str(e)}")

    # Validate file types and sizes
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

    async def save_file(file: UploadFile, prefix: str) -> Optional[str]:
        if not file or not file.filename:
            return None
        
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File extension {file_ext} not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Check file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Generate safe filename
        safe_filename = file.filename.replace(' ', '_')
        safe_filename = ''.join(c if c.isalnum() or c in '._-' else '_' for c in safe_filename)
        filename = f"{order_id}_{prefix}_{safe_filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        # Save file asynchronously
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)
        
        return filename

    old_values = {
        "customer_requirements": order.customer_requirements,
        "deadline": str(order.deadline) if order.deadline else None,
        "price": order.price,
        "material_photo": order.material_photo,
        "furniture_photo": order.furniture_photo,
    }

    # Handle file uploads
    try:
        if material_photo:
            order.material_photo = await save_file(material_photo, "material")
        if furniture_photo:
            order.furniture_photo = await save_file(furniture_photo, "furniture")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    order.customer_requirements = customer_requirements
    order.deadline = deadline_dt
    order.price = price
    order.status = OrderStatus.in_progress
    order.updated_by = current_user.id
    order.updated_at = datetime.now(timezone.utc)

    await db.commit()

    new_values = {
        "customer_requirements": customer_requirements,
        "deadline": deadline,
        "price": price,
        "material_photo": order.material_photo,
        "furniture_photo": order.furniture_photo,
    }

    field_changes = {}
    for key in old_values:
        if old_values[key] != new_values[key]:
            field_changes[key] = {"old": old_values[key], "new": new_values[key]}

    if field_changes:
        await log_order_change(db, order_id, current_user.id, "details_added", field_changes)

    return {"message": "Order details added successfully"}

@router.post("/{order_id}/ready")
async def mark_order_ready(
    order_id: int,
    current_user: User = Depends(get_current_logist_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.ready:
        raise HTTPException(status_code=400, detail="Order not ready")

    order.status = OrderStatus.delivered
    order.updated_by = current_user.id
    order.updated_at = datetime.now(timezone.utc)
    await db.commit()

    await log_order_change(db, order_id, current_user.id, "delivered")

    return {"message": "Order marked as delivered"}

# Workshop endpoints
@router.post("/{order_id}/complete")
async def complete_order(
    order_id: int,
    current_user: User = Depends(get_current_work_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.in_progress:
        raise HTTPException(status_code=400, detail="Order not in progress")

    order.status = OrderStatus.ready
    order.updated_by = current_user.id
    order.updated_at = datetime.now(timezone.utc)
    await db.commit()

    await log_order_change(db, order_id, current_user.id, "completed")

    return {"message": "Order marked as ready"}

# Get order history
@router.get("/{order_id}/history")
async def get_order_history(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check if order exists and user has access
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    result = await db.execute(
        select(OrderEditHistory, User.username)
        .join(User, OrderEditHistory.user_id == User.id)
        .where(OrderEditHistory.order_id == order_id)
        .order_by(OrderEditHistory.timestamp.desc())
    )
    history = result.all()

    return [
        {
            "timestamp": entry.OrderEditHistory.timestamp.isoformat(),
            "user": entry.username,
            "action": entry.OrderEditHistory.action,
            "field_changes": json.loads(entry.OrderEditHistory.field_changes) if entry.OrderEditHistory.field_changes else None,
        }
        for entry in history
    ]