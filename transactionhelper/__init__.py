import asyncio
import logging
import math

from pyplanet.apps.config import AppConfig
from pyplanet.contrib.command import Command

from pyplanet.apps.core.maniaplanet import callbacks as mp_signals

logger = logging.getLogger(__name__)


class TransactionHelper(AppConfig):
    # This is a simplified clone of contrib.transactions (commit:7eac67006adaff12cf2151d46aa8d9f33a2737c4)
    # Changes: Removed the widget (and corresponding methods / callbacks) and some chat messages during the /donate process (those are handled by contrib.betmania)

    name = 'pyplanet.apps.contrib.transactionhelper'
    game_dependencies = ['trackmania']
    app_dependencies = ['core.maniaplanet']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.current_bills = dict()
        self.min_donation = 10
        self.lock = asyncio.Lock()

    async def on_start(self):
        await self.instance.permission_manager.register('payout', 'Pay planets to players', app=self, min_level=3)

        await self.instance.command_manager.register(
            Command(command='payout', target=self.payout, perms='transactionhelper:payout', admin=True)
            .add_param(name='login', required=True, type=str)
            .add_param(name='amount', required=True, type=int)
        )

    async def payout(self, player, data, **kwargs):
        try:
            amount = abs(int(data.amount))

            planets = await self.instance.gbx('GetServerPlanets')
            if amount <= (planets - 2 - math.floor(amount * 0.05)):
                async with self.lock:
                    bill_id = await self.instance.gbx('Pay', data.login, amount, 'Bet payout from the server')
                    self.current_bills[bill_id] = dict(bill=bill_id, admin=player, player=data.login, amount=-amount)

        except ValueError:
            await self.instance.chat('$z$s$fff» $i$f00The amount should be a numeric value.', player)
