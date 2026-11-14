-- 시드 주입 직후 기준 트랜잭션 COMMIT / ROLLBACK 시나리오

-- 0. 시작 전 상태
select id, name, stock from public.products order by id;
select count(*) as orders_count from public.orders;

-- 1. 성공 시나리오 : 주문 생성 후 COMMIT
-- 회원 1이 노트북 거치대(4) 2개와 USB-C 케이블(3) 1개를 주문한다.
-- 주문 저장 + 주문상품 저장 + 재고 차감 + 합계 기록이 모두 성공해야 확정한다.
begin;

insert into public.orders (user_id, status, total_amount)
values ('11111111-1111-1111-1111-111111111111', 'pending', 0);

insert into public.order_items (order_id, product_id, quantity, unit_price) values
    (currval(pg_get_serial_sequence('public.orders', 'id')), 4, 2, 35000),
    (currval(pg_get_serial_sequence('public.orders', 'id')), 3, 1,  9900);

update public.products set stock = stock - 2 where id = 4;
update public.products set stock = stock - 1 where id = 3;

update public.orders
set total_amount = 2 * 35000 + 1 * 9900
where id = currval(pg_get_serial_sequence('public.orders', 'id'));

commit;

-- 1-검증. COMMIT 결과 확인 (별도 Run)
-- 기대 : 새 주문 total_amount = items_total = 79900, 재고 3번 199 / 4번 18, 주문 4개
select o.id, o.status, o.total_amount, sum(oi.quantity * oi.unit_price) as items_total
from public.orders o
join public.order_items oi on oi.order_id = o.id
group by o.id, o.status, o.total_amount
order by o.id desc
limit 1;

select id, name, stock from public.products where id in (3, 4) order by id;
select count(*) as orders_count from public.orders;

-- 2. ROLLBACK 시나리오 : 변경했다가 일부러 취소
begin;
update public.products set stock = stock - 5 where id = 1;
rollback;

-- 2-검증. ROLLBACK 결과 확인 (별도 Run)
-- 기대 : 1번 상품 재고가 50 그대로 남아있다. 재고가 45가 되지 않았다.
select id, name, stock from public.products where id = 1;

-- 3. 실패 재현 : 중간에 오류가 나면 앞의 변경도 함께 취소된다.
-- 1번 상품 재고 차감은 성공하지만, 2번째 문장은 재고 0인 5번 상품을 100개 빼려다 CHECK 위반으로 실패한다.
begin;
update public.products set stock = stock - 1   where id = 1;   -- 성공(이 트랜잭션 안에서만)
update public.products set stock = stock - 100 where id = 5;   -- 오류: ck_products_stock_nonneg
update public.products set stock = stock - 1   where id = 2;   -- 실행되지 않는다
commit;

-- 3-검증. 부분 반영이 없는지 확인 (별도 Run)
-- 기대 : 1번 50, 2번 30, 5번 0 (모두 원래 값). 1번이 49가 되었다면 정합성이 깨진 것이다.
rollback;
select id, name, stock from public.products where id in (1, 2, 5) order by id;
