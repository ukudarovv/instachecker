#!/usr/bin/env python3
import sys
sys.path.append('project')
from models import User, Proxy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def add_proxies():
    # Connect to database
    engine = create_engine('sqlite:///bot.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Get user
    user = session.query(User).filter(User.id == 1972775559).first()
    if not user:
        print('User not found')
        return

    # List of new proxies from the image
    proxies_data = [
        {'host': '142.111.48.253', 'port': 7030, 'country': 'US', 'city': 'Los Angeles'},
        {'host': '31.59.20.176', 'port': 6754, 'country': 'GB', 'city': 'London'},
        {'host': '38.170.176.177', 'port': 5572, 'country': 'US', 'city': 'Los Angeles'},
        {'host': '198.23.239.134', 'port': 6540, 'country': 'US', 'city': 'Buffalo'},
        {'host': '45.38.107.97', 'port': 6014, 'country': 'GB', 'city': 'London'},
        {'host': '107.172.163.27', 'port': 6543, 'country': 'US', 'city': 'Bloomingdale'},
        {'host': '64.137.96.74', 'port': 6641, 'country': 'ES', 'city': 'Madrid'},
        {'host': '216.10.27.159', 'port': 6837, 'country': 'US', 'city': 'Dallas'},
        {'host': '142.111.67.146', 'port': 5611, 'country': 'JP', 'city': 'Tokyo'},
        {'host': '142.147.128.93', 'port': 6593, 'country': 'US', 'city': 'Ashburn'}
    ]

    print(f'Adding {len(proxies_data)} proxies for user {user.id}...')

    # Add proxies
    for i, proxy_data in enumerate(proxies_data):
        proxy = Proxy(
            user_id=user.id,
            scheme='http',
            host=f"{proxy_data['host']}:{proxy_data['port']}",
            username='aiiigauk',
            password='pi8vftb70eic',
            is_active=True,
            priority=i + 1
        )
        session.add(proxy)
        print(f'Added proxy {i+1}: {proxy_data["host"]}:{proxy_data["port"]} ({proxy_data["country"]})')

    session.commit()
    print(f'Successfully added {len(proxies_data)} proxies!')

if __name__ == '__main__':
    add_proxies()
