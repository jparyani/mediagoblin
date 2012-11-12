# Copyright 2012 Brandon Invergo <brandon@invergo.net>
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.  This file is offered as-is,
# without any warranty.

# This is a basic Autoconf configure.ac file for Python-based
# projects. It is not intended to be used as-is, but rather to be
# modified to the specific needs of the project.


dnl####################################
dnl Define some macros here as needed #
dnl####################################

# The minimum-required Python versions
m4_define(python_min_ver, 2.6)


dnl#############################################
dnl Import the Python-specific Autoconf macros #
dnl#############################################

# Unless these macros are included upstream somewhere, this must be included
m4_include([m4/python.m4])


dnl#######################################
dnl Autoconf and Automake initialization #
dnl#######################################

# Initialize Autoconf.
AC_INIT(mediagoblin, 0.3.1)

# Load macros from the m4/ directory
AC_CONFIG_MACRO_DIR([m4])
AM_INIT_AUTOMAKE

# Here we check if we are using Python 3
PC_PYTHON_VERIFY_VERSION([$PYTHON], 3.0,
                          py3k=true,
                          py3k=false)
# If using python 3, try to find python 2 instead
if test "$py3k" = "true" ; then
   m4_define_default([_PYTHON2_BINS], [python2 python2.7 python2.6])
   AC_PATH_PROGS(PYTHON, [_PYTHON2_BINS])
else
# otherwise check that the Python 2 version is sufficient
   PC_PYTHON_VERIFY_VERSION([$PYTHON], python_min_ver, ,
                            [AC_MSG_ERROR(Python interpreter too old)])
fi

AC_CHECK_PROGS([SPHINXBUILD], [sphinx-build sphinx-build2], [no])
AS_IF([test "x$SPHINXBUILD" = xno], 
	    AC_MSG_WARN(sphinx-build is required to build documentation))


AC_ARG_WITH([virtualenv],
	[AS_HELP_STRING([--with-virtualenv], [install to a Python virtualenv])],
	[],
	[with_virtualenv=no])
AS_IF([test "x$with_virtualenv" != xno],
	    AC_CHECK_PROGS([VIRTUALENV], [virtualenv virtualenv2], [no])
	    AS_IF([test "x$VIRTUALENV" = xno],
	    [AC_MSG_FAILURE(
		[--with-virtualenv given but virtualenv could not be found])]),
	AC_SUBST([VIRTUALENV], [no]))
AC_ARG_VAR([VIRTUALENV_FLAGS], [flags to pass to the virtualenv command])

AC_PROG_MKDIR_P
AC_PROG_INSTALL	    

PC_PYTHON_CHECK_HEADERS(,[AC_MSG_ERROR(could not find Python headers)])

PC_PYTHON_SITE_PACKAGE_DIR
PC_PYTHON_EXEC_PACKAGE_DIR

PC_PYTHON_CHECK_MODULE([lxml],,[AC_MSG_ERROR(could not find Python lxml module)])
PC_PYTHON_CHECK_MODULE([Image],,[AC_MSG_ERROR(could not find Python Imaging Library)])



# Files to be configured
AC_CONFIG_FILES([Makefile])
# Generate config.status
AC_OUTPUT
