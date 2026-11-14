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


# 결과 출력 (목록이면 한 줄씩, 상품 1개면 생성·수정 시각까지, 그 외(None 등)는 그대로)
def show(title: str, value) -> None:
    print(f'\n[{title}]')
    if isinstance(value, list):
        for row in value:
            print(f'  {format_row(row)}')
    elif isinstance(value, dict) and 'price' in value:
        print(f'  {format_row(value, detail=True)}')
    else:
        print(f'  {value}')


# 오류가 나야 정상인 호출 (막히면 오류 코드와 메시지를 출력, 성공해 버리면 경고)
def expect_error(title: str, func, *args, **kwargs) -> None:
    print(f'\n[{title}]')
    try:
        func(*args, **kwargs)
        print('  !! 오류 없이 성공함 (제약이 동작하지 않는 것)')
    except APIError as e:
        print(f'  막힘 -> code={e.code} / {e.message}')


# 테스트
def main() -> None:
    # 시작 전 상태 (마지막에 같은 상태로 돌아왔는지 비교한다)
    show("0. 시작 전 목록", list_products())

    # CREATE: 상품 추가 (id는 DB가 정해서 돌려준다)
    created = create_product("데모 상품", 10000, 5)
    show("1. CREATE", created)
    new_id = created["id"]

    # READ: id로 1개 조회
    show("2. READ (1개)", get_product(new_id))

    # UPDATE: 가격과 재고 수정 (updated_at도 함께 갱신된다)
    updated = update_product(new_id, price=12000, stock=4)
    show("3. UPDATE", updated)

    # READ: 재고가 있는 상품만 조회 (재고 0인 5번은 빠진다)
    show("4. READ (재고 있는 목록)", list_products(only_in_stock=True))

    # DELETE: 직접 만든 상품만 지운다 (시드 상품은 건드리지 않는다)
    show("5. DELETE", delete_product(new_id))
    show("5-1. 지운 뒤 조회(None이 정상)", get_product(new_id))

    # 제약 위반: 오류가 나야 정상
    # E-1: 가격이 음수 -> CHECK 위반
    expect_error("E-1. 음수 가격", create_product, "음수 가격", -1, 1)
    # E-2: 주문에 들어 있는 상품은 지울 수 없다 -> FK 위반
    expect_error("E-2. 주문된 상품 삭제 (1번)", delete_product, 1)

    show("끝. 최종 목록 (시작 전 목록과 같아야 한다)", list_products())


if __name__ == "__main__":
    main()