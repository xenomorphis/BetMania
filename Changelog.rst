========
BetMania
========

Changelog
-----------

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