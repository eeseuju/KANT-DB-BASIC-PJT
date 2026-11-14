# 로그인, 로그아웃 - 로그인 후 해당 회원의 권한(RLS)으로 처리 가능
from supabase import AuthApiError

from shoppingmall_db.client import get_client
from shoppingmall_db.errors import AuthenticationError


# 로그인
def sign_in(email: str, password: str) -> dict:
    get_client.cache_clear() # 이전 로그인 흔적 제거
    try:
        res = get_client().auth.sign_in_with_password({'email': email, 'password': password})
    except AuthApiError as e:
        if 'Invalid login credentials' in str(e):
            raise AuthenticationError('이메일 또는 비밀번호가 올바르지 않습니다.') from e
        raise AuthenticationError(f'로그인에 실패했습니다: {e}') from e
    return {'id': res.user.id, 'email': res.user.email}

# 로그아웃
def sign_out() -> None:
    get_client().auth.sign_out()
    get_client.cache_clear()
