@0xa95358d75add78c4;

using Spk = import "/sandstorm/package.capnp";
# This imports:
#   $SANDSTORM_HOME/latest/usr/include/sandstorm/package.capnp
# Check out that file to see the full, documented package definition format.

const pkgdef :Spk.PackageDefinition = (
  # The package definition. Note that the spk tool looks specifically for the
  # "pkgdef" constant.

  id = "70awyqss6jq2gkz7dwzsnvumzr07256pzdt3hda9acfuxwh6uh7h",
  # Your app ID is actually its public key. The private key was placed in
  # your keyring. All updates must be signed with the same key.

  manifest = (
    # This manifest is included in your app package to tell Sandstorm
    # about your app.

    appTitle = (defaultText = "MediaGoblin"),

    appVersion = 4,  # Increment this for every release.

    appMarketingVersion = (defaultText = "0.7.1"),

    actions = [
      # Define your "new document" handlers here.
      ( title = (defaultText = "New MediaGoblin Instance"),
        nounPhrase = (defaultText = "collection"),
        command = .myCommand
        # The command to run when starting for the first time. (".myCommand"
        # is just a constant defined at the bottom of the file.)
      )
    ],

    continueCommand = .myCommand,

    metadata = (
      icons = (
        appGrid = (svg = ( embed "app-graphics/mediagoblin-128.svg")),
        grain = (svg = ( embed "app-graphics/mediagoblin-24.svg")),
        market =  (svg = ( embed "app-graphics/mediagoblin-150.svg")),
      ),

      website = "http://mediagoblin.org/",
      codeUrl = "https://github.com/jparyani/mediagoblin",
      license = (openSource = agpl3),
      categories = [media],

      author = (
        contactEmail = "jparyani@sandstorm.io",
        pgpSignature = embed "pgp-signature",
        upstreamAuthor = "MediaGoblin Project",
      ),
      pgpKeyring = embed "pgp-keyring",

      description = (defaultText = embed "description.md"),

      screenshots = [
        (width = 448, height = 376, png = embed "sandstorm-screenshot.png")
      ],
    ),
  ),

  sourceMap = (
    # Here we defined where to look for files to copy into your package. The
    # `spk dev` command actually figures out what files your app needs
    # automatically by running it on a FUSE filesystem. So, the mappings
    # here are only to tell it where to find files that the app wants.
    searchPath = [
      ( sourcePath = "./dockerenv" ),
      ( sourcePath = "." )
    ]
  ),

  fileList = "sandstorm-files.list",
  # `spk dev` will write a list of all the files your app uses to this file.
  # You should review it later, before shipping your app.

  alwaysInclude = ["opt/app", "usr/lib/python2.7"],
  # Fill this list with more names of files or directories that should be
  # included in your package, even if not listed in sandstorm-files.list.
  # Use this to force-include stuff that you know you need but which may
  # not have been detected as a dependency during `spk dev`. If you list
  # a directory here, its entire contents will be included recursively.

  bridgeConfig = (viewInfo = (permissions = [(name = "admin")]))
);

const myCommand :Spk.Manifest.Command = (
  # Here we define the command used to start up your server.
  argv = ["/sandstorm-http-bridge", "6543", "--", "/bin/bash", "run_grain.sh"],
  environ = [
    # Note that this defines the *entire* environment seen by your app.
    (key = "PATH", value = "/usr/local/bin:/usr/bin:/bin")
  ]
);
