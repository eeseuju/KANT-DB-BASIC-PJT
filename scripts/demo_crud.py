# 통합 CRUD 데모 (관리자 로그인)

import os
import demo_orders
import demo_products
import demo_users
from shoppingmall_db.auth import sign_in, sign_out


# 환경변수
def env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f'{name}가 환경변수에 없습니다. 환경변수 설정을 확인하세요.')
    return value


# 안내표시
def banner(title: str) -> None:
    print(f'\n{'#'*8} {title} {'#'*8}')


# 테스트
def main() -> None:
    admin_email = env('DEMO_ADMIN_EMAIL')
    print(f'관리자 로그인: {sign_in(admin_email, env('DEMO_PASSWORD'))['email']}')
    try:
        banner('상품 CRUD')
        demo_products.main()
        banner('회원 CRUD')
        demo_users.main()
        banner('주문 CRUD + 트랜잭션')
        demo_orders.main()
    finally:
        sign_out()


if __name__ == "__main__":
    main()