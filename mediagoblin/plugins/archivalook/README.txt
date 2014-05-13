
.&&&&&&&&&&&&&&&&&&&&&&&&&&&&.
!&& A R C H I V A L O O K &&&!
,============================,
``````````````````````````````

Q: What is this?
A: It's a very simple plugin for MediaGoblin <http://mediagoblin.org>

Q: What does it do?
A: Archivalook swaps the default MediaGoblin front page (which is a gallery of
the most recent media submitted) with a new front page that is better for cura-
ted websites. Instead of showing the most recent media, archivalook shows
Featured Media on the front page.

Q: How do I install it?
A: Check out this page for instructions:
http://mediagoblin.readthedocs.org/en/v0.6.1/siteadmin/plugins.html
Be sure to run ./bin/gmg assetlink after you have added the plugin to your
instance, this is necessary because the plugin uses custom css.

Q: I set it up but I still can't feature media, what do I do?
A: So when you first activate this plugin, no users have the proper user
permissions to manage featured media. Below this I'll give instructions of how
to give those permissions to yourself and no one else:

    1) If you haven't already, create a user for yourself. You can do this
       one of two ways
        a) you can run your website, visit it, click the link that says `Login`
           (in the top right corner), and then click the link that says
           `Register`. Enter your information and you now have a user account.
        b) you can use the command line tool. in a terminal, navigate to your
           mediagoblin directory. run the command
               $ ./bin/gmg adduser
           and then follow the prompts on screen.
    2) Next, you need to use the command line tool to make yourself an admin.
       If you haven't already, navigate to the mediagoblin directory in a
       terminal. Once there, run the command
               $ ./bin/gmg makeadmin <username>
       where instead of <username> you type in your actual username :P
    3) Now you're the admin! Next, you need to run your server. It's fine if
       you run it locally, by just running:
               $ ./lazyserver.sh
       from the mediagoblin directory. Visit the website, and if you click the
       downard facing arrow to the top left, you should see that you now have
       access to new pages, the very useful moderation panels. Click on the one
       labeled `User Moderation Panel`.
    4) You should be directed to a (possibly very short) table of users, find
       your own username, and click on it.
    5) Now you see your own `User's Detail Page`. At the bottom you should see
       a table of all the things your user has permission to do, including
       being active, and being an administrator. You should see that you don't
       have permission to feature media. Fix that by clicking the `+` button to
       the right of 'Featurer'.
    6) Wooo! Now you can feature and unfeature media!
