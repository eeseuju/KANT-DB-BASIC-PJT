from datetime import datetime, timezone
from shoppingmall_db.client import get_client
from shoppingmall_db.errors import translate_errors


TABLE = 'products'
UPDATABLE = {'name', 'price', 'stock'}


# 새로운 상품 등록과 조회
@translate_errors
def create_product(name: str, price: int, stock: int = 0) -> dict:
    res = (
        get_client()
        .table(TABLE)
        .insert({'name': name, 'price': price, 'stock': stock})
        .execute()
    )
    return res.data[0]


# 재고가 있는 상품을 조회
@translate_errors
def list_products(only_in_stock: bool = False) -> list[dict]:
    query = get_client().table(TABLE).select('*').order('id')
    if only_in_stock:
        query = query.gt('stock', 0)
    return query.execute().data


# 해당 상품이 있는지 조회
@translate_errors
def get_product(product_id: int) -> dict | None:
    res = (
        get_client()
        .table(TABLE)
        .select('*')
        .eq('id', product_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


# 특정 상품의 정보를 수정
@translate_errors
def update_product(product_id: int, **fields) -> dict | None:
    
    unknown = set(fields) - UPDATABLE
    if unknown:
        raise ValueError(f'수정불가항목({sorted(unknown)})')
    if not fields:
        raise ValueError('고칠 값이 없습니다.')
    
    fields['updated_at'] = datetime.now(timezone.utc).isoformat()
    res = (
        get_client()
        .table(TABLE)
        .update(fields)
        .eq('id', product_id)
        .execute()
    )
    return res.data[0] if res.data else None


# 특정 상품의 정보를 삭제
@translate_errors
def delete_product(product_id: int) -> dict | None:
    res = (
        get_client()
        .table(TABLE)
        .delete()
        .eq('id', product_id)
        .execute()
    )
    return res.data[0] if res.data else None