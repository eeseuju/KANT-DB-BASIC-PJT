from postgrest.exceptions import APIError
from shoppingmall_db.products import (
    create_product,
    delete_product,
    get_product,
    list_products,
    update_product,
)

# 상품 1행을 보기 좋게 (가격은 천 단위 콤마)
def format_row(row: dict, detail: bool = False) -> str:
    text = f"{row['id']}: {row['name']} / {row['price']:,}원 / 재고 {row['stock']}개"
    if detail:
        text += f" / 생성 {row['created_at']} / 수정 {row['updated_at']}"
    return text

# 현재 상품 등록 상태 확인
def show(title: str, value) -> None:
    print(f'\n[{title}]')
    if isinstance(value, list):
        for row in value:
            print(f'  {format_row(row)}')
    elif isinstance(value, dict) and 'price' in value:
        print(f'  {format_row(value, detail=True)}')
    else:
        print(f'  {value}')

# 오류가 나야 정상인 호출
def expect_error(title: str, func, *args, **kwargs) -> None:
    print(f'\n[{title}]')
    try:
        func(*args, **kwargs)
        print('  !! 오류 없이 성공함 (제약이 동작하지 않는 것)')
    except APIError as e:
        print(f'  막힘 -> code={e.code} / {e.message}')

# 테스트
def main() -> None:
    show("0. 시작 전 목록", list_products())

    created = create_product("데모 상품", 10000, 5)
    show("1. CREATE", created)
    new_id = created["id"]

    show("2. READ (1개)", get_product(new_id))

    updated = update_product(new_id, price=12000, stock=4)
    show("3. UPDATE", updated)

    show("4. READ (재고 있는 목록)", list_products(only_in_stock=True))

    show("5. DELETE", delete_product(new_id))
    show("5-1. 지운 뒤 조회(None이 정상)", get_product(new_id))

    # 제약 위반: 오류가 나야 정상
    expect_error("E-1. 음수 가격", create_product, "음수 가격", -1, 1)
    expect_error("E-2. 주문된 상품 삭제 (1번)", delete_product, 1)

    show("끝. 최종 목록 (시작 전 목록과 같아야 한다)", list_products())

if __name__ == "__main__":
    main()