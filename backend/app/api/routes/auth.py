from fastapi import APIRouter, HTTPException, Depends, status
from backend.app.core.auth import (
    LoginRequest, TokenResponse, User, authenticate_user,
    generate_signed_token, get_current_user, TOKEN_EXPIRY_SECONDS
)

router = APIRouter(prefix="/api/auth", tags=["Authentication & Access Control"])

@router.post("/login", response_model=TokenResponse, summary="User Authentication & Token Issuance")
async def login(req: LoginRequest):
    """
    Authenticates operator identity against PBKDF2 credential store.
    Issues HMAC-SHA256 authenticated session token with embedded role context.
    """
    user = authenticate_user(req.username.strip(), req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    token = generate_signed_token({
        "sub": user.username,
        "role": user.role,
        "name": user.full_name
    })
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=TOKEN_EXPIRY_SECONDS,
        user=user
    )

@router.get("/me", response_model=User, summary="Get Current Authenticated Identity Profile")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Validates session token and returns current authenticated user profile."""
    return current_user

@router.post("/logout", summary="Operator Session Logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Invalidates or clears client session state."""
    return {"status": "SUCCESS", "message": f"User {current_user.username} logged out successfully."}
