"""예외 처리 데모 (캡처용). 거절되는 요청이 어떤 예외로 바뀌는지 보인다. 데이터는 바뀌지 않는다."""

import os

from shoppingmall_db.auth import sign_in, sign_out
from shoppingmall_db.errors import InUseError, ParentError
from shoppingmall_db.orders import cancel_order, create_order
from shoppingmall_db.products import create_product, delete_product, list_products, update_product
from shoppingmall_db.users import create_user, list_users


# .env 값 읽기 (없으면 안내)
def env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} 가 .env 에 없습니다. U10의 .env 설정을 확인하세요.")
    return value


def section(title: str) -> None:
    print(f"\n{'=' * 8} {title} {'=' * 8}")


# 오류가 나야 정상인 호출: 어떤 예외로 바뀌었는지 출력한다
def expect_error(label: str, func, *args, **kwargs) -> None:
    print(f"\n[{label}]")
    try:
        func(*args, **kwargs)
        print("  !! 오류 없이 성공함 (규칙이 동작하지 않는 것)")
    except ParentError as e:
        print(f"  {type(e).__name__} / code={e.code} / constraint={e.constraint}")
        print(f"  메시지: {e}")


def main() -> None:
    user_email = env("DEMO_USER_EMAIL")
    admin_email = env("DEMO_ADMIN_EMAIL")
    password = env("DEMO_PASSWORD")

    # A. 로그인 안 한 상태
    section("A. 로그인 전")
    expect_error("1. 권한 없음: 로그인 없이 상품 추가", create_product, "권한 테스트", 1000, 1)
    expect_error("2. 로그인 실패: 틀린 비밀번호", sign_in, user_email, "wrong-password-xyz")

    # B. 관리자로 로그인해서 DB 규칙 위반을 일으킨다
    section(f"B. 관리자 ({admin_email})")
    sign_in(admin_email, password)
    first_user = list_users()[0]

    expect_error("3. 중복: 이미 있는 이메일", create_user, first_user["email"], "중복")
    expect_error("4. 값 오류(CHECK): 이메일 형식", create_user, "abc", "형식오류")
    expect_error("5. 값 오류(CHECK): 음수 가격", create_product, "음수 가격", -1, 1)
    expect_error("6. 값 오류(NOT NULL): 상품 이름 없음", create_product, None, 1000, 1)
    expect_error("7. 사용 중: 주문된 상품(1번) 삭제", delete_product, 1)
    expect_error("8. 업무 규칙: 재고 부족 주문(5번 상품)", create_order, first_user["id"],
                 [{"product_id": 5, "quantity": 1}])
    expect_error("9. 업무 규칙: 없는 주문 취소", cancel_order, 99999)

    # 종류별로 다르게 처리하는 예: InUseError만 잡아서 안내를 바꾼다
    print("\n[10. 종류별 처리: InUseError만 잡기]")
    try:
        delete_product(1)
    except InUseError as e:
        print(f"  InUseError를 잡았다 -> 삭제 대신 다른 방법을 안내: {e}")

    # 코드 실수(ValueError)는 DB 오류가 아니라서 그대로 나온다
    print("\n[11. 코드 실수: 고칠 수 없는 컬럼 (ValueError는 변환하지 않는다)]")
    try:
        update_product(1, id=5)
    except ValueError as e:
        print(f"  ValueError: {e}")

    print(f"\n(데이터는 바뀌지 않았다: 상품 {len(list_products())}개)")
    sign_out()


if __name__ == "__main__":
    main()
