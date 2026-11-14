# 로그인, 로그아웃 - 로그인 후 해당 회원의 권한(RLS)으로 처리 가능
from shoppingmall_db.client import get_client


# 로그인
def sign_in(email: str, password: str) -> dict:
    get_client.cache_clear() # 이전 로그인 흔적 제거
    res = get_client().auth.sign_in_with_password({'email': email, 'password': password})
    return {'id': res.user.id, 'email': res.user.email}

# 로그아웃
def sign_out() -> None:
    get_client().auth.sign_out()
    get_client.cache_clear()