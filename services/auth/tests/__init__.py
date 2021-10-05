import asyncio
from unittest import TestCase

import jwt
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import user_crud, verification_crud
from app.tokens import ALGORITHM
from config import SECRET_KEY
from db import engine, Base
from main import app


async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def async_loop(function):
    loop = asyncio.get_event_loop()
    try:
        return loop.run_until_complete(function)
    finally:
        pass


class AuthTestCase(TestCase):

    def setUp(self) -> None:
        self.session = AsyncSession(engine)
        self.client = TestClient(app)
        self.data = {
            'password': 'Test1234!',
            'confirm_password': 'Test1234!',
            'username': 'test',
            'email': 'test@example.com',
            'freelancer': False,
        }
        async_loop(create_all())

    def tearDown(self) -> None:
        async_loop(self.session.close())
        async_loop(drop_all())

    def test_register(self):
        self.assertEqual(len(async_loop(user_crud.all(self.session))), 0)
        self.assertEqual(len(async_loop(verification_crud.all(self.session))), 0)

        # Invalid passwords
        response = self.client.post('/api/v1/register', json={**self.data, 'password': 'test'})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['detail'][0]['msg'], 'Password invalid')
        self.assertEqual(len(async_loop(user_crud.all(self.session))), 0)
        self.assertEqual(len(async_loop(verification_crud.all(self.session))), 0)

        response = self.client.post('/api/v1/register', json={**self.data, 'password': 'test241fg'})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['detail'][0]['msg'], 'Password invalid')
        self.assertEqual(len(async_loop(user_crud.all(self.session))), 0)
        self.assertEqual(len(async_loop(verification_crud.all(self.session))), 0)

        response = self.client.post('/api/v1/register', json={**self.data, 'password': 'test241fg!'})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['detail'][0]['msg'], 'Password invalid')
        self.assertEqual(len(async_loop(user_crud.all(self.session))), 0)
        self.assertEqual(len(async_loop(verification_crud.all(self.session))), 0)

        response = self.client.post('/api/v1/register', json={**self.data, 'confirm_password': 'test241fg!'})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['detail'][0]['msg'], 'Passwords do not match')
        self.assertEqual(len(async_loop(user_crud.all(self.session))), 0)
        self.assertEqual(len(async_loop(verification_crud.all(self.session))), 0)

        # Register
        response = self.client.post('/api/v1/register', json=self.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {'msg': 'Send email for activate your account'})
        self.assertEqual(len(async_loop(user_crud.all(self.session))), 1)
        self.assertEqual(len(async_loop(verification_crud.all(self.session))), 1)

        response = self.client.post('/api/v1/register', json=self.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Username exist'})
        self.assertEqual(len(async_loop(user_crud.all(self.session))), 1)
        self.assertEqual(len(async_loop(verification_crud.all(self.session))), 1)

        response = self.client.post('/api/v1/register', json={**self.data, 'username': 'test2'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Email exist'})
        self.assertEqual(len(async_loop(user_crud.all(self.session))), 1)
        self.assertEqual(len(async_loop(verification_crud.all(self.session))), 1)

        self.assertEqual(async_loop(verification_crud.get(self.session, id=1)).user_id, 1)
        self.assertEqual(async_loop(user_crud.get(self.session, id=1)).freelancer, False)

    def test_verification(self):
        self.client.post('/api/v1/register', json={**self.data, 'freelancer': True})
        self.assertEqual(async_loop(user_crud.get(self.session, id=1)).freelancer, True)
        self.assertEqual(len(async_loop(verification_crud.all(self.session))), 1)
        self.assertEqual(async_loop(user_crud.get(self.session, id=1)).is_active, False)

        verification = async_loop(verification_crud.get(self.session, id=1))
        response = self.client.get(f'/api/v1/verify?link={verification.link}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'msg': 'Your account has been activated'})

        self.assertEqual(len(async_loop(verification_crud.all(self.session))), 0)
        self.assertEqual(async_loop(user_crud.get(self.session, id=1)).is_active, True)

        response = self.client.get(f'/api/v1/verify?link={verification.link}')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Verification not exist'})

    def test_login(self):
        self.client.post('/api/v1/register', json=self.data)

        response = self.client.post('/api/v1/login', data={'username': 'test', 'password': 'Test1234!'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {'detail': 'You not activated'})

        verification = async_loop(verification_crud.get(self.session, id=1))
        self.client.get(f'/api/v1/verify?link={verification.link}')

        response = self.client.post('/api/v1/login', data={'username': 'test', 'password': 'Test1234!'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['type'], 'bearer')
        self.assertEqual('access_token' in response.json(), True)
        self.assertEqual('refresh_token' in response.json(), True)

        access = jwt.decode(response.json()['access_token'], SECRET_KEY, algorithms=[ALGORITHM])
        self.assertEqual(access['user_id'], 1)
        self.assertEqual(access['sub'], 'access')

        refresh = jwt.decode(response.json()['refresh_token'], SECRET_KEY, algorithms=[ALGORITHM])
        self.assertEqual(refresh['user_id'], 1)
        self.assertEqual(refresh['sub'], 'refresh')

        response = self.client.post('/api/v1/login', data={'username': 'test2', 'password': 'Test1234!'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Username not found'})

        response = self.client.post('/api/v1/login', data={'username': 'test', 'password': 'Test1234!!'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'detail': 'Password mismatch'})

        response = self.client.post('/api/v1/login', data={'username': 'test', 'password': 't'})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['detail'][0]['msg'], 'ensure this value has at least 8 characters')

        response = self.client.post('/api/v1/login', data={'username': 'test', 'password': 't' * 25})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['detail'][0]['msg'], 'ensure this value has at most 20 characters')
