
# Импортируем все shared fixtures (DB, client)
from tests.shared.fixtures.db_fixtures import *  # noqa: F401, F403
from tests.shared.fixtures.client_fixtures import *  # noqa: F401, F403

# Импортируем domain-specific fixtures (users)
from tests.users.fixtures.auth_fixtures import *  # noqa: F401, F403
