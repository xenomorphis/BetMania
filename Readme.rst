========
BetMania
========
:Release: 2023-04-19
:Version: 0.3.3

BetMania is a plugin for `PyPlanet <https://pypla.net/en/latest/index.html>`_ and provides an ingame betting system
for Trackmania. Since version 0.2.0 the codebase in the ``master``-branch can be considered 'stable'. Don't consider
a copy of the master-branch to be an official release however - there may still be some WIP going on.


Basic Usage
-----------
BetMania is currently a command-line tool using the ingame chat as it's CLI. The amount of available commands was
reduced to a bare minimum for the sake of simplicity. There'll be room for extra functionality once a GUI is added and
the commands are well hidden behind stylish little buttons.

**Administrative commands**

``//openbet``
    | *Admin Level 1*
    | Initializes the betting system and enables placing bets.

``//closebet``
    | *Admin Level 1*
    | Closes an opened bet for new stakes.

``//resolvebet <team>``
    | *Admin Level 3*
    | Closes (if still open) and resolves the currently running bet. Triggers the payouts according to the specified result.

``//resetbet``
    | *Admin Level 3*
    | Cancels the current bet. All current payins will be returned to the respective players.

--------

**Development commands**

``//bmdebug``
    | *Admin Level 3*
    | Outputs current values of almost every plugin variable. Needed occasionally during the development process. Will be removed once plugin is stable.

--------

**Player commands**

``/bet <amount> <team>``
    | *No permissions needed*
    | Places the specified **amount** as a bet on the specified **team**.

``/supporters <team>``
    | *No permissions needed*
    | Shows a list containing all players which have placed stakes on a specific **team**.

``/quota``
    | *No permissions needed*
    | Writes the current payout quotas for both teams into the ingame chat.

``/betmania``
    | *No permissions needed*
    | Writes the version number of the currently installed BetMania instance into the ingame chat.


Settings
--------
BetMania can be configured ingame via the following settings:

``bet_config_teams``
    | *Type: list(str)*
    | *Default: blue,red*
    | Configure the available betting targets (teams).

``bet_config_team_colors``
    | *Type: list(str)*
    | *Default: $s$00F,$s$F00*
    | Configures the highlighting colors used in chat announcements for each team.

``bet_margin``
    | *Type: int*
    | *Default: 0*
    | Defines the amount of planets deducted as transaction fees from the total stake before a bet
    payout. Use values between 1 and 100 if bet_margin_relative is activated.

``bet_margin_relative``
    | *Type: bool*
    | *Default: False*
    | If set to ``True``, bet_margin is handled as a relative amount (xx % of the stake). By default
    ``bet_margin`` will be used as an absolute amount (xxx planets).

``bet_minimum_stake``
    | *Type: int*
    | *Default: 1*
    | Defines the minimum amount of planets needed for placing a bet. A value of 1 accepts all stakes.

``bet_maximum_stake``
    | *Type: int*
    | *Default: 2500*
    | Defines the maximum amount of planets allowed for placing a bet.

``show_widget``
    | *Type: bool*
    | *Default: False*
    | Shows / Hides the BetMania widget (currently unused).


Roadmap
-------
A non-comprehensive list of enhancements planned for future releases. As this is a spare-time project there's no
guarantee that the features listet here will be actually developed. So take it as a collection of ideas how this module could
be improved beyond it's basic functionalities.

* Adding a GUI / widget for easier usability

* Adding a configurable Auto-Bet mode (especially for Rounds mode) running with almost zero administration needed
