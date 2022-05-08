from pyplanet.apps.config import AppConfig
from pyplanet.contrib.command import Command


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
        self.stack_red = 0
        self.stack_blue = 0
        self.supporters_red = dict()
        self.supporters_blue = dict()
        self.teams = ['blue', 'red']   # TODO: Fill list with items from the current configuration

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
            Command(command='bet', target=self.place_bet, description='Kicks the provided player from the server.')
                .add_param(name='amount', required=True, type=int, help='Enter here how many planets you want to bet')
                .add_param(name='team', required=True, type=str, help='Enter the team you want to bet for. You\'ll receive a playout if your specified team wins (blue / red).'),
            Command(command='quota', target=self.show_bet_quota,
                    description='Returns the current payout quotas for both teams.'),
            Command(command='bmdebug', target=self.debug, perms='betmania:resolve_bet', admin=True,
                    description='For development purposes.'),
            Command(command='betmania', target=self.betmania_info, description='Displays intro message'),
        )

        await self.instance.chat('$s$FFF//Bet$1EFMania $FFFBetting System v$FF00.1.11 $FFF(Subsystem v1) online')

    async def open_bet(self, player, data, **kwargs):
        if not self.bet_current:
            # Works as intended
            # Initializes vars and sets bet to open (it's more or less an init-function)
            self.bet_open = True
            self.bet_current = True
            self.stack_red = 0
            self.stack_blue = 0
            self.supporters_red.clear()
            self.supporters_blue.clear()

            await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: BET IS NOW OPEN! //')
            await self.instance.chat(
                'A bet has been opened. Place your stakes now with \'/bet XXX red\' or \'/bet XXX blue\'. Good luck!')
        else:
            await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: Reivously unresolved bet found. I\'ll reopen that... //', player)
            self.bet_open = True
            await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: BET HAS BEEN REOPENED! //')

    async def close_bet(self, player, data, **kwargs):
        # Works as intended
        # Sets bet to closed without resolving it
        if self.bet_open:
            self.bet_open = False
            await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: BET IS NOW CLOSED!')
        else:
            await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: We don\'t have an active bet at the moment.', player)

    async def resolve_bet(self, player, data, **kwargs):
        # Works until line 90 - still needs testing
        # Sets bet to closed and immediately resolves it
        if self.bet_current:
            self.bet_open = False

            if data.team in self.teams:
                # data.team contains the winning team as provided by /resolve <team>
                stake = self.stack_blue + self.stack_red

                if stake > 0:
                    if self.stack_red > 0:
                        quota_red = round(stake / self.stack_red, 3)
                    else:
                        quota_red = 0

                    if self.stack_blue > 0:
                        quota_blue = round(stake / self.stack_blue, 3)
                    else:
                        quota_blue = 0

                    await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: BET PAYOUTS!!!')

                    if data.team == 'blue':
                        str_team_format = '$s$00F'
                        await self.instance.chat(
                            '$s$FFF//Bet$1EFMania$FFF: Team {}{} $FFFhas won the tournament. Quota was {}.'
                            .format(str_team_format, data.team, str(quota_blue)))
                    else:
                        str_team_format = '$s$F00'
                        await self.instance.chat(
                            '$s$FFF//Bet$1EFMania$FFF: Team {}{} $FFFhas won the tournament. Quota was {}.'
                            .format(str_team_format, data.team, str(quota_red)))

                    if data.team == 'blue':
                        for supporter in self.supporters_blue:
                            payout = round(self.supporters_blue[supporter] * quota_blue)

                            await self.instance.chat(
                                '$s$FFF//Bet$1EFMania$FFF: Congrats! Team $00F{} $FFFwon. You receive $222{} $FFFplanets as your bet payout.'
                                .format(data.team, str(payout)), supporter)
                            # the following should evoke the /pay <supporter> <amount> command
                            await self.instance.command_manager.execute(player, '//payout', supporter, str(payout))
                    else:
                        for supporter in self.supporters_red:
                            payout = round(self.supporters_red[supporter] * quota_red)

                            await self.instance.chat(
                                '$s$FFF//Bet$1EFMania$FFF: Congrats! Team $F00{} $FFFwon. You receive $222{} $FFFplanets as your bet payout.'
                                .format(data.team, str(payout)), supporter)
                            # the following should evoke the /pay <supporter> <amount> command
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
        # Works so far, but for-loop doesn't do the payout
        # Resets a bet and returns all bets to the respective players
        if self.bet_current:
            self.bet_open = False
            self.bet_current = False

            for supporter in self.supporters_blue:
                payout = self.supporters_blue[supporter]
                await self.instance.command_manager.execute(player, '//payout', supporter, str(payout))

            for supporter in self.supporters_red:
                payout = self.supporters_red[supporter]
                await self.instance.command_manager.execute(player, '//payout', supporter, str(payout))

            self.stack_red = 0
            self.stack_blue = 0
            self.supporters_red.clear()
            self.supporters_blue.clear()

            await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: BET IS CANCELLED! You\'ll receive your Planets back.')
        else:
            await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: There\'s nothing to reset...', player)

    async def show_bet_quota(self, player, data, **kwargs):
        # Outputs the current payout quotas for each team
        if self.bet_current:
            stake = self.stack_blue + self.stack_red

            if self.stack_blue > 0:
                quota_blue = round(stake / self.stack_blue, 2)
                await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: Quota for $00FBlue $FFFWin is {}'
                                         .format(str(quota_blue)), player)
            else:
                await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: No current Quota for Team $00FBlue $FFFWin', player)

            if self.stack_red > 0:
                quota_red = round(stake / self.stack_red, 2)
                await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: Quota for $F00Red $FFFWin is {}'
                                         .format(str(quota_red)), player)
            else:
                await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: No current Quota for Team $F00Red $FFFWin', player)

        else:
            await self.instance.chat('$s$FFF//Bet$1EFMania$FFF: We don\'t have an active bet at the moment.', player)

    async def place_bet(self, player, data, **kwargs):
        # Should work now
        # Checks first if bet is open. Allows player to bet planets via donating them (works the same way)
        if self.bet_open:
            if data.team in self.teams:
                # data.amount contains the amount of planets placed as a bet (as provided by /bet <amount> <team>)
                # data.team contains the team the bet is meant for (as provided by /bet <amount> <team>)

                # the following should evoke the /payin <amount> command
                await self.instance.command_manager.execute(player, '/payin', str(data.amount))
                await self.instance.chat(
                    '$s$FFF//Bet$1EFMania$FFF: {} $FFFhas placed a bet of $s$FE1{} $FFFplanets on team {}.'
                    .format(player.nickname, str(data.amount), data.team))

                if data.team == 'blue':
                    self.stack_blue += data.amount

                    if player.login in self.supporters_blue:
                        self.supporters_blue[player.login] += data.amount
                    else:
                        self.supporters_blue[player.login] = data.amount
                else:
                    self.stack_red += data.amount

                    if player.login in self.supporters_red:
                        self.supporters_red[player.login] += data.amount
                    else:
                        self.supporters_red[player.login] = data.amount

            else:
                await self.instance.chat(
                    '$s$FFF//Bet$1EFMania$FFF: Please specify the team you want to place your bet on. Allowed arguments are \'blue\' and \'red\'',
                    player)
        else:
            await self.instance.chat(
                '$s$FFF//Bet$1EFMania$FFF: There\'s no open bet at the moment. Please try again later (or ask an ServerOp to open one ;)',
                player)

    async def betmania_info(self, player, data, **kwargs):
        await self.instance.chat('$s$FFF//Bet$1EFMania $FFFBetting System v$FF00.1.11 $FFF(Subsystem v1)', player)

    async def debug(self, player, data, **kwargs):
        await self.instance.chat('$FFFbet_open: $000{} $FFF// bet_current: $000{} $FFF// stack_red: $F00{} $FFF// stack_blue: $00F{}'
                                 .format(str(self.bet_open), str(self.bet_current), str(self.stack_red), str(self.stack_blue)),
                                 player)
        await self.instance.chat('$FFFEntries in supporters_red: $F00{} $FFF// Entries in supporters_blue: $00F{}'
                                 .format(str(len(self.supporters_red)), str(len(self.supporters_blue))), player)
