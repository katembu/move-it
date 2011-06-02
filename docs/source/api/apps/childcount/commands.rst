.. contents::

childcount.commands
===================

Please see :doc:`/tech/forms_and_commands` for information
on what forms and commands are.

Defining a Command
------------------

Say you want to define a new command called `ReverseTextCommand`
that users invoke by SMS like this::

    REVERSE First Second Third


To define this command, you must:

#. Look through the existing commands in :file:`apps/childcount/commands`
   to make sure that the command you want does not already exist.
   There are lots of useful commands defined there, so please check first.

#. Create a file :file:`apps/childcount/commands/ReverseTextCommand.py`

#. Within this new file, import :class:`childcount.commands.CCCommand`
   and define a new class that inherits from it::


    from childcount.commands import CCCommand
    from childcount.utils import authenticated

    class ReverseTextCommand(CCCommand):

        KEYWORDS = {
            'en': ['reverse'],
            'fr': ['inverse'],
        }

        @authenticated
        def process(self):
            ...do actual work here

   See :ref:`api__childcount__commands__CCCommand` for the definition
   of the :class:`childcount.command.CCCommand` class.

#. In :file:`apps/childcount/commands/__init__.py`, add the line::

    from childcount.commands.ReverseTextCommand import ReverseTextCommand

#. In your :file:`local.ini` file in the root ChildCount+ directory,
   add :class:`ReverseTextCommand` to the list of active commands::

    ...
    [childcount]
    commands = WhoCommand, LookupCommands, ReverseTextCommand, ...
    ...


.. _api__childcount__commands__CCCommand:

childcount.commands.CCCommand
-----------------------------
.. automodule:: childcount.commands.CCCommand
    :members:
    :inherited-members:
    :undoc-members:

Pre-Defined Commands
--------------------

There are a variety of commands already
defined in :file:`apps/childcount/commands`.
Consult them before writing a new command.


