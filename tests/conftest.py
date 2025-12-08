"""
Корневой conftest для автоматического импорта всех fixtures.

Pytest автоматически обнаруживает fixtures из conftest.py.
Этот файл импортирует все fixtures из модульных файлов,
делая их доступными для всех тестов.
"""

# Импортируем все shared fixtures (DB, client)
from tests.shared.fixtures.db_fixtures import *  # noqa: F401, F403
from tests.shared.fixtures.client_fixtures import *  # noqa: F401, F403

# Импортируем domain-specific fixtures (users)
from tests.users.fixtures.auth_fixtures import *  # noqa: F401, F403
