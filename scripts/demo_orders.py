from postgrest.exceptions import APIError
from shoppingmall_db.orders import (
    cancel_order,
    create_order,
    get_order,
    list_orders,
    update_order_status,
)
from shoppingmall_db.products import list_products
from shoppingmall_db.users import list_users


# 주문 1건을 보기 좋게 (주문상품 줄까지)
def format_order(order: dict) -> str:
    lines = [f"주문 번호 {order['id']} / {order['status']} / 합계 {order['total_amount']:,}원"]
    for item in order["order_items"]:
        name = item["products"]["name"]
        lines.append(f"    - {name} x {item['quantity']}개 x {item['unit_price']:,}원")
    return "\n".join(lines)


# 재고 현황을 한 줄로
def stock_line() -> str:
    return " / ".join(f"{p['id']}번 {p['stock']}" for p in list_products())


# 결과 출력 (주문 하나, 주문 목록, 그 외(None 등)는 그대로)
def show(title: str, value) -> None:
    print(f"\n[{title}]")
    if isinstance(value, list):
        for order in value:
            print(f"  {format_order(order)}")
    elif isinstance(value, dict):
        print(f"  {format_order(value)}")
    else:
        print(f"  {value}")


# 오류가 나야 정상인 호출
def expect_error(title: str, func, *args, **kwargs) -> None:
    print(f"\n[{title}]")
    try:
        func(*args, **kwargs)
        print("  !! 오류 없이 성공함 (규칙이 동작하지 않는 것)")
    except APIError as e:
        print(f"  막힘 -> code={e.code} / {e.message}")


# 테스트
def main() -> None:
    user = list_users()[0]  # 이메일 순 첫 회원
    print(f"주문자: {user['name']} ({user['email']})")
    print(f"0. 시작 재고: {stock_line()}")
    print(f"   시작 주문 수: {len(list_orders())}")

    # CREATE: 노트북 거치대(4) 2개 + USB-C 케이블(3) 1개 -> 한 번의 호출로 원자적으로 처리
    order = create_order(user["id"], [
        {"product_id": 4, "quantity": 2},
        {"product_id": 3, "quantity": 1},
    ])
    show("1. CREATE (합계 79,900원이어야 한다)", order)
    print(f"  재고 내역: {stock_line()}  (3번 -1, 4번 -2)")
    order_id = order["id"]

    # READ
    show("2-1. READ (1건)", get_order(order_id))
    show("2-2. READ (이 회원의 주문 목록)", list_orders(user_id=user["id"]))

    # UPDATE: 상태 변경
    show("3. UPDATE (pending -> paid)", update_order_status(order_id, "paid"))

    # 취소: 상태 canceled + 재고 복구
    show("4. 취소 (canceled, 재고 복구)", cancel_order(order_id))
    print(f"  재고 내역: {stock_line()}  (시작 재고와 같아야 한다)")

    # 취소된 주문은 다시 취소할 수 없고 상태도 못 바꾼다
    expect_error("E-1. 이미 취소된 주문 재취소", cancel_order, order_id)
    show("E-2. 취소된 주문 상태 변경 시도 (None이 정상)", update_order_status(order_id, "paid"))

    # 실패 재현: 1번은 재고가 충분하지만 5번은 재고 0 -> 전체 취소되어야 한다
    orders_before = len(list_orders())
    stock_before = stock_line()
    expect_error(
        "E-3. 재고 부족 주문 (1번 1개 + 5번 1개)",
        create_order, user["id"], [
            {"product_id": 1, "quantity": 1},
            {"product_id": 5, "quantity": 1},
        ],
    )
    print(f"  주문 수: 전 {orders_before} / 후 {len(list_orders())} (같아야 한다)")
    print(f"  재고 전: {stock_before}")
    print(f"  재고 후: {stock_line()} (같아야 한다, 1번이 줄었다면 원자성이 깨진 것)")

    # 그 밖의 규칙 위반
    expect_error("E-4. 없는 회원", create_order, "99999999-9999-9999-9999-999999999999",
                 [{"product_id": 1, "quantity": 1}])
    expect_error("E-5. 수량 0", create_order, user["id"], [{"product_id": 1, "quantity": 0}])
    expect_error("E-6. 빈 주문", create_order, user["id"], [])


if __name__ == "__main__":
    main()
