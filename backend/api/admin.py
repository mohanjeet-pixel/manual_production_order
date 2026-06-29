import io

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File

from backend.schemas.response import StandardResponse
from backend.schemas.admin import (
    UserCreate, UserUpdate, PasswordReset,
    MatrixCreate, MatrixUpdate,
)
from backend.dependencies.auth import require_admin, CurrentUser
from backend.repositories.user_repository import (
    get_all_users, create_user, update_user, deactivate_user,
)
from backend.repositories.admin_repository import (
    get_matrix, create_matrix_entry, update_matrix_entry,
    get_audit_logs, replace_products,
)
from backend.core.security import hash_password
from backend.repositories.audit_repository import log_action

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Users ─────────────────────────────────────────────────────

@router.get("/users", response_model=StandardResponse)
def list_users(
    include_inactive: bool = False,
    _: CurrentUser = Depends(require_admin),
):
    users = get_all_users(include_inactive=include_inactive)
    return StandardResponse(success=True, message=f"{len(users)} users", data=users)


@router.post("/users", response_model=StandardResponse)
def add_user(body: UserCreate, admin: CurrentUser = Depends(require_admin)):
    if body.role not in ("OPERATOR", "MANAGER", "ADMIN"):
        raise HTTPException(400, "role must be OPERATOR, MANAGER, or ADMIN")
    hashed = hash_password(body.password)
    create_user(body.employee_id, hashed, body.full_name, body.email, body.department, body.role)
    log_action("USER_CREATED", employee_id=admin.employee_id, entity="USER",
               entity_id=body.employee_id, detail=f"role={body.role}")
    return StandardResponse(success=True, message=f"User {body.employee_id} created")


@router.put("/users/{employee_id}", response_model=StandardResponse)
def edit_user(employee_id: str, body: UserUpdate, admin: CurrentUser = Depends(require_admin)):
    updates = body.model_dump(exclude_none=True)
    if "password" in updates:
        updates["password_hash"] = hash_password(updates.pop("password"))
    if body.role and body.role not in ("OPERATOR", "MANAGER", "ADMIN"):
        raise HTTPException(400, "role must be OPERATOR, MANAGER, or ADMIN")
    update_user(employee_id, updates)
    log_action("USER_UPDATED", employee_id=admin.employee_id, entity="USER", entity_id=employee_id)
    return StandardResponse(success=True, message=f"User {employee_id} updated")


@router.delete("/users/{employee_id}", response_model=StandardResponse)
def remove_user(employee_id: str, admin: CurrentUser = Depends(require_admin)):
    if employee_id == admin.employee_id:
        raise HTTPException(400, "Cannot deactivate your own account")
    deactivate_user(employee_id)
    log_action("USER_DEACTIVATED", employee_id=admin.employee_id,
               entity="USER", entity_id=employee_id)
    return StandardResponse(success=True, message=f"User {employee_id} deactivated")


@router.post("/users/{employee_id}/reset-password", response_model=StandardResponse)
def reset_password(
    employee_id: str,
    body: PasswordReset,
    admin: CurrentUser = Depends(require_admin),
):
    if not body.new_password or len(body.new_password) < 4:
        raise HTTPException(400, "Password must be at least 4 characters")
    hashed = hash_password(body.new_password)
    updated = update_user(employee_id, {"password_hash": hashed})
    if not updated:
        raise HTTPException(404, f"User {employee_id} not found")
    log_action("PASSWORD_RESET", employee_id=admin.employee_id,
               entity="USER", entity_id=employee_id)
    return StandardResponse(success=True, message=f"Password reset for {employee_id}")


# ── Approval Matrix ───────────────────────────────────────────

@router.get("/matrix", response_model=StandardResponse)
def list_matrix(_: CurrentUser = Depends(require_admin)):
    return StandardResponse(success=True, message="Approval matrix", data=get_matrix())


@router.post("/matrix", response_model=StandardResponse)
def add_matrix_entry(body: MatrixCreate, admin: CurrentUser = Depends(require_admin)):
    create_matrix_entry(body.level, body.min_value, body.max_value,
                        body.approver_email, body.approver_name)
    log_action("MATRIX_CREATED", employee_id=admin.employee_id, entity="MATRIX",
               detail=f"{body.min_value}-{body.max_value} → {body.approver_email}")
    return StandardResponse(success=True, message="Matrix entry created")


@router.put("/matrix/{entry_id}", response_model=StandardResponse)
def edit_matrix_entry(
    entry_id: int, body: MatrixUpdate, admin: CurrentUser = Depends(require_admin)
):
    updates = body.model_dump(exclude_none=True)
    if "approver_email" in updates:
        updates["approver_email"] = str(updates["approver_email"])
    update_matrix_entry(entry_id, updates)
    log_action("MATRIX_UPDATED", employee_id=admin.employee_id, entity="MATRIX",
               entity_id=str(entry_id))
    return StandardResponse(success=True, message=f"Matrix entry {entry_id} updated")


# ── Products Upload (full replace) ───────────────────────────

@router.post("/products/upload", response_model=StandardResponse)
async def upload_products(
    file: UploadFile = File(...),
    admin: CurrentUser = Depends(require_admin),
):
    if not file.filename.endswith((".csv", ".xlsx")):
        raise HTTPException(400, "Only .csv or .xlsx files are accepted")

    content = await file.read()
    try:
        if file.filename.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(400, f"Could not parse file: {e}")

    # Normalise column names → lowercase, strip whitespace
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    # Map Excel header names to internal DB column names
    col_map = {
        "material_no":  "part",
        "material_num": "part",
        "material":     "part",
        "plant":        "pro_type",
    }
    df.rename(columns=col_map, inplace=True)

    required = {"part", "price"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(
            400,
            f"Missing required columns: {missing}. "
            "Expected headers: Material No, Description, Price, Plant",
        )

    df = df.dropna(subset=["part", "price"])
    df["part"]  = df["part"].astype(str).str.strip()
    df["price"] = df["price"].astype(float)
    if "pro_type" in df.columns:
        df["pro_type"] = df["pro_type"].astype(str).str.strip()

    rows = df.to_dict(orient="records")
    count = replace_products(rows)

    log_action("PRODUCTS_REPLACED", employee_id=admin.employee_id,
               entity="PRODUCTS", detail=f"rows={count} file={file.filename}")
    return StandardResponse(
        success=True,
        message=f"Products replaced: {count} rows loaded from {file.filename}",
        data={"count": count},
    )


# ── Audit Logs ────────────────────────────────────────────────

@router.get("/audit-logs", response_model=StandardResponse)
def audit_logs(
    limit: int = Query(100, le=500),
    offset: int = 0,
    action: str | None = None,
    employee_id: str | None = None,
    _: CurrentUser = Depends(require_admin),
):
    logs = get_audit_logs(limit=limit, offset=offset, action=action, employee_id=employee_id)
    return StandardResponse(success=True, message=f"{len(logs)} log entries", data=logs)
