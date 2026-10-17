from fastapi import (
    Depends,
    HTTPException,
    status
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)

from jose import (
    JWTError,
    jwt
)

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.core.config import settings

from app.models.user import User


security = HTTPBearer()


def get_current_user(

    credentials:
    HTTPAuthorizationCredentials =
    Depends(security),

    db: Session =
    Depends(get_db)

):

    token = credentials.credentials


    try:

        payload = jwt.decode(

            token,

            settings.JWT_SECRET_KEY,

            algorithms=[
                settings.JWT_ALGORITHM
            ]

        )


        user_id = payload.get(
            "sub"
        )


        if user_id is None:

            raise HTTPException(

                status_code=
                status.HTTP_401_UNAUTHORIZED,

                detail=
                "Invalid authentication token"

            )


    except JWTError:

        raise HTTPException(

            status_code=
            status.HTTP_401_UNAUTHORIZED,

            detail=
            "Invalid or expired token"

        )


    user = db.query(User).filter(
        User.id == int(user_id)
    ).first()


    if not user:

        raise HTTPException(

            status_code=
            status.HTTP_401_UNAUTHORIZED,

            detail=
            "User not found"

        )


    if not user.is_active:

        raise HTTPException(

            status_code=
            status.HTTP_403_FORBIDDEN,

            detail=
            "Inactive account"

        )


    return user
def require_roles(*allowed_roles):

    def role_checker(
        current_user: User = Depends(
            get_current_user
        )
    ):

        if current_user.role not in allowed_roles:

            raise HTTPException(

                status_code=
                status.HTTP_403_FORBIDDEN,

                detail=
                "You do not have permission to access this resource"

            )

        return current_user

    return role_checker