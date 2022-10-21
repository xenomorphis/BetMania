import asyncio

from pyplanet.apps.config import AppConfig
from .views import SupportersListView
from pyplanet.contrib.command import Command
from pyplanet.contrib.setting import Setting

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
        self.min_bet = 1
        self.reconfigure = False
        self.stack = dict()
        self.supporters = dict()
        self.teams = list()
        self.team_colors = dict()
        self.waiting = dict()

        self.lock = asyncio.Lock()

        self.setting_bet_config_teams = Setting(
            'bet_config_teams', 'Configure the available betting targets (teams)', Setting.CAT_BEHAVIOUR, type=str,
            description='Configure the available betting targets (teams).',
            default='blue,red', change_target=self.reconfigure_teams
        )

        self.setting_bet_config_team_colors = Setting(
            'bet_config_team_colors', 'Configure the highlighting colors for each team', Setting.CAT_BEHAVIOUR, type=str,
            description='Configure the highlighting colors for each team.',
            default='$s$00F,$s$F00', change_target=self.reconfigure_teams
        )

        self.setting_bet_margin = Setting(
            'bet_margin', 'Sets the server margin for all bets.', Setting.CAT_BEHAVIOUR, type=int,
            description='Defines the amount of planets deducted as transaction fees from the total stake before a bet payout. Use values between 1 and 100 if bet_margin_relative is activated.',
            default=0,
        )

        self.setting_bet_margin_relative = Setting(
            'bet_margin_relative', 'Use bet_margin as a relative amount', Setting.CAT_BEHAVIOUR, type=bool,
            description='If activated, bet_margin is handled as a relative amount (xx % of the stake). By default bet_margin will be used as an absolute amount (xxx planets).',
            default=False,
        )

        self.setting_bet_minimum_stake = Setting(
            'bet_minimum_stake', 'Sets the minimum amount of planets needed for placing a bet.', Setting.CAT_BEHAVIOUR,
            type=int, description='Defines the minimum amount of planets needed for placing a bet. A value of 1 accepts all stakes.',
            default=1,
        )

        self.setting_show_widget = Setting(
            'bet_show_widget', 'Shows / Hides the BetMania widget', Setting.CAT_BEHAVIOUR, type=bool,
            description='Shows / Hides the BetMania widget (currently not used).',
            default=False, change_target=self.toggle_widget
        )

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
            Command(command='bet', target=self.place_bet,
                    description='Places a configurable amount of planets on a bet.')
            .add_param(name='amount', required=True, type=int, help='Enter here how many planets you want to bet')
            .add_param(name='team', required=True, type=str,
                       help='Enter the team you want to bet for. You\'ll receive a playout if your specified team wins (blue / red).'),
            Command(command='quota', target=self.show_bet_quota,
                    description='Returns the current payout quotas for both teams.'),
            Command(command='supporters', target=self.show_supporters,
                    description='Shows a list of all current supporters of a specified team.')
            .add_param(name='team', required=True, type=str, help='Enter which teams supporters you want to see.'),
            Command(command='bmdebug', target=self.debug, perms='betmania:resolve_bet', admin=True,
                    description='For development purposes.'),
            Command(command='betmania', target=self.betmania_info, description='Displays intro message'),
        )

        await self.context.setting.register(self.setting_bet_config_teams, self.setting_bet_config_team_colors,
                                            self.setting_bet_margin, self.setting_bet_margin_relative,
                                            self.setting_bet_minimum_stake, self.setting_show_widget)

        await self.reconfigure_teams()

        # Register callback.
        self.context.signals.listen(mp_signals.other.bill_updated, self.receive_bet)

        await self.instance.chat('$s$FFF//Bet$1EFMania $FFFBetting System v$FF00.2.1 $FFF(Subsystem v2) online')

    async def open_bet(self, player, data, **kwargs):
        if not self.bet_current:
            # Initializes vars and sets bet to open (it's more or less an init-function)
            self.bet_open = True
            self.bet_current = True
            self.bets.clear()
            self.min_bet = await self.setting_bet_minimum_stake.get_value()

            if self.reconfigure:
                self.reconfigure = False
                new_config = await self.setting_bet_config_teams.get_value()
                self.teams = new_config.split(',')

                for team in self.teams:
                    self.supporters[team] = dict()
                    self.stack[team] = 0
            else:
                for team in self.teams:
                    self.supporters[team].clear()
                    self.stack[team] = 0

            self.waiting.clear()

            await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: BET IS NOW OPEN! //')
            await self.instance.chat(
                '$FFFA bet has been opened. Place your stakes now with \'/bet XXX red\' or \'/bet XXX blue\'. '
                'Minimum stake for this bet is $1EF{} $FFFplanets. Good luck!'.format(self.min_bet))

        else:
            await self.instance.chat(
                '$s$FFF//Bet$1EFMania$FFF: Reivously unresolved bet found. I\'ll reopen that... //', player)
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

                if self.stack[data.team] > 0:
                    quota = round(stake / self.stack[data.team], 3)

                    await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: BET PAYOUTS!!!')

                    await self.instance.chat(
                        '$s$FFF//Bet$1EFMania$FFF: Team {}{} $FFFhas won the tournament. Quota was {}.'
                        .format(self.team_colors[data.team], data.team, str(quota)))

                    for supporter in self.supporters[data.team]:
                        payout = round(self.supporters[data.team][supporter] * quota)

                        await self.instance.chat(
                            '$s$FFF//Bet$1EFMania$FFF: Congrats! Team {}{} $FFFwon. You receive $222{} $FFFplanets as your bet payout.'
                            .format(self.team_colors[data.team], data.team, str(payout)), supporter)
                        await self.instance.command_manager.execute(player, '//payout', supporter, str(payout))

                else:
                    await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: Total stake is zero, no payout this time!')

                self.bet_current = False
            else:
                await self.instance.chat(
                    '$s$FFF//Bet$1EFMania$FFF: Please specify the winning team. Allowed arguments are \'blue\' and \'red\'',
                    player)
        else:
            await self.instance.chat(
                '$s$FFF//Bet$1EFMania$FFF: There\'s no available bet at the moment that could be resolved.',
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

    async def show_supporters(self, player, data, **kwargs):
        if data.team in self.teams:
            if self.stack[data.team] > 0:
                view = SupportersListView(self, data.team)
                await view.display(player.login)
            else:
                await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: Team {}{} $FFFhas  currently no supporters :('
                                         .format(self.team_colors[data.team], data.team), player)

        else:
            await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: There\'s no $CCC{} $FFFteam.'.format(data.team), player)

    async def place_bet(self, player, data, **kwargs):
        # Checks first if bet is open. Allows player to bet planets via donating them (works the same way)
        if self.bet_open:
            if data.team in self.teams:
                self.waiting['player'] = player
                self.waiting['amount'] = data.amount
                self.waiting['team'] = data.team

                if data.amount >= self.min_bet:
                    bet_allowed = True

                    for team in self.teams:
                        if team == data.team:
                            continue

                        if player.login in self.supporters[team]:
                            bet_allowed = False
                            await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: You have already supported a team, '
                                                     'thus you can\'t support a second one. Bet rejected.', player)
                            break

                    if bet_allowed:
                        await self.instance.command_manager.execute(player, '/payin', str(data.amount))

                else:
                    await self.instance.chat(
                        '$s$FFF//Bet$1EFMania$FFF: Your stake is not high enough. Current minimum stake is {} planets.'
                        .format(self.min_bet), player)

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
                        .format(self.bets[bill_id]['player'].nickname, str(self.bets[bill_id]['amount']),
                                self.bets[bill_id]['team']))

                    self.stack[self.bets[bill_id]['team']] += self.bets[bill_id]['amount']

                    if self.bets[bill_id]['player'].login in self.supporters[self.bets[bill_id]['team']]:
                        self.supporters[self.bets[bill_id]['team']][self.bets[bill_id]['player'].login] += self.bets[bill_id]['amount']
                    else:
                        self.supporters[self.bets[bill_id]['team']][self.bets[bill_id]['player'].login] = self.bets[bill_id]['amount']

                    del self.bets[bill_id]
                elif state > 4:
                    await self.instance.chat(
                        '$s$FFF//Bet$1EFMania$FFF: Transaction refused or failed! No bet was placed!',
                        self.bets[bill_id]['player'])
                    del self.bets[bill_id]

    async def betmania_info(self, player, data, **kwargs):
        await self.instance.chat('$s$FFF//Bet$1EFMania $FFFBetting System v$FF00.3.0-0 $FFF(Subsystem v2)', player)

        await self.instance.chat('$s$1EF/bet <amount> <team>$FFF: $iBets an individual amount of planets on a team.',
                                 player)
        await self.instance.chat('$s$1EF/quota$FFF: $iShows the current payout quotas for each possible result.',
                                 player)

        if player.level > 0:
            await self.instance.chat('$s$1EF//openbet$FFF: $iOpens up a new bet or reopens a closed one.', player)
            await self.instance.chat('$s$1EF//closebet$FFF: $iCloses an existing bet for new entries.', player)

        if player.level == 3:
            await self.instance.chat('$s$1EF//resolvebet$FFF: $iCloses and resolves an open bet.', player)
            await self.instance.chat('$s$1EF//resetbet$FFF: $iResets an open bet. Players get their payins refunded.',
                                     player)

    async def reconfigure_teams(self, *args, **kwargs):
        if self.bet_current:
            self.reconfigure = True
        else:
            team_config = await self.setting_bet_config_teams.get_value()
            self.teams = team_config.split(',')

            color_config = await self.setting_bet_config_team_colors.get_value()
            colors = color_config.split(',')

            iteration = 0

            for team in self.teams:
                if iteration < len(colors):
                    self.team_colors[team] = colors[iteration]
                else:
                    self.team_colors[team] = '$s$DDD'

                self.supporters[team] = dict()
                self.stack[team] = 0
                iteration += 1

    async def toggle_widget(self, *args, **kwargs):
        await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: UI will be added in a future version.')

    def calc_stake(self):
        stake = 0

        for team in self.teams:
            stake += self.stack[team]

        deduct_amount = self.setting_bet_margin.get_value()
        deduct_rel = self.setting_bet_margin_relative.get_value()

        if deduct_rel:
            if abs(deduct_amount) > 100:
                deduct_amount %= 100

            stake -= abs(deduct_amount) * (stake / 100)
        else:
            stake -= abs(deduct_amount)

        return stake

    async def debug(self, player, data, **kwargs):
        await self.instance.chat(
            '$FFFbet_open: $000{} $FFF// bet_current: $000{} $FFF// stack_red: $F00{} $FFF// stack_blue: $00F{}'
            .format(str(self.bet_open), str(self.bet_current), str(self.stack['red']), str(self.stack['blue'])),
            player)
        await self.instance.chat('$FFFEntries in supporters_red: $F00{} $FFF// Entries in supporters_blue: $00F{}'
                                 .format(str(len(self.supporters['red'])), str(len(self.supporters['blue']))), player)
        await self.instance.chat('$FFFEntries in supporters_red: $F00{}'.format(str(self.supporters['red'])), player)
