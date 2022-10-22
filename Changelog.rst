========
BetMania
========

Changelog
-----------

``0.3.2``
    | Feature: Transfers the ``TransactionHelper`` subsystem completely into the main application

``0.3.1``
    | Feature: Migrates ``/payin`` functionality from TransactionHelper to BetMania
    | Feature: Adds a first draft for the apps main UI
    | Update: Checks if a player has already placed a bet on another team before allowing the player to place a new bet
    | Update: Adds a possibility to configure a minimum amount of planets needed for placing a bet
    | Update: Adds 'supporters' command (displays a list of all supporters of a specific team)
    | Update: Adds a new setting used for storing team colors

``0.2.0``
    | Feature: Replaces hard coded team-specific variables with dynamically created dictionaries for each configured team
    | Update: Removes transactionhelpers bill_updated callback function
    | Update: Adds a small explanation for all available commands to ``/betmania``

``0.1.12``
    | Update: Adds a payin callback function (triggered after receiving a bet payment)

``0.1.11``
    | Fix: TypeError when calling ``/payin`` command

``0.1.10``
    | Fix: Possible divide-by-zero error in ``show_bet_quota()``
    | Fix: Possible divide-by-zero error in ``resolve_bet()``