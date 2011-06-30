Development Processes
===========================


Bug Tracker
----------------

You can find our bug tracker at: `<http://code.mvpafrica.org/>`_.


Mailing List
------------------

We do not have a public developer mailing list (yet). 
You can reach the ChildCount+ developers on our internal
mailing list at dev at mvpafrica dot org.

Repo and Branches
------------------------

**Repositories**

The ChildCount+ code repository is online here:

    `<http://www.github.com/mvpdev/rapidsms>`_

The installation and server configuration files for 
ChildCount+ installations are online here:

    `<http://www.github.com/mvpdev/rapidsms-impl>`_

**Branches**

The ChildCount+ code repository has two 
two main branches: `ccdev <http://www.github.com/mvpdev/rapidsms/tree/ccdev>` and
`ccstable <http://www.github.com/mvpdev/rapidsms/tree/ccstable>`.
   
If a software developer wants to create a new ChildCount+ feature, the process
generally goes like this:

#.  Developer creates a new branch from ``ccdev``, let's call
    it ``twitter`` and pretend that it adds some `Twitter <http://www.twitter.com/>`_
    functionality to ChildCount+.

#.  Developer does the work on the ``twitter`` branch, merging
    changes from ``ccdev`` into ``twitter`` to make sure that 
    ``twitter`` stays current.

#.  When the developer is satisfied that the Twitter feature works
    as hoped, she merges ``twitter`` into the ``ccdev`` branch.

#.  Every few months, the release developer merges all of the changes
    from ``ccdev`` into ``ccstable``. 
    The release developer tests all of these features and makes sure
    that the translations and localization works properly for 
    French- and Tigrinya-speaking sites.

#.  The release developer pushes the ``ccstable`` code out to the
    sites. In MVP lingo, this is a "stage".



[U] Stages and Version Numbers
-------------------------------

[U] Documentation
-------------------

[U] Who to Contact
-------------------




