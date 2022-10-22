from pyplanet.contrib.player.exceptions import PlayerNotFound
from pyplanet.views.generics.list import ManualListView
from pyplanet.views.generics.widget import WidgetView


class SupportersListView(ManualListView):
    app = None

    title = ''
    icon_style = 'Icons128x128_1'
    icon_substyle = 'Statistics'
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
                'width': 50
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


class ServerInfoWidget(WidgetView):
    widget_x = -160
    widget_y = -50
    z_index = 60

    template_name = 'betmania/main.xml'

    def __init__(self, app):
        """
        :param app: App instance.
        :type app: pyplanet.apps.contrib.info.Info
        """
        super().__init__(self)
        self.app = app
        self.manager = app.context.ui
        self.id = 'betmania__main_window'

    async def get_context_data(self):
        context = await super().get_context_data()

        if self.app.bet_open:
            bet_status = 'OPEN'
        else:
            bet_status = 'CLOSED'

        context.update({
            'bet_status': bet_status,
            'current_stake': self.app.stake,
        })

        return context
