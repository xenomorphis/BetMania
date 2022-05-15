import asyncio

from pyplanet.apps.config import AppConfig
from pyplanet.contrib.command import Command
from pyplanet.apps.core.maniaplanet import callbacks as mp_signals


class BetMania(AppConfig):
    # default settings
    name = 'pyplanet.apps.contrib.betmania'
    game_dependencies = ['trackmania']
    app_dependencies = ['core.maniaplanet', 'transactionhelper']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Init vars
        self.bet_open = False
        self.bet_current = False
        self.bets = dict()
        self.stack = dict()
        self.supporters = dict()
        self.teams = ['blue', 'red']   # TODO: Fill list with items from the current configuration
        self.waiting = dict()

        self.lock = asyncio.Lock()

    async def on_start(self):
        # Sets command permissions
        await self.instance.permission_manager.register('open_bet', 'Opens a new bet.', app=self, min_level=1)
        await self.instance.permission_manager.register('close_bet', 'Closes an open bet.', app=self, min_level=1)
        await self.instance.permission_manager.register('resolve_bet', 'Resolves a bet.', app=self, min_level=3)

        # Registers available chat commands
        await self.instance.command_manager.register(
            Command(command='openbet', target=self.open_bet, perms='betmania:open_bet', admin=True,
                    description='Opens up a new bet and clears all related variables.'),
            Command(command='closebet', target=self.close_bet, perms='betmania:close_bet', admin=True,
                    description='Closes an open bet and prevents players from placing new bets.'),
            Command(command='resolvebet', aliases=['resolve'], target=self.resolve_bet, perms='betmania:resolve_bet',
                    admin=True, description='Closes and resolves a bet.')
                .add_param(name='team', required=True, type=str, help='Plase specify the winning team (blue / red)'),
            Command(command='resetbet', target=self.reset_bet, perms='betmania:resolve_bet', admin=True,
                    description='Resets an already opened bet. Use only when necessary!'),
            Command(command='bet', target=self.place_bet, description='Places a configurable amount of planets on a bet.')
                .add_param(name='amount', required=True, type=int, help='Enter here how many planets you want to bet')
                .add_param(name='team', required=True, type=str, help='Enter the team you want to bet for. You\'ll receive a playout if your specified team wins (blue / red).'),
            Command(command='quota', target=self.show_bet_quota,
                    description='Returns the current payout quotas for both teams.'),
            Command(command='bmdebug', target=self.debug, perms='betmania:resolve_bet', admin=True,
                    description='For development purposes.'),
            Command(command='betmania', target=self.betmania_info, description='Displays intro message'),
        )

        for team in self.teams:
            self.supporters[team] = dict()
            self.stack[team] = 0

        # Register callback.
        self.context.signals.listen(mp_signals.other.bill_updated, self.receive_bet)

        await self.instance.chat('$s$FFF//Bet$1EFMania $FFFBetting System v$FF00.2.0 $FFF(Subsystem v2) online')

    async def open_bet(self, player, data, **kwargs):
        if not self.bet_current:
            # Initializes vars and sets bet to open (it's more or less an init-function)
            self.bet_open = True
            self.bet_current = True
            self.bets.clear()

            for team in self.teams:
                self.supporters[team].clear()
                self.stack[team] = 0

            self.waiting.clear()

            await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: BET IS NOW OPEN! //')
            await self.instance.chat(
                'A bet has been opened. Place your stakes now with \'/bet XXX red\' or \'/bet XXX blue\'. Good luck!')
        else:
            await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: Reivously unresolved bet found. I\'ll reopen that... //', player)
            self.bet_open = True
            await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: BET HAS BEEN REOPENED! //')

    async def close_bet(self, player, data, **kwargs):
        # Sets bet to closed without resolving it
        if self.bet_open:
            self.bet_open = False
            await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: BET IS NOW CLOSED!')
        else:
            await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: We don\'t have an active bet at the moment.', player)

    async def resolve_bet(self, player, data, **kwargs):
        # Sets bet to closed and immediately resolves it
        if self.bet_current:
            self.bet_open = False

            if data.team in self.teams:
                # data.team contains the winning team as provided by /resolve <team>
                stake = self.calc_stake()

                str_team_format = {
                    'red': '$s$F00',
                    'blue': '$s$00F'
                }

                if self.stack[data.team] > 0:
                    quota = round(stake / self.stack[data.team], 3)

                    await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: BET PAYOUTS!!!')

                    await self.instance.chat(
                        '$s$FFF//Bet$1EFMania$FFF: Team {}{} $FFFhas won the tournament. Quota was {}.'
                            .format(str_team_format[data.team], data.team, str(quota)))

                    for supporter in self.supporters[data.team]:
                        payout = round(self.supporters[data.team][supporter] * quota)

                        await self.instance.chat(
                            '$s$FFF//Bet$1EFMania$FFF: Congrats! Team {}{} $FFFwon. You receive $222{} $FFFplanets as your bet payout.'
                                .format(str_team_format[data.team], data.team, str(payout)), supporter)
                        await self.instance.command_manager.execute(player, '//payout', supporter, str(payout))

                else:
                    await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: Total stake is zero, no payout this time!')

                self.bet_current = False
            else:
                await self.instance.chat(
                    '$s$FFF//Bet$1EFMania$FFF: Please specify the winning team. Allowed arguments are \'blue\' and \'red\'',
                    player)
        else:
            await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: There\'s no available bet at the moment that could be resolved.',
                                     player)

    async def reset_bet(self, player, data, **kwargs):
        # Resets a bet and returns all bets to the respective players
        if self.bet_current:
            self.bet_open = False
            self.bet_current = False
            self.bets.clear()

            for team in self.teams:
                for supporter in self.supporters[team]:
                    payout = self.supporters[team][supporter]
                    await self.instance.command_manager.execute(player, '//payout', supporter, str(payout))
                self.supporters[team].clear()
                self.stack[team] = 0

            await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: BET IS CANCELLED! You\'ll receive your Planets back.')
        else:
            await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: There\'s nothing to reset...', player)

    async def show_bet_quota(self, player, data, **kwargs):
        # Outputs the current payout quotas for each team
        if self.bet_current:
            stake = self.calc_stake()

            for team in self.teams:
                if self.stack[team] > 0:
                    quota = round(stake / self.stack[team], 3)
                    await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: Quota for $CCC{} $FFFWin is {}'
                                             .format(team, str(quota)), player)
                else:
                    await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: No current Quota for Team $CCC{} $FFFWin'
                                             .format(team), player)

        else:
            await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: We don\'t have an active bet at the moment.', player)

    async def place_bet(self, player, data, **kwargs):
        # Checks first if bet is open. Allows player to bet planets via donating them (works the same way)
        if self.bet_open:
            if data.team in self.teams:
                self.waiting['player'] = player
                self.waiting['amount'] = data.amount
                self.waiting['team'] = data.team

                await self.instance.command_manager.execute(player, '/payin', str(data.amount))
            else:
                await self.instance.chat(
                    '$s$FFF//Bet$1EFMania$FFF: Please specify the team you want to place your bet on. Allowed arguments are \'blue\' and \'red\'',
                    player)
        else:
            await self.instance.chat(
                '$s$FFF//Bet$1EFMania$FFF: There\'s no open bet at the moment. Please try again later (or ask an ServerOp to open one ;)',
                player)

    async def receive_bet(self, bill_id, state, state_name, transaction_id, **kwargs):
        # Callback method when bill_updated signal is received. Ensures that the BetMania vars are only updated if a payment has occured
        if (len(self.waiting) > 0) or (bill_id in self.bets):
            if bill_id not in self.bets:
                self.bets[bill_id] = {
                    'player': self.waiting['player'],
                    'amount': self.waiting['amount'],
                    'team': self.waiting['team']
                }

                self.waiting.clear()

            async with self.lock:
                if state == 4:
                    await self.instance.chat(
                        '$s$FFF//Bet$1EFMania$FFF: {} $FFFhas placed a bet of $s$FE1{} $FFFplanets on team {}.'
                            .format(self.bets[bill_id]['player'].nickname, str(self.bets[bill_id]['amount']), self.bets[bill_id]['team']))

                    self.stack[self.bets[bill_id]['team']] += self.bets[bill_id]['amount']

                    if self.bets[bill_id]['player'].login in self.supporters[self.bets[bill_id]['team']]:
                        self.supporters[self.bets[bill_id]['team']][self.bets[bill_id]['player'].login] += self.bets[bill_id]['amount']
                    else:
                        self.supporters[self.bets[bill_id]['team']][self.bets[bill_id]['player'].login] = self.bets[bill_id]['amount']

                    del self.bets[bill_id]
                elif state > 4:
                    await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: Transaction refused or failed! No bet was placed!',
                                             self.bets[bill_id]['player'])
                    del self.bets[bill_id]

    async def betmania_info(self, player, data, **kwargs):
        await self.instance.chat('$s$FFF//Bet$1EFMania $FFFBetting System v$FF00.2.0 $FFF(Subsystem v2)', player)

        if player.level == 0:
            await self.instance.chat('$s$1EF/bet <amount> <team>$FFF: $iBets an individual amount of planets on a team.', player)
            await self.instance.chat('$s$1EF/quota$FFF: $iShows the current payout quotas for each possible result.', player)

        if player.level > 0:
            await self.instance.chat('$s$1EF//openbet$FFF: $iOpens up a new bet or reopens a closed one.', player)
            await self.instance.chat('$s$1EF//closebet$FFF: $iCloses an existing bet for new entries.', player)

        if player.level == 3:
            await self.instance.chat('$s$1EF//resolvebet$FFF: $iCloses and resolves an open bet.', player)
            await self.instance.chat('$s$1EF//resetbet$FFF: $iResets an open bet. Players get their payins refunded.', player)

    def calc_stake(self):
        stake = 0

        for team in self.teams:
            stake += self.stack[team]

        return stake

    async def debug(self, player, data, **kwargs):
        await self.instance.chat('$FFFbet_open: $000{} $FFF// bet_current: $000{} $FFF// stack_red: $F00{} $FFF// stack_blue: $00F{}'
                                 .format(str(self.bet_open), str(self.bet_current), str(self.stack['red']), str(self.stack['blue'])),
                                 player)
        await self.instance.chat('$FFFEntries in supporters_red: $F00{} $FFF// Entries in supporters_blue: $00F{}'
                                 .format(str(len(self.supporters['red'])), str(len(self.supporters['blue']))), player)
        await self.instance.chat('$FFFEntries in supporters_red: $F00{}'.format(str(self.supporters['red'])), player)
