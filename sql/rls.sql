-- 도우미 함수 + RLS 켜기 + 정책
-- drop policy if exists 후 다시 만들기 때문에 여러 번 실행해도 된다.

-- 1. 도우미 함수
-- 관리자 여부 : 로그인 토큰의 app_metadata.role 이 'admin' 인가
create or replace function public.is_admin()
returns boolean
language sql
stable
as $$
    select coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin'
$$;

-- 내 회원번호 : 로그인 계정과 연결된(그리고 탈퇴하지 않은) users.id
-- security definer: users 의 RLS를 거치지 않고 읽는다(정책 안에서 users를 다시 조회하는 반복을 피한다)
create or replace function public.my_user_id()
returns uuid
language sql
stable
security definer
set search_path = public
as $$
    select id from public.users
    where auth_user_id = auth.uid() and deleted_at is null
$$;

-- 2. RLS 켜기
alter table public.users       enable row level security;
alter table public.products    enable row level security;
alter table public.orders      enable row level security;
alter table public.order_items enable row level security;

-- 3. products : 누구나 읽기, 쓰기는 관리자
drop policy if exists products_select_all on public.products;
create policy products_select_all on public.products
    for select to anon, authenticated
    using (true);

drop policy if exists products_admin_all on public.products;
create policy products_admin_all on public.products
    for all to authenticated
    using (public.is_admin())
    with check (public.is_admin());

-- 4. users : 본인 행만, 관리자는 전체
drop policy if exists users_select_own on public.users;
create policy users_select_own on public.users
    for select to authenticated
    using (auth_user_id = auth.uid() and deleted_at is null);

drop policy if exists users_insert_own on public.users;
create policy users_insert_own on public.users
    for insert to authenticated
    with check (auth_user_id = auth.uid());

drop policy if exists users_update_own on public.users;
create policy users_update_own on public.users
    for update to authenticated
    using (auth_user_id = auth.uid() and deleted_at is null)
    with check (auth_user_id = auth.uid());

drop policy if exists users_admin_all on public.users;
create policy users_admin_all on public.users
    for all to authenticated
    using (public.is_admin())
    with check (public.is_admin());

-- 5. orders : 본인 주문만 읽기, 쓰기는 관리자(회원은 함수로)
drop policy if exists orders_select_own on public.orders;
create policy orders_select_own on public.orders
    for select to authenticated
    using (user_id = public.my_user_id());

drop policy if exists orders_admin_all on public.orders;
create policy orders_admin_all on public.orders
    for all to authenticated
    using (public.is_admin())
    with check (public.is_admin());

-- 6. order_items : 내가 볼 수 있는 주문의 줄만
-- (orders 의 RLS가 이미 본인 주문만 보여 주므로, 그 주문이 보이면 줄도 보인다)
drop policy if exists order_items_select_own on public.order_items;
create policy order_items_select_own on public.order_items
    for select to authenticated
    using (exists (select 1 from public.orders o where o.id = order_items.order_id));

drop policy if exists order_items_admin_all on public.order_items;
create policy order_items_admin_all on public.order_items
    for all to authenticated
    using (public.is_admin())
    with check (public.is_admin());
