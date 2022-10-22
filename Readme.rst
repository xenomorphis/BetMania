========
BetMania
========
:Release: 2022-10-23
:Version: 0.3.2

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


Modules
-------
BetMania currently consists of two separate modules. It may be possible to combine both modules into one at some point
in the future, but for now both modules are needed when using the plugin.

betmania
    Contains the core functionality and provides the necessary commands used by admins and players.

transactionhelper
    This module is a customized and simplified copy of ``pyplanet.apps.contrib.transactions``. It covers everything
    transaction-related and provides the corresponding commands used by ``betmania`` itself. This additional
    *abstraction layer* allowed me to focus entirely on the development of the main module since I didn't need to
    worry about the details of how transaction handling works in PyPlanet. This module will possibly be obsolete in the
    near future.


Roadmap
-------
A non-comprehensive list of enhancements planned for future releases. As this is a spare-time project there's no
guarantee that the features listet here will be actually developed. So take it as a collection of ideas how this module could
be improved beyond it's basic functionalities.

* Adding some configuration options for more flexibility

* Adding a GUI / widget for easier usability

* Adding a configurable Auto-Bet mode (especially for Rounds mode) running with almost zero administration needed
