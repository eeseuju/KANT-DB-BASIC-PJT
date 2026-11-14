# 주문 CRUD 중 생성 및 취소는 DB 함수(RPC)로 하나의 트랜잭션 처리

from shoppingmall_db.client import get_client


TABLE = 'orders'
STATUS_CHANGEABLE = {'pending', 'paid', 'shipped'}

# 조회할 때 주문상품과 상품이름까지 같이 가져온다.
SELECT_WITH_ITEMS = '*, order_items(*, products(name))'


# 원자적 주문 생성
def create_order(user_id: str, items: list[dict]) -> dict:
    res = (
        get_client()
        .rpc('create_order', {'p_user_id': user_id, 'p_items': items})
        .execute()
    )
    return get_order(res.data)


# 특정 주문 조회
def get_order(order_id: int) -> dict | None:
    res = (
        get_client()
        .table(TABLE)
        .select(SELECT_WITH_ITEMS)
        .eq('id', order_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


# 주문 목록 조회
def list_orders(user_id: str | None=None, status: str | None=None) -> list[dict]:
    query = get_client().table(TABLE).select(SELECT_WITH_ITEMS).order('id', desc=True)
    if user_id is not None:
        query = query.eq('user_id', user_id)
    if status is not None:
        query = query.eq('status', status)
    return query.execute().data


# 주문 정보 수정
def update_order_status(order_id: int, status: str) -> dict | None:
    
    if status not in STATUS_CHANGEABLE:
        raise ValueError(f'수정불가상태({status}) / 취소는 cancel_order')

    res = (
        get_client()
        .table(TABLE)
        .update({'status': status})
        .eq('id', order_id)
        .neq('status', 'canceled')
        .execute()
    )
    return get_order(order_id) if res.data else None


# 원자적 주문 취소
def cancel_order(order_id: int) -> dict | None:
    get_client().rpc('cancel_order', {'p_order_id': order_id}).execute()
    return get_order(order_id)