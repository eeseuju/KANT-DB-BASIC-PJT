-- 1. 회원
create table public.users (
    id            uuid         not null default gen_random_uuid(),
    email         text         not null,
    name          text         not null,
    phone         text,
    created_at    timestamptz  not null default now(),
    deleted_at    timestamptz,
    auth_user_id  uuid,
    constraint pk_users primary key (id),
    constraint uq_users_email unique (email),
    constraint uq_users_auth_user_id unique (auth_user_id),
    constraint fk_users_auth_users foreign key (auth_user_id)
        references auth.users (id) on delete set null
);

-- 2. 상품
create table public.products (
    id          bigint         generated always as identity,
    name        text           not null,
    price       integer        not null,
    stock       integer        not null default 0,
    created_at  timestamptz    not null default now(),
    constraint pk_products primary key (id),
    constraint ck_products_name_not_blank check (length(trim(name)) > 0),
    constraint ck_products_price_nonneg   check (price >= 0),
    constraint ck_products_stock_nonneg   check (stock >= 0)
);

-- 3. 주문
create table public.orders (
    id            bigint         generated always as identity,
    user_id       uuid           not null,
    status        text           not null default 'pending',
    total_amount  integer        not null default 0,
    created_at    timestamptz    not null default now(),
    constraint pk_orders primary key (id),
    constraint fk_orders_users foreign key (user_id)
        references public.users (id) on delete restrict,
    constraint ck_orders_status check (status in ('pending', 'paid', 'shipped', 'canceled')),
    constraint ck_orders_total_nonneg check (total_amount >= 0)
);

-- 4. 주문상품 (주문 1개에 상품 여러 개)
create table public.order_items (
    id          bigint         generated always as identity,
    order_id    bigint         not null,
    product_id  bigint         not null,
    quantity    integer        not null,
    unit_price  integer        not null,
    constraint pk_order_items primary key (id),
    constraint fk_order_items_orders foreign key (order_id)
        references public.orders (id) on delete cascade,
    constraint fk_order_items_products foreign key (product_id)
        references public.products (id) on delete restrict,
    constraint uq_order_items_order_product unique (order_id, product_id),
    constraint ck_order_items_quantity_positive check (quantity > 0),
    constraint ck_order_items_unit_price_nonneg check (unit_price >= 0)
);

-- 5. 인덱스 (FK로 자주 찾는 컬럼)
create index idx_orders_user_id on public.orders (user_id);
create index idx_order_items_product_id on public.order_items (product_id);

-- 6. 변경 (ALTER)
alter table public.products
    add column updated_at timestamptz not null default now();

alter table public.users
    add constraint ck_users_email_format check (email like '%@%');