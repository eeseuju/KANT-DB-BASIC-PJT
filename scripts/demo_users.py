from uuid import uuid4
from postgrest.exceptions import APIError
from shoppingmall_db.client import get_client
from shoppingmall_db.users import (
    create_user,
    delete_user,
    get_user,
    get_user_by_email,
    list_users,
    restore_user,
    update_user,
)


# 회원 1행을 보기 좋게 (삭제된 회원이면 끝에 삭제 시각을 붙인다)
def format_row(row: dict) -> str:
    deleted = f" / 삭제 {row['deleted_at']}" if row.get("deleted_at") else ""
    return f"{row['id']} / {row['name']} / {row['email']} / {row['phone']}{deleted}"


# 결과 출력 (목록이면 한 줄씩, 한 명이면 한 줄, 그 외(None 등)는 그대로)
def show(title: str, value) -> None:
    print(f"\n[{title}]")
    if isinstance(value, list):
        for row in value:
            print(f"  {format_row(row)}")
    elif isinstance(value, dict):
        print(f"  {format_row(value)}")
    else:
        print(f"  {value}")


# 오류가 나야 정상인 호출
def expect_error(title: str, func, *args, **kwargs) -> None:
    print(f"\n[{title}]")
    try:
        func(*args, **kwargs)
        print("  !! 오류 없이 성공함 (제약이 동작하지 않는 것)")
    except APIError as e:
        print(f"  막힘 -> code={e.code} / {e.message}")


# 특정 회원의 주문 수 (소프트삭제 후에도 주문이 남는지 확인용)
def count_orders(user_id: str) -> int:
    res = get_client().table("orders").select("id", count="exact").eq("user_id", user_id).execute()
    return res.count


# 테스트
def main() -> None:
    # 시작 전 상태 (마지막에 같은 상태로 돌아왔는지 비교하려고 저장해 둔다)
    before = list_users()
    show("0. 시작 전 목록 (활성 회원)", before)

    # CREATE: 삭제해도 이메일이 남아 중복되므로, 실행마다 다른 이메일을 쓴다
    email = f"demo-{uuid4().hex[:8]}@test.com"
    created = create_user(email, "강데모", "010-0000-9999")
    show("1. CREATE", created)
    new_id = created["id"]

    # READ: uuid로, 이메일로
    show("2-1. READ (uuid로)", get_user(new_id))
    show("2-2. READ (이메일로)", get_user_by_email(email))

    # UPDATE: 이름과 전화번호 수정
    show("3. UPDATE", update_user(new_id, name="강데모(수정)", phone="010-0000-8888"))

    show("4. 목록 (활성 4명)", list_users())

    # 소프트삭제: 행을 지우지 않고 deleted_at만 채운다 -> 기본 조회에서 빠진다
    show("5. 소프트삭제 (deleted_at이 채워진다)", delete_user(new_id))
    show("5-1. 삭제 후 조회 (None이 정상)", get_user(new_id))
    show("5-2. 삭제 후 목록 (다시 3명)", list_users())
    show("5-3. 삭제된 회원 조회", get_user(new_id, include_deleted=True))
    show("5-4. 삭제된 회원 수정 시도 (None이 정상)", update_user(new_id, name="강데모(수정시도)"))
    show("5-5. 이미 삭제된 회원 재삭제 (None이 정상)", delete_user(new_id))

    show("6. 복구", restore_user(new_id))
    show("6-1. 복구 후 목록 (활성 4명)", list_users())
    delete_user(new_id)  # 다시 삭제 표시로 정리

    # 주문이 있는 시드 회원을 소프트삭제해도 주문은 남는다 (끝나면 복구)
    target = before[0]
    orders_before = count_orders(target["id"])
    try:
        delete_user(target["id"])
        print(f"\n[7. 주문 있는 회원 소프트삭제: {target['name']}]")
        print(f"  주문 수 삭제 전 {orders_before} / 삭제 후 {count_orders(target['id'])} (같아야 한다)")
    finally:
        restore_user(target["id"])

    # 제약 위반: 오류가 나야 정상
    expect_error("E-1. 이메일 중복", create_user, before[0]["email"], "중복")
    expect_error("E-2. 이메일 형식 오류", create_user, "abc", "형식오류")

    show("끝. 최종 활성 목록 (시작 전 목록과 같아야 한다)", list_users())
    print(f"\n(삭제 표시된 회원 포함 전체: {len(list_users(include_deleted=True))}명)")


if __name__ == "__main__":
    main()
