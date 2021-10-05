from fastapi import APIRouter, Depends, status, Form, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app import views
from app.models import User
from app.schemas import Register, Message, Tokens, AccessToken, PermissionResponse
from db import get_db

auth_router = APIRouter()


@auth_router.post(
    '/register',
    name='Register',
    description='Register user',
    response_description='Message',
    status_code=status.HTTP_201_CREATED,
    response_model=Message,
    tags=['auth'],
)
async def register(schema: Register, db: AsyncSession = Depends(get_db)):
    return await views.register(db, schema)


@auth_router.get(
    '/verify',
    name='Verification account',
    description='Verification user account',
    response_description='Message',
    status_code=status.HTTP_200_OK,
    response_model=Message,
    tags=['auth'],
)
async def verify(link: str, db: AsyncSession = Depends(get_db)):
    return await views.verify(db, link)


@auth_router.post(
    '/login',
    name='Login',
    description='Login user',
    response_description='Tokens',
    status_code=status.HTTP_200_OK,
    response_model=Tokens,
    tags=['auth'],
)
async def login(
        username: str = Form(...),
        password: str = Form(..., min_length=8, max_length=20),
        db: AsyncSession = Depends(get_db),
):
    return await views.login(db, username, password)


@auth_router.post(
    '/refresh',
    name='Refresh token',
    description='Refresh token',
    response_description='Access token',
    status_code=status.HTTP_200_OK,
    response_model=AccessToken,
    tags=['auth'],
)
async def refresh(token: str, db: AsyncSession = Depends(get_db)):
    return await views.refresh(db, token)


@auth_router.post(
    '/is-authenticated',
    name='Authenticated user',
    description='Authenticated user',
    response_description='User ID',
    status_code=status.HTTP_200_OK,
    response_model=PermissionResponse,
    tags=['permission'],
)
async def is_authenticated(user_id: int = Depends(views.is_authenticated)):
    return {'user_id': user_id}


@auth_router.post(
    '/is-active',
    name='Is activated user',
    description='Is activated user',
    response_description='User ID',
    status_code=status.HTTP_200_OK,
    response_model=PermissionResponse,
    tags=['permission'],
)
async def is_active(user: User = Depends(views.is_active)):
    return {'user_id': user.id}


@auth_router.post(
    '/is-superuser',
    name='Is superuser user',
    description='Is superuser user',
    response_description='User ID',
    status_code=status.HTTP_200_OK,
    response_model=PermissionResponse,
    tags=['permission'],
)
async def is_superuser(user: User = Depends(views.is_superuser)):
    return {'user_id': user.id}


@auth_router.post(
    '/avatar',
    name='Avatar',
    description='User avatar',
    response_description='Message',
    status_code=status.HTTP_200_OK,
    response_model=Message,
    tags=['change-data'],
)
async def avatar(
        file: UploadFile = File(...), user: User = Depends(views.is_active), db: AsyncSession = Depends(get_db)
):
    return await views.avatar(db, user, file)
