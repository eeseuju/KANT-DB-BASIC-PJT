-- 쇼핑몰 테이블을 전부 삭제 (DROP) / 처음부터 다시 만들고 싶을 때만 실행한다.
-- 순서 : 자식 -> 부모 (FK 때문에 부모를 먼저 지우면 오류가 발생하기 때문)

drop table if exists public.order_items cascade;
drop table if exists public.orders cascade;
drop table if exists public.products cascade;
drop table if exists public.users cascade;