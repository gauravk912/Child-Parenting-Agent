from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.child import Child
from app.models.user import User
from app.schemas.child import ChildCreate, ChildResponse, ChildUpdate
from app.services.graph_memory_service import (
    create_child_profile_node,
    update_child_profile_node,
    delete_child_profile_node,
)

router = APIRouter(prefix="/children", tags=["children"])


@router.post("", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
def create_child(
    payload: ChildCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    child = Child(
        **payload.model_dump(),
        parent_id=current_user.id,
    )
    db.add(child)
    db.commit()
    db.refresh(child)

    create_child_profile_node(
        child_id=child.id,
        child_name=child.name,
        parent_id=child.parent_id,
    )

    return child


@router.get("/{child_id}", response_model=ChildResponse)
def get_child(
    child_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    child = (
        db.query(Child)
        .filter(Child.id == child_id, Child.parent_id == current_user.id)
        .first()
    )
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    return child


@router.get("", response_model=list[ChildResponse])
def list_children(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Child).filter(Child.parent_id == current_user.id).all()


@router.put("/{child_id}", response_model=ChildResponse)
def update_child(
    child_id: UUID,
    payload: ChildUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    child = (
        db.query(Child)
        .filter(Child.id == child_id, Child.parent_id == current_user.id)
        .first()
    )
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(child, key, value)

    db.commit()
    db.refresh(child)

    update_child_profile_node(
        child_id=child.id,
        child_name=child.name,
    )

    return child


@router.delete("/{child_id}")
def delete_child(
    child_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    child = (
        db.query(Child)
        .filter(Child.id == child_id, Child.parent_id == current_user.id)
        .first()
    )
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    db.delete(child)
    db.commit()

    delete_child_profile_node(child_id)

    return {"message": "Child deleted successfully"}