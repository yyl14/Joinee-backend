from app.base import do, enums, vo
from app.persistence.database import reservation_member
from tests import AsyncMock, AsyncTestCase, Mock, patch


class TestBatchAddWithDo(AsyncTestCase):
    def setUp(self) -> None:
        self.reservation_id = 1
        self.member_ids = [1, 2]
        self.members = [
            do.ReservationMember(
                reservation_id=self.reservation_id,
                account_id=1,
                is_manager=True,
                source=enums.ReservationMemberSource.invitation_code,
                status=enums.ReservationMemberStatus.invited,
            ),
            do.ReservationMember(
                reservation_id=self.reservation_id,
                account_id=2,
                is_manager=False,
                source=enums.ReservationMemberSource.invitation_code,
                status=enums.ReservationMemberStatus.invited,
            ),
        ]
        self.params = {
            'reservation_id_0': self.reservation_id, 'account_id_0': 1, 'is_manager_0': True,
            'status_0': enums.ReservationMemberStatus.invited,
            'source_0': enums.ReservationMemberSource.invitation_code,

            'reservation_id_1': self.reservation_id, 'account_id_1': 2, 'is_manager_1': False,
            'status_1': enums.ReservationMemberStatus.invited,
            'source_1': enums.ReservationMemberSource.invitation_code,
        }

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_happy_path(self, mock_execute: AsyncMock, mock_init: Mock):
        mock_execute.return_value = None

        result = await reservation_member.batch_add_with_do(
            members=self.members,
        )

        self.assertIsNone(result)

        mock_init.assert_called_with(
            sql=r'INSERT INTO reservation_member'
                r'            (reservation_id, account_id, is_manager, status, source)'
                r'     VALUES (%(reservation_id_0)s, %(account_id_0)s, %(is_manager_0)s, %(status_0)s, %(source_0)s),'
                r' (%(reservation_id_1)s, %(account_id_1)s, %(is_manager_1)s, %(status_1)s, %(source_1)s)',
            **self.params,
        )


class TestBrowse(AsyncTestCase):
    def setUp(self) -> None:
        self.reservation_id = 1
        self.account_id = 1
        self.params = {
            'account_id': self.account_id,
            'reservation_id': self.reservation_id,
        }
        self.raw_reservation_members = [
            (1, 1, True, 'INVITED', 'INVITATION_CODE', 'nickname'),
        ]
        self.reservation_members = [
            vo.ReservationMemberWithName(
                reservation_id=1,
                account_id=1,
                is_manager=True,
                source=enums.ReservationMemberSource.invitation_code,
                status=enums.ReservationMemberStatus.invited,
                nickname='nickname',
            ),
        ]

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_all', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_reservation_members

        result = await reservation_member.browse_with_names(
            account_id=self.account_id,
            reservation_id=self.reservation_id,
        )

        self.assertEqual(result, self.reservation_members)
        mock_init.assert_called_with(
            sql=r'SELECT reservation_id, account_id, is_manager, status, source, nickname'
                r'  FROM reservation_member'
                r' INNER JOIN account'
                r'    ON reservation_member.account_id = account.id'
                r' WHERE reservation_id = %(reservation_id)s'
                r' AND account_id = %(account_id)s'
                r' ORDER BY is_manager, account_id',
            **self.params,
        )


class TestReject(AsyncTestCase):
    def setUp(self) -> None:
        self.reservation_id = 1
        self.account_id = 1

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_happy_path(self, mock_execute: AsyncMock, mock_init: Mock):
        mock_execute.return_value = None

        result = await reservation_member.reject(
            account_id=self.account_id,
            reservation_id=self.reservation_id,
        )

        self.assertIsNone(result)
        mock_init.assert_called_with(
            sql=r"UPDATE reservation_member"
                r"   SET status = %(status)s"
                r" WHERE reservation_id = %(reservation_id)s and account_id = %(account_id)s",
            reservation_id=self.reservation_id, account_id=self.account_id, status=enums.ReservationMemberStatus.rejected,
        )


class TestRead(AsyncTestCase):
    def setUp(self) -> None:
        self.reservation_id = 1
        self.account_id = 1

        self.raw_member = 1, 1, False, enums.ReservationMemberStatus.invited, enums.ReservationMemberSource.invitation_code

        self.member = do.ReservationMember(
            reservation_id=self.reservation_id,
            account_id=self.account_id,
            is_manager=False,
            status=enums.ReservationMemberStatus.invited,
            source=enums.ReservationMemberSource.invitation_code,
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_member

        result = await reservation_member.read(
            account_id=self.account_id,
            reservation_id=self.reservation_id,
        )

        self.assertEqual(result, self.member)
        mock_init.assert_called_with(
            sql=r'SELECT reservation_id, account_id, is_manager, status, source'
                r'  FROM reservation_member'
                r' WHERE reservation_id = %(reservation_id)s and account_id = %(account_id)s',
            reservation_id=self.reservation_id, account_id=self.account_id,
        )
