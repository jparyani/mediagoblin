dnl configure.ac
dnl
dnl Copyright 2012, 2013 Brandon Invergo <brandon@invergo.net>
dnl
dnl Copying and distribution of this file, with or without modification,
dnl are permitted in any medium without royalty provided the copyright
dnl notice and this notice are preserved.  This file is offered as-is,
dnl without any warranty.

dnl#########
dnl README #
dnl#########
dnl
dnl This is a basic Autoconf configure.ac file for Python-based
dnl projects. It is not intended to be used as-is, but rather to be
dnl modified to the specific needs of the project.
dnl
dnl Lines prefixed with "dnl" are comments that are automatically
dnl removed by Autoconf/M4, thus they will not appear in the generated
dnl configure script (see the M4 documentation for more information). 
dnl Such comments are used in this file to communicate information to 
dnl you, the developer. In some cases, the comments contain extra 
dnl macros that you might consider including in your configure script. 
dnl If you wish to include them, simply remove the "dnl" from the 
dnl beginning of the line.
dnl
dnl Lines prefixed with "#" are comments that will appear in the 
dnl generated configure script. These comments are thus used to clarify
dnl to the user what is happening in that script
dnl
dnl Wherever pyconfigure-specific macros are used, extra comments are
dnl included to describe the macros.

dnl######################
dnl Package Information #
dnl######################

dnl----
dnl Initialize Autoconf with the package metadata
dnl The arguments have been set via the project's PKG-INFO file
dnl and correspond to:
dnl
dnl 1) package name (i.e. foo)
dnl 2) package version (i.e. 1.2)
dnl 3) bug/info/project email address (i.e. bug-foo@gnu.org)
dnl----
dnl
AC_INIT([mediagoblin], [0.4.0.dev], [cwebber@gnu.org])

dnl----
dnl Load macros from the m4/ directory. If you plan to write new 
dnl macros, put them in files in this directory.
dnl----
dnl
AC_CONFIG_MACRO_DIR([m4])


# The default prefix should be changed from /usr/local. Set it, as in
# the documentation, to /srv/mediagoblin.example.org/mediagoblin/
AC_PREFIX_DEFAULT([`pwd`])


dnl###########################
dnl Program/command support  #
dnl###########################
dnl
dnl In this section, we check for the presence of important commands
dnl and programs.

dnl--PC_INIT----------------------------------------------------------
dnl This is the only required macro. Its primary function is to find
dnl a Python interpreter that is compatible with the package and set 
dnl the PYTHON variable to hold its path. It can optionally take
dnl arguments to specify minimum and/or maximum versions:
dnl PC_INIT: find an interpreter with a version between 2.0 and 3.3.99
dnl          (in other words, up to and including any possible release
dnl          in the 3.3 series)
dnl PC_INIT([MIN_VER], [MAX_VER]): Find an interpreter that is between
dnl          the minimum and maximum version. If the min is in the 2.0
dnl          series and the max is in the 3.0 series, non-existent 
dnl          releases (2.8 & 2.9) will be correctly skipped.
dnl----
dnl
PC_INIT([2.6], [2.7.99])

dnl--PC_PYTHON_PROG_PYTHON_CONFIG-------------------------------------
dnl In order to use some of the other macros, you also need the 
dnl python-config command, which will fall subject to the same problem 
dnl of python3-config being preferred to python2-config. This macro
dnl will be automatically included if you use on of the macros that 
dnl depends on it, so you normally don't have to call it. However, if
dnl you require a specific version, you can do something like the
dnl following example.
dnl----
dnl
PC_PYTHON_PROG_PYTHON_CONFIG([python2-config])
if [[ "x$PYTHON_CONFIG" == "x" ]]; then
   PC_PYTHON_PROG_PYTHON_CONFIG([$PYTHON-config])
fi   

dnl----
dnl With the following set of macros, we implement an option 
dnl "--with-virtualenv", which the user can pass to the configure 
dnl script in order to install to a Virtualenv (AC_ARG_WITH). If the 
dnl option is specified by the user, then we check if the program is
dnl available, checking both for "virtualenv" and "virtualenv2" 
dnl (AC_CHECK_PROGS)
dnl----
dnl
# Support installing to a virtualenv via the --with-virtualenv 
# configure flag
AC_ARG_WITH([virtualenv],
	[AS_HELP_STRING([--without-virtualenv], [install to a Python virtualenv])],
	[],
	[with_virtualenv=yes])
AS_IF([test "x$with_virtualenv" != xno],
	    AC_CHECK_PROGS([VIRTUALENV], [virtualenv virtualenv3 virtualenv2], [no])
	    AS_IF([test "x$VIRTUALENV" = xno],
	    [AC_MSG_FAILURE(
		[--with-virtualenv given but virtualenv could not be found])]),
	AC_SUBST([VIRTUALENV], [no]))
AC_ARG_VAR([VIRTUALENV_FLAGS], [flags to pass to the virtualenv command])

dnl----
dnl If the program uses sphinx-build to build documentation, uncomment 
dnl this to create a SPHINXBUILD variable in the Makefile pointing to 
dnl the program. Thus, the user would specify 
dnl SPHINXBUILD=/path/to/sphinx-build as an argument to the configure
dnl script. Since building the documentation should be optional, just
dnl print a warning. If the program uses some other documentation
dnl system, you can do something similar with it.
dnl----
dnl
# Check for sphinx-build
AC_CHECK_PROGS([SPHINXBUILD], [sphinx-build sphinx-build3 sphinx-build2], [no])
AS_IF([test "x$SPHINXBUILD" = xno], 
    AC_MSG_WARN(sphinx-build is required to build documentation))


dnl----
dnl These two are standard Autoconf macros which check for the 
dnl presence of some programs that we will use in the Makefile.
dnl----
dnl
AC_PROG_MKDIR_P
AC_PROG_INSTALL	    

# Check for a supported database program
AC_PATH_PROG([SQLITE], [sqlite3])
AC_PATH_PROG([POSTGRES], [postgres])
AS_IF([test "x$SQLITE" = x -a "x$POSTGRES" = "x"],
   [AC_MSG_ERROR([SQLite or PostgreSQL is required])])


dnl--PC_PYTHON_SITE_PACKAGE_DIR---------------------------------------
dnl This uses PYTHON_SITE_DIR to construct a directory for this
dnl project (ie $PYTHON_SITE_DIR/project_name) and stores it in
dnl pkgpythondir. This value is used by Automake for installing Python
dnl scripts. By default, this begins with $pythondir, unexpanded, to
dnl provide compatibility with GNU Makefile specifications, allowing
dnl the user to change the prefix from the commandline.
dnl----
dnl
PC_PYTHON_SITE_PACKAGE_DIR

dnl--PC_PYTHON_EXEC_PACKAGE_DIR----------------------------------------
dnl Same as PC_PYTHON_SITE_PACKAGE_DIR but for $exec-prefix. Stored in
dnl pkgpyexecdir
dnl----
dnl
PC_PYTHON_EXEC_PACKAGE_DIR


dnl###############################
dnl Checking Python capabilities #
dnl###############################

dnl--PC_PYTHON_CHECK_MODULE([PYTHON-MODULE], [ACTION-IF-PRESENT],
dnl                         [ACTION-IF-ABSENT]) 
dnl This macro lets you check if a given Python module exists on the
dnl system.
dnl----
dnl
dnl PC_PYTHON_CHECK_MODULE([foo])

# Check for python-lxml module
PC_PYTHON_CHECK_MODULE([lxml], [], 
                       [AC_MSG_ERROR([python-lxml is required])])

# Check for the Python Imaging Library
PC_PYTHON_CHECK_MODULE([Image], [],
                       [AC_MSG_ERROR([Python Imaging Library is required])])


dnl#########
dnl Finish #
dnl#########

dnl Define the files to be configured
AC_CONFIG_FILES([Makefile])
dnl Generate config.status
AC_OUTPUT
