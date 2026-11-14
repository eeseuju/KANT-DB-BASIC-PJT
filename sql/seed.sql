-- 시드 데이터
-- 실행하면 기존 데이터를 모두 지우고 새로 넣는다. id 번호도 1부터 다시 시작한다.

truncate table public.order_items, public.orders, public.products, public.users
    restart identity cascade;

-- 회원 3명 (carol은 주문이 없다)
insert into public.users (id, email, name, phone) values
    ('11111111-1111-1111-1111-111111111111', 'user1@test.com', '김하나', '010-0000-0001'),
    ('22222222-2222-2222-2222-222222222222', 'user2@test.com', '박두울', '010-0000-0002'),
    ('33333333-3333-3333-3333-333333333333', 'user3@test.com', '최서이', '010-0000-0003');

-- 상품 5개 (id 1~5 순서대로, 5번은 품절)
insert into public.products (name, price, stock) values
    ('무선 마우스', 25000, 50),
    ('기계식 키보드', 89000, 30),
    ('USB-C 케이블', 9900, 200),
    ('노트북 거치대', 35000, 20),
    ('모니터 받침대', 42000, 0);

-- 주문 3개 (id 1~3 순서대로)
insert into public.orders (user_id, status, total_amount) values
    ('11111111-1111-1111-1111-111111111111', 'paid',    44800),
    ('11111111-1111-1111-1111-111111111111', 'pending', 89000),
    ('22222222-2222-2222-2222-222222222222', 'shipped', 44900);

-- 주문상품 5개 (order_id, product_id, 수량, 단가)
insert into public.order_items (order_id, product_id, quantity, unit_price) values
    (1, 1, 1, 25000),
    (1, 3, 2,  9900),
    (2, 2, 1, 89000),
    (3, 4, 1, 35000),
    (3, 3, 1,  9900);

-- 로그인 계정 연결 : 데모 계정이 있으면 시드 회원 1번과 연결한다. 없으면 NULL로 둔다.
update public.users
set auth_user_id = (select id from auth.users where email = 'demo-user@test.com')
where id = '11111111-1111-1111-1111-111111111111';