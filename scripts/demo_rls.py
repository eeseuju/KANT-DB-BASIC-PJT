import os
from shoppingmall_db.errors import ParentError
from shoppingmall_db.auth import sign_in, sign_out
from shoppingmall_db.orders import (
    cancel_order,
    create_order,
    get_order,
    list_orders,
    update_order_status,
)
from shoppingmall_db.products import create_product, delete_product, list_products, update_product
from shoppingmall_db.users import list_users, update_user


OTHER_USER_ID = "22222222-2222-2222-2222-222222222222"  # 시드 회원 2번 (데모 계정과 연결 안 됨)
OTHER_ORDER_ID = 3  # 시드 3번 주문 (회원 2번 것)


# .env 값 읽기 (없으면 안내)
def env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} 가 .env 에 없습니다. U10의 .env 설정을 확인하세요.")
    return value


def section(title: str) -> None:
    print(f"\n{'=' * 8} {title} {'=' * 8}")


def say(label: str, value) -> None:
    print(f"  {label}: {value}")


# 오류가 나야 정상인 호출
def expect_error(label: str, func, *args, **kwargs) -> None:
    try:
        func(*args, **kwargs)
        print(f"  {label}: !! 오류 없이 성공함 (규칙이 동작하지 않는 것)")
    except ParentError as e:
        print(f"  {label}: 막힘 -> code={e.code} / {e}")


# 주문 목록을 "번호:상태" 로 요약
def brief(orders: list[dict]) -> str:
    return ", ".join(f"{o['id']}:{o['status']}" for o in orders) or "(없음)"


# 상품 1번 가격
def price_of_1() -> int:
    return next(p for p in list_products() if p["id"] == 1)["price"]


def main() -> None:
    user_email = env("DEMO_USER_EMAIL")
    admin_email = env("DEMO_ADMIN_EMAIL")
    password = env("DEMO_PASSWORD")

    # A. 로그인 안 한 상태 (anon)
    section("A. 로그인 안 함")
    say("상품 목록 수 (공개라서 보인다)", len(list_products()))
    say("주문 목록 수 (빈 결과가 정상)", len(list_orders()))
    say("회원 목록 수 (빈 결과가 정상)", len(list_users()))
    expect_error("상품 추가 시도", create_product, "RLS 테스트", 1000, 1)
    say("상품 1번 가격 수정 시도 (None이 정상)", update_product(1, price=1))
    say("상품 1번 가격 (그대로여야 한다)", f"{price_of_1():,}원")
    expect_error("주문 생성 시도 (로그인 필요)", create_order, OTHER_USER_ID,
                 [{"product_id": 3, "quantity": 1}])

    # B. 일반 회원
    section(f"B. 일반 회원 ({user_email})")
    say("로그인", sign_in(user_email, password)["email"])
    me = list_users()
    say("보이는 회원 수 (본인 1명이 정상)", len(me))
    my_id, my_name = me[0]["id"], me[0]["name"]
    say("보이는 주문 (본인 주문만)", brief(list_orders()))
    say(f"남의 주문 {OTHER_ORDER_ID}번 조회 (None이 정상)", get_order(OTHER_ORDER_ID))
    say("남의 정보 수정 시도 (None이 정상)", update_user(OTHER_USER_ID, name="해킹"))
    say("내 이름 수정 (성공)", (update_user(my_id, name=f"{my_name}(수정)") or {}).get("name"))
    update_user(my_id, name=my_name)  # 되돌리기
    expect_error("상품 추가 시도 (관리자만)", create_product, "RLS 테스트", 1000, 1)
    say("상품 1번 가격 수정 시도 (None이 정상)", update_product(1, price=1))
    order = create_order(my_id, [{"product_id": 3, "quantity": 1}])
    say("내 주문 생성 (성공)", f"{order['id']}번 / {order['total_amount']:,}원")
    say("내 주문 상태 변경 시도 (None이 정상)", update_order_status(order["id"], "paid"))
    expect_error("남의 이름으로 주문 생성", create_order, OTHER_USER_ID,
                 [{"product_id": 3, "quantity": 1}])
    expect_error(f"남의 주문 {OTHER_ORDER_ID}번 취소", cancel_order, OTHER_ORDER_ID)
    say("내 주문 취소 (성공)", cancel_order(order["id"])["status"])
    sign_out()

    # C. 관리자
    section(f"C. 관리자 ({admin_email})")
    say("로그인", sign_in(admin_email, password)["email"])
    say("보이는 회원 수 (전체)", len(list_users()))
    say("보이는 주문 (전체)", brief(list_orders()))
    created = create_product("RLS 테스트 상품", 1000, 1)
    say("상품 추가 (성공)", created["name"])
    say("상품 삭제 (성공)", delete_product(created["id"])["name"])
    sign_out()


if __name__ == "__main__":
    main()
