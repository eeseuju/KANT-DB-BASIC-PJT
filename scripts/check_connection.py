from shoppingmall_db.client import get_client

TABLES = ['users', 'products', 'orders', 'order_items']

def main() -> None:
    try:
        client = get_client()
        for table in TABLES:
            res = client.table(table).select('*', count='exact').limit(1).execute()
            print(f'{table}: {res.count}행')
    except Exception as e:
        print(f'연결확인실패: {type(e).__name__}: {e}')
        raise SystemExit(1)

if __name__ == '__main__':
    main()