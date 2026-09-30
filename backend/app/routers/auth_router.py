import sqlite3
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.models import UserRegister, UserLogin, UserResponse, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegister, conn: sqlite3.Connection = Depends(get_db)):
    """Registers a new user account with unique email and username."""
    cursor = conn.cursor()

    # Check for existing email or username
    existing = cursor.execute(
        "SELECT id, email, username FROM users WHERE email = ? OR username = ?",
        (user_data.email.lower(), user_data.username.lower())
    ).fetchone()

    if existing:
        if existing["email"].lower() == user_data.email.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This username is already taken. Please choose another."
            )

    hashed_pw = hash_password(user_data.password)
    cursor.execute("""
        INSERT INTO users (email, username, hashed_password, full_name, role)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user_data.email.lower(),
        user_data.username.lower(),
        hashed_pw,
        user_data.full_name.strip(),
        user_data.role or "job_seeker"
    ))
    conn.commit()
    user_id = cursor.lastrowid

    # Fetch newly created user
    row = cursor.execute("SELECT id, email, username, full_name, role, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
    user_resp = UserResponse(**dict(row))

    token = create_access_token({"sub": str(user_id), "email": user_resp.email, "role": user_resp.role})
    return TokenResponse(access_token=token, user=user_resp)

@router.post("/login", response_model=TokenResponse)
def login_user(login_data: UserLogin, conn: sqlite3.Connection = Depends(get_db)):
    """Authenticates a user with email or username and password."""
    cursor = conn.cursor()
    identifier = login_data.email_or_username.strip().lower()

    row = cursor.execute("""
        SELECT id, email, username, hashed_password, full_name, role, created_at
        FROM users
        WHERE LOWER(email) = ? OR LOWER(username) = ?
    """, (identifier, identifier)).fetchone()

    if not row or not verify_password(login_data.password, row["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify your email/username and password."
        )

    user_dict = dict(row)
    del user_dict["hashed_password"]
    user_resp = UserResponse(**user_dict)

    token = create_access_token({"sub": str(row["id"]), "email": row["email"], "role": row["role"]})
    return TokenResponse(access_token=token, user=user_resp)

@router.get("/me", response_model=UserResponse)
def get_profile(current_user: dict = Depends(get_current_user)):
    """Retrieves profile data for the authenticated user."""
    return UserResponse(**current_user)

@router.post("/logout")
def logout_user():
    """Client logout acknowledgement."""
    return {"message": "Successfully logged out. Please remove token from client storage."}
