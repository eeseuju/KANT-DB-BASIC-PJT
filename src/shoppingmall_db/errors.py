import re
from functools import wraps
from postgrest.exceptions import APIError


# 이 프로젝트 예외의 부모
class ParentError(Exception):

    def __init__(self, message: str, code: str | None=None, constraint: str | None=None):

        super().__init__(message)
        self.code = code
        self.constraint = constraint


# [23505] 이미 있는 값
class DuplicateError(ParentError):
    pass


# [23503] 이미 사용 중
class InUseError(ParentError):
    pass


# [23514/23502/23503] 허용되지 않는 값
class InvalidValueError(ParentError):
    pass


# [42501] 권한 없음
class PermissionDeniedError(ParentError):
    pass


# [P0001] 업무 규칙 위반
class BusinessRuleError(ParentError):
    pass


# 로그인 실패
class AuthenticationError(ParentError):
    pass


# 그 외 오류
class DatabaseError(ParentError):
    pass


# 제약 이름 -> 사용자에게 보여 줄 메시지 (UNIQUE, CHECK)
CONSTRAINT_MESSAGES = {
    "uq_users_email": "이미 사용 중인 이메일입니다.",
    "uq_users_auth_user_id": "이미 다른 회원과 연결된 로그인 계정입니다.",
    "uq_order_items_order_product": "같은 주문에 같은 상품이 이미 담겨 있습니다.",
    "ck_users_email_format": "이메일 형식이 올바르지 않습니다.",
    "ck_products_name_not_blank": "상품 이름이 비어 있습니다.",
    "ck_products_price_nonneg": "가격은 0 이상이어야 합니다.",
    "ck_products_stock_nonneg": "재고는 0 이상이어야 합니다.",
    "ck_orders_status": "허용되지 않는 주문 상태입니다.",
    "ck_orders_total_nonneg": "주문 합계는 0 이상이어야 합니다.",
    "ck_order_items_quantity_positive": "수량은 1 이상이어야 합니다.",
    "ck_order_items_unit_price_nonneg": "단가는 0 이상이어야 합니다.",
}


# 삭제가 막혔을 때(FK) 제약 이름 -> 메시지
IN_USE_MESSAGES = {
    "fk_order_items_products": "주문된 상품은 삭제할 수 없습니다. 판매를 멈추려면 재고를 0으로 하세요.",
    "fk_orders_users": "주문이 있는 회원은 삭제할 수 없습니다. 탈퇴(소프트삭제)로 처리하세요.",
}


# APIError를 이 프로젝트 예외로 바꾸기
def translate(e: APIError) -> ParentError:

    code = e.code
    msg = e.message or ""
    found = re.search(r'constraint "([^"]+)"', msg)
    name = found.group(1) if found else None

    if code == "23505":
        return DuplicateError(CONSTRAINT_MESSAGES.get(name, "이미 존재하는 값입니다."), code, name)
    if code == "23503":
        if "update or delete on table" in msg:
            default = "다른 데이터가 사용 중이라 삭제할 수 없습니다."
            return InUseError(IN_USE_MESSAGES.get(name, default), code, name)
        return InvalidValueError("참조하는 대상이 존재하지 않습니다.", code, name)
    if code == "23514":
        return InvalidValueError(CONSTRAINT_MESSAGES.get(name, "허용되지 않는 값입니다."), code, name)
    if code == "23502":
        column = re.search(r'column "([^"]+)"', msg)
        return InvalidValueError(f"필수 값이 비어 있습니다: {column.group(1) if column else '?'}", code)
    if code == "42501":
        return PermissionDeniedError("권한이 없습니다. 로그인 상태와 권한을 확인하세요.", code)
    if code == "P0001":
        return BusinessRuleError(msg, code)
    return DatabaseError(f"데이터베이스 오류 ({code}): {msg}", code)


# 데코레이터 생성
def translate_errors(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            raise translate(e) from e

    return wrapper
