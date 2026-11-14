-- INSERT / UPDATE / DELETE 와 제약 위반 검증



-- A. 변경 전 상태
select * from public.products order by id;



-- B. INSERT

-- B-01. 상품 추가 (RETURNING으로 바로 확인)
insert into public.products (name, price, stock)
values ('테스트 상품', 10000, 5)
returning *;

-- B-02. 회원 추가
insert into public.users (email, name, phone)
values ('user4@test.com', '정임시', '010-0000-0004')
returning *;

-- B-03. 검증: seed 기준 products 6개, users 4개가 되어야 한다
select (select count(*) from public.products) as products_count,
       (select count(*) from public.users) as users_count;



-- C. UPDATE

-- C-01. 변경 전
select id, name, price, stock from public.products where name = '테스트 상품';

-- C-02. 가격과 재고 수정
update public.products
set price = 12000, stock = stock - 1, updated_at = now()
where name = '테스트 상품'
returning id, name, price, stock, updated_at;

-- C-03. 주문 상태 변경 (2번 주문 pending -> paid)
select id, status from public.orders where id = 2;
update public.orders set status = 'paid' where id = 2 returning id, status;



-- D. DELETE

-- D-01. 방금 추가한 상품과 회원 삭제 : 다른 데이터가 참조하지 않아서 삭제된다.
delete from public.products where name = '테스트 상품' returning *;
delete from public.users where email = 'user4@test.com' returning *;

-- D-02. 검증: products 5개, users 3개로 돌아와야 한다
select (select count(*) from public.products) as products_count,
       (select count(*) from public.users) as users_count;



-- E. 제약 위반 테스트

-- E-01. 가격이 음수 -> ck_products_price_nonneg
insert into public.products (name, price, stock) values ('음수 가격', -1, 1);

-- E-02. 이름이 공백 -> ck_products_name_not_blank
insert into public.products (name, price, stock) values ('   ', 1000, 1);

-- E-03. 이름이 비어 있음(NULL) -> not-null 위반
insert into public.products (name, price, stock) values (null, 1000, 1);

-- E-04. 이메일 중복 -> uq_users_email
insert into public.users (email, name)
select email, '중복' from public.users order by id limit 1;

-- E-05. 이메일 형식 오류 -> ck_users_email_format
insert into public.users (email, name) values ('abc', '형식오류');

-- E-06. 주문 상태가 규칙 밖 -> ck_orders_status
insert into public.orders (user_id, status, total_amount)
select id, 'unknown', 0 from public.users order by id limit 1;

-- E-07. 없는 회원의 주문 -> fk_orders_users
insert into public.orders (user_id, status, total_amount)
values ('99999999-9999-9999-9999-999999999999', 'pending', 0);

-- E-08. 수량이 0 -> ck_order_items_quantity_positive
insert into public.order_items (order_id, product_id, quantity, unit_price)
select o.id, p.id, 0, p.price
from public.orders o cross join public.products p
order by o.id, p.id limit 1;

-- E-09. 주문이 있는 회원 삭제 -> fk_orders_users (on delete restrict)
-- 주문이 있는 회원들을 모두 지우려 시도한다. 하나라도 막히면 오류가 난다.
delete from public.users where id in (select user_id from public.orders);

-- E-10. 주문된 상품 삭제 -> fk_order_items_products (on delete restrict)
-- 주문된 상품들을 모두 지우려 시도한다. 하나라도 막히면 오류가 난다.
delete from public.products where id in (select product_id from public.order_items);

-- E-11. 같은 주문에 같은 상품 줄을 또 추가 -> uq_order_items_order_product
-- DB는 같은 주문에 같은 상품 줄이 두 개 생기는 것을 막는다. (줄이 아닌 주문수량이 늘어나야 하기 때문에)
insert into public.order_items (order_id, product_id, quantity, unit_price)
select order_id, product_id, quantity, unit_price
from public.order_items order by id limit 1;

-- E-11-1. 첫 번째 주문상품의 수량 확인
select id, order_id, product_id, quantity
from public.order_items order by id limit 1;

-- E-11-2. 같은 상품을 1개 더 담기 (quantity +1)
insert into public.order_items (order_id, product_id, quantity, unit_price)
select order_id, product_id, 1, unit_price
from public.order_items order by id limit 1
on conflict (order_id, product_id)
do update set quantity = public.order_items.quantity + excluded.quantity
returning id, order_id, product_id, quantity;

-- E-11-3. 행 개수는 그대로 5개, 첫 줄의 quantity만 1 늘어나 있어야 한다.
select count(*) as items_count from public.order_items;
select id, order_id, product_id, quantity
from public.order_items order by id limit 1;