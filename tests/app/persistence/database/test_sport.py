from unittest.mock import patch

from app.base import do
from app.persistence.database import sport
from tests import AsyncMock, AsyncTestCase, Mock


class TestBrowse(AsyncTestCase):
    def setUp(self) -> None:
        self.raw_sport = [
            (1, '桌球'),
            (2, '羽球'),
        ]
        self.sports = [
            do.Sport(
                id=1,
                name='桌球',
            ),
            do.Sport(
                id=2,
                name='羽球',
            ),
        ]

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_all', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_sport

        result = await sport.browse()

        self.assertEqual(result, self.sports)
        mock_init.assert_called_with(
            sql=r'SELECT sport.id, sport.name'
                r'  FROM sport',
        )


class TestRead(AsyncTestCase):
    def setUp(self):
        self.sport_id = 1
        self.raw_sport = 1, 'name'
        self.sport = do.Sport(id=1, name='name')

    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch: AsyncMock):
        mock_fetch.return_value = self.raw_sport

        result = await sport.read(sport_id=self.sport_id)

        self.assertEqual(result, self.sport)
