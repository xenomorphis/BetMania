from pyplanet.contrib.player.exceptions import PlayerNotFound
from pyplanet.views.generics.list import ManualListView


class SupportersListView(ManualListView):

    app = None

    title = ''
    icon_style = 'Icons128x128_1'
    icon_substyle = 'Browse'
    team = ''

    data = []

    def __init__(self, app, team):
        super().__init__(self)
        self.app = app
        self.manager = app.context.ui
        self.team = team
        self.title = 'Supporters – Team ' + team

    async def get_fields(self):
        return [
            {
                'name': 'Player',
                'index': 'player_name',
                'sorting': False,
                'searching': True,
                'width': 100,
                'type': 'label'
            },
            {
                'name': 'Bet Amount',
                'index': 'bet_amount',
                'sorting': True,
                'searching': False,
                'width': 45
            }
        ]

    async def get_data(self):
        items = []

        for login in self.app.supporters[self.team]:
            try:
                player = self.instance.player_manager.get_player(login)
                supporter = player.nickname
            except PlayerNotFound:
                supporter = login

            items.append({'player_name': supporter, 'bet_amount': self.app.supporters[self.team][login]})

        return items
