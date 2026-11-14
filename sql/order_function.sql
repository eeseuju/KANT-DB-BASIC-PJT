-- 주문 생성·취소를 하나의 트랜잭션으로 처리하는 DB 함수
-- 함수 안에서 오류가 나면(raise exception) 그 함수가 한 일은 전부 취소된다.
-- create or replace 라서 다시 실행해도 된다.


-- 1. 주문 생성
-- p_items 예: [{"product_id": 4, "quantity": 2}, {"product_id": 3, "quantity": 1}]
-- 반환 : 새 주문 id
create or replace function public.create_order(p_user_id uuid, p_items jsonb)
returns bigint
language plpgsql
security definer
set search_path = public
as $$
declare
    v_order_id  bigint;
    v_item      jsonb;
    v_pid       bigint;
    v_qty       integer;
    v_price     integer;
    v_stock     integer;
    v_total     integer := 0;
begin
    -- 0) 권한 검사: 로그인한 본인(또는 관리자)만 만들 수 있다
    if auth.uid() is null then
        raise exception '로그인이 필요합니다.';
    end if;
    if not public.is_admin() and p_user_id is distinct from public.my_user_id() then
        raise exception '다른 회원의 주문은 만들 수 없습니다.';
    end if;

    -- 1) 입력 검사
    if p_items is null or jsonb_typeof(p_items) <> 'array' or jsonb_array_length(p_items) = 0 then
        raise exception '주문 상품이 비어 있습니다.';
    end if;

    if not exists (select 1 from public.users where id = p_user_id and deleted_at is null) then
        raise exception '존재하지 않거나 탈퇴한 회원입니다: %', p_user_id;
    end if;

    -- 2) 주문 만들기 (합계는 마지막에 채운다)
    insert into public.orders (user_id, status, total_amount)
    values (p_user_id, 'pending', 0)
    returning id into v_order_id;

    -- 3) 상품별 처리 (상품 번호 순서로 잠가 교착을 피한다)
    for v_item in
        select value from jsonb_array_elements(p_items)
        order by (value ->> 'product_id')::bigint
    loop
        v_pid := (v_item ->> 'product_id')::bigint;
        v_qty := (v_item ->> 'quantity')::integer;

        if v_qty is null or v_qty <= 0 then
            raise exception '수량은 1 이상이어야 합니다 (상품 %).', v_pid;
        end if;

        select price, stock into v_price, v_stock
        from public.products
        where id = v_pid
        for update;

        if not found then
            raise exception '존재하지 않는 상품입니다: %', v_pid;
        end if;

        if v_stock < v_qty then
            raise exception '재고 부족: 상품 % (재고 %, 주문 %)', v_pid, v_stock, v_qty;
        end if;

        insert into public.order_items (order_id, product_id, quantity, unit_price)
        values (v_order_id, v_pid, v_qty, v_price);

        update public.products
        set stock = stock - v_qty, updated_at = now()
        where id = v_pid;

        v_total := v_total + v_price * v_qty;
    end loop;

    -- 4) 합계 기록
    update public.orders set total_amount = v_total where id = v_order_id;

    return v_order_id;
end;
$$;


-- 2. 주문 취소 (재고 복구)
-- pending, paid 상태의 주문만 취소할 수 있다.
create or replace function public.cancel_order(p_order_id bigint)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
    v_status text;
    v_owner  uuid;
begin
    if auth.uid() is null then
        raise exception '로그인이 필요합니다.';
    end if;

    select status, user_id into v_status, v_owner
    from public.orders
    where id = p_order_id
    for update;

    if not found then
        raise exception '존재하지 않는 주문입니다: %', p_order_id;
    end if;

    if not public.is_admin() and v_owner is distinct from public.my_user_id() then
        raise exception '다른 회원의 주문은 취소할 수 없습니다.';
    end if;

    if v_status not in ('pending', 'paid') then
        raise exception '취소할 수 없는 주문 상태입니다: % (주문 %)', v_status, p_order_id;
    end if;

    update public.products p
    set stock = p.stock + oi.quantity, updated_at = now()
    from public.order_items oi
    where oi.order_id = p_order_id
      and oi.product_id = p.id;

    update public.orders set status = 'canceled' where id = p_order_id;
end;
$$;


-- 3. 실행 권한
revoke execute on function public.create_order(uuid, jsonb) from public, anon;
revoke execute on function public.cancel_order(bigint) from public, anon;
grant  execute on function public.create_order(uuid, jsonb) to authenticated;
grant  execute on function public.cancel_order(bigint) to authenticated;