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
                .add_param(name='amount', required=True, type=int),
            Command(command='payin', target=self.payin).add_param(name='amount', required=True, type=int),
        )

        # Register callback.
        self.context.signals.listen(mp_signals.other.bill_updated, self.bill_updated)

    async def payin(self, player, data, **kwargs):
        try:
            async with self.lock:
                amount = abs(int(data.amount))
                bill_id = await self.instance.gbx('SendBill', player.login, amount,
                                                  'BetMania: Paying {} planets as stake for a bet!'.format(amount), '')
                self.current_bills[bill_id] = dict(bill=bill_id, player=player, amount=amount)

        except ValueError:
            message = '$i$f00The amount should be a numeric value.'
            await self.instance.chat(message, player)

    async def payout(self, player, data, **kwargs):
        try:
            amount = abs(int(data.amount))

            planets = await self.instance.gbx('GetServerPlanets')
            if amount <= (planets - 2 - math.floor(amount * 0.05)):
                async with self.lock:
                    bill_id = await self.instance.gbx('Pay', data.login, amount, 'Bet payout from the server')
                    self.current_bills[bill_id] = dict(bill=bill_id, admin=player, player=data.login, amount=-amount)

        except ValueError:
            message = '$z$s$fff» $i$f00The amount should be a numeric value.'
            await self.instance.chat(message, player)

    async def bill_updated(self, bill_id, state, state_name, transaction_id, **kwargs):
        async with self.lock:
            if bill_id not in self.current_bills:
                logger.debug('BillUpdated for unknown BillId {}: "{}" ({}) (TxId {})'.format(bill_id, state_name, state, transaction_id))
                return

            current_bill = self.current_bills[bill_id]
            logger.debug(
                'BillUpdated for BillId {}: "{}" ({}) (TxId {})'.format(bill_id, state_name, state, transaction_id))

            if state == 4:
                if current_bill['amount'] > 0:
                    message = '$f0fPayment of $fff{}$f0f planets from $fff{}$f0f confirmed!'.format(
                        current_bill['amount'], current_bill['player'].nickname)
                    await self.instance.chat(message, current_bill['admin'].login)
                else:
                    message = '$f0fPayment of $fff{}$f0f planets to $fff{}$f0f confirmed!'.format(
                        -current_bill['amount'], current_bill['player'])
                    await self.instance.chat(message, current_bill['admin'].login)

                del self.current_bills[bill_id]
            elif state == 5:
                if current_bill['amount'] > 0:
                    message = '$i$f00Transaction refused!'
                    await self.instance.chat(message, current_bill['player'].login)
                else:
                    message = '$i$f00Transaction refused!'
                    await self.instance.chat(message, current_bill['admin'].login)

                del self.current_bills[bill_id]
            elif state == 6:
                if current_bill['amount'] > 0:
                    message = '$i$f00Transaction failed: $fff{}$f00!'.format(state_name)
                    await self.instance.chat(message, current_bill['player'].login)
                else:
                    message = '$i$f00Transaction failed: $fff{}$f00!'.format(state_name)
                    await self.instance.chat(message, current_bill['admin'].login)

                del self.current_bills[bill_id]
