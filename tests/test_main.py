from unittest.mock import patch

from app import main
from tests import AsyncMock, AsyncTestCase, Mock


class TestStartUp(AsyncTestCase):
    @patch('app.persistence.database.pg_pool_handler.initialize', new_callable=AsyncMock)
    @patch('app.persistence.email.smtp_handler.initialize', new_callable=AsyncMock)
    @patch('app.client.oauth.oauth_handler.initialize', new_callable=Mock)
    @patch('app.persistence.file_storage.gcs.gcs_handler.initialize', new_callable=Mock)
    async def test_happy_path(self, mock_gcs: Mock, mock_oauth: Mock, mock_smtp: AsyncMock, mock_pg: AsyncMock):
        await main.app_startup()

        mock_pg.assert_called_once()
        mock_smtp.assert_called_once()
        mock_oauth.assert_called_once()
        mock_gcs.assert_called_once()


class TestShutDown(AsyncTestCase):
    @patch('app.persistence.database.pg_pool_handler.close', new_callable=AsyncMock)
    @patch('app.persistence.email.smtp_handler.close', new_callable=AsyncMock)
    async def test_happy_path(self, mock_smtp: AsyncMock, mock_pg: AsyncMock):
        await main.app_shutdown()

        mock_pg.assert_called_once()
        mock_smtp.assert_called_once()
