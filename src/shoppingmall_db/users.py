from datetime import datetime, timezone
from shoppingmall_db.client import get_client


TABLE = 'users'
UPDATABLE = {'name', 'phone', 'email'}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# 회원 등록
def create_user(email: str, name: str, phone: str | None=None) -> dict:
    data = {'email': email, 'name':name}
    if phone is not None:
        data['phone'] = phone
    res = get_client().table(TABLE).insert(data).execute()
    return res.data[0]


# 회원 목록
def list_users(include_deleted: bool = False) -> list[dict]:
    query = get_client().table(TABLE).select('*').order('email')
    if not include_deleted:
        query = query.is_('deleted_at', 'null')
    return query.execute().data


# 특정 회원 조회 - 이이디
def get_user(user_id: str, include_deleted: bool = False) -> dict | None:
    query = get_client().table(TABLE).select('*').eq('id', user_id)
    if not include_deleted:
        query = query.is_('deleted_at', 'null')
    res = query.limit(1).execute()
    return res.data[0] if res.data else None


# 특정 회원 조회 - 이메일
def get_user_by_email(email: str, include_deleted: bool = False) -> dict | None:
    query = get_client().table(TABLE).select('*').eq('email', email)
    if not include_deleted:
        query = query.is_('deleted_at', 'null')
    res = query.limit(1).execute()
    return res.data[0] if res.data else None


# 특정 회원 정보 수정
def update_user(user_id: str, **fields) -> dict | None:

    unknown = set(fields) - UPDATABLE
    if unknown:
        raise ValueError(f'수정불가항목({sorted(unknown)})')
    if not fields:
        raise ValueError('고칠 값이 없습니다.')

    res = (
        get_client()
        .table(TABLE)
        .update(fields)
        .eq('id', user_id)
        .is_('deleted_at', 'null')
        .execute()
    )
    return res.data[0] if res.data else None


# 회원 탈퇴
def delete_user(user_id: str) -> dict | None:
    res = (
        get_client()
        .table(TABLE)
        .update({'deleted_at': _now()})
        .eq('id', user_id)
        .is_('deleted_at', 'null')
        .execute()
    )
    return res.data[0] if res.data else None


# 회원 탈퇴 복구
def restore_user(user_id: str) -> dict | None:
    res = (
        get_client()
        .table(TABLE)
        .update({'deleted_at': None})
        .eq('id', user_id)
        .not_.is_('deleted_at', 'null')
        .execute()
    )
    return res.data[0] if res.data else None