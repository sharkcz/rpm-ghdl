%define gccver 4.0.2
%define versuffix dev

Summary: A VHDL simulator, using the GCC technology
Name: ghdl
Version: 0.21
Release: 0.24svn.2%{?dist}
License: GPL
Group: Development/Languages
URL: http://ghdl.free.fr/
# HOWTO create source files from ghdl SVN at https://gna.org/projects/ghdl/
# check out the SVN repo
# cd translate/gcc/
# ./dist.sh sources
Source0: http://ghdl.free.fr/ghdl-%{version}%{versuffix}.tar.bz2
Source1: ftp://gcc.gnu.org/pub/gcc/releases/gcc-%{gccver}/gcc-core-%{gccver}.tar.bz2
Patch0: ghdl-0.21-infodirentry.patch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: gcc-gnat >= 4.0.0-0.40, texinfo
Requires(post): /sbin/install-info
Requires(preun): /sbin/install-info
# gcc-gnat missing on ppc: Bug 174720
# mock does not install glibc-devel.i386 on x86_64, therefore
# gcc -m32 fails, therefore the package does not build under
# mock/plague on x86_64: Bug 174731
ExcludeArch: ppc x86_64

# Make sure we don't use clashing namespaces
%define _vendor fedora_ghdl

%define _gnu %{nil}
%ifarch sparc
%define gcc_target_platform sparc64-%{_vendor}-%{_target_os}
%endif
%ifarch ppc
%define gcc_target_platform ppc64-%{_vendor}-%{_target_os}
%endif
%ifnarch sparc ppc
%define gcc_target_platform %{_target_platform}
%endif

%description
GHDL is a VHDL simulator, using the GCC technology. VHDL is a language
standardized by the IEEE, intended for developing electronic systems. GHDL
implements the VHDL language according to the IEEE 1076-1987 or the IEEE
1076-1993 standard. It compiles VHDL files and creates a binary that simulates
(or executes) your design. GHDL does not do synthesis: it cannot translate your
design into a netlist.

Since GHDL is a compiler (i.e., it generates object files), you can call
functions or procedures written in a foreign language, such as C, C++, or
Ada95.

%prep
%setup -q -n gcc-%{gccver} -T -b 1 -a 0
%{__mv} ghdl-%{version}%{versuffix}/vhdl gcc/
%patch0 -p0

%build
%{__mkdir} obj-%{gcc_target_platform}
pushd obj-%{gcc_target_platform}

# Flag settings cribbed from gcc package
OPT_FLAGS=$(echo %{optflags} | %{__sed} \
	-e 's/\(-Wp,\)\?-D_FORTIFY_SOURCE=[12]//g' \
	-e 's/-m64//g;s/-m32//g;s/-m31//g' \
%ifarch sparc sparc64
	-e 's/-mcpu=ultrasparc/-mtune=ultrasparc/g' \
%endif
	-e 's/[[:blank:]]\+/ /g')

# These compiler flags in rawhide seem to break the build, so get rid of them
OPT_FLAGS=$(echo $OPT_FLAGS | %{__sed} \
	-e 's/-fstack-protector//g ' \
	-e 's/--param=ssp-buffer-size=[0-9]*//g')

export CFLAGS="$OPT_FLAGS"
export XCFLAGS="$OPT_FLAGS"
export TCFLAGS="$OPT_FLAGS"
#configure --enable-languages=vhdl
../configure \
	--program-prefix=%{?_program_prefix} \
	--prefix=%{_prefix} \
	--exec-prefix=%{_exec_prefix} \
	--bindir=%{_bindir} \
	--sbindir=%{_sbindir} \
	--sysconfdir=%{_sysconfdir} \
	--datadir=%{_datadir} \
	--includedir=%{_includedir} \
	--libdir=%{_libdir} \
	--libexecdir=%{_libexecdir} \
	--localstatedir=%{_localstatedir} \
	--sharedstatedir=%{_sharedstatedir} \
	--mandir=%{_mandir} \
	--infodir=%{_infodir} \
	--enable-languages=vhdl \
%ifarch sparc
	--host=%{gcc_target_platform} \
	--build=%{gcc_target_platform} \
	--target=%{gcc_target_platform} \
	--with-cpu=v7
%endif
%ifarch ppc
	--host=%{gcc_target_platform} \
	--build=%{gcc_target_platform} \
	--target=%{gcc_target_platform} \
	--with-cpu=default32
%endif
%ifnarch sparc ppc
	--host=%{gcc_target_platform}
%endif

# Parallel make doesn't work, so not using %{?_smp_mflags}
%{__make}

popd

%install
%{__rm} -rf %{buildroot}
%{__make} -C obj-%{gcc_target_platform} DESTDIR=%{buildroot} install

# Add additional libraries to link
(
echo "-lm"
%ifarch x86_64
echo "-ldl"
%endif
) >> %{buildroot}%{_libdir}/gcc/%{gcc_target_platform}/%{gccver}/vhdl/lib/grt.lst

# Remove files not to be packaged
pushd %{buildroot}
%{__rm} -f \
	.%{_bindir}/{cpp,gcc,gccbug,gcov} \
	.%{_bindir}/%{gcc_target_platform}-gcc{,-%{gccver}} \
	.%{_includedir}/mf-runtime.h \
	.%{_libdir}/lib* \
	.%{_infodir}/dir \
	.%{_infodir}/{cpp,cppinternals,gcc,gccinstall,gccint}.info* \
	.%{_datadir}/locale/*/LC_MESSAGES/{gcc,cpplib}.mo \
	.%{_mandir}/man1/{cpp,gcc,gcov}.1* \
	.%{_mandir}/man7/{fsf-funding,gfdl,gpl}.7* \
	.%{_exec_prefix}/lib/libgcc_s.* \
	.%{_exec_prefix}/lib/libmudflap.* \
	.%{_exec_prefix}/lib/libmudflapth.* \
	.%{_libdir}/32/libiberty.a

# Remove directory hierarchies not to be packaged
%{__rm} -rf \
	.%{_libdir}/gcc/%{gcc_target_platform}/%{gccver}/{include,install-tools} \
	.%{_libexecdir}/gcc/%{gcc_target_platform}/%{gccver}/install-tools

popd

%clean
%{__rm} -rf %{buildroot}

%post
[ -f %{_infodir}/ghdl.info.gz ] && \
	/sbin/install-info %{_infodir}/ghdl.info.gz %{_infodir}/dir || :

%preun
[ -f %{_infodir}/ghdl.info.gz ] && [ $1 = 0 ] && \
	/sbin/install-info --delete %{_infodir}/ghdl.info.gz %{_infodir}/dir || :

%files
%defattr(-,root,root,-)
%doc ghdl-%{version}%{versuffix}/COPYING
%{_bindir}/ghdl
%{_infodir}/ghdl.info.gz
# Need to own directory %{_libdir}/gcc even though we only want the
# %{gcc_target_platform}/%{gccver} subdirectory
%{_libdir}/gcc/
# Need to own directory %{_libexecdir}/gcc even though we only want the
# %{gcc_target_platform}/%{gccver} subdirectory
%{_libexecdir}/gcc/

%changelog
* Thu Dec  1 2005 Thomas Sailer <t.sailer@alumni.ethz.ch> - 0.21-0.24svn.2
- Exclude ppc because gcc-gnat is missing
- Exclude x86_64 because of mock build issues

* Fri Nov 25 2005 Thomas Sailer <t.sailer@alumni.ethz.ch> - 0.21-0.24svn.1
- update to SVN rev 24
- remove additional files to fix x86_64 build

* Tue Nov 22 2005 Thomas Sailer <t.sailer@alumni.ethz.ch> - 0.21-0.23svn.1
- update to SVN rev 23

* Mon Nov 14 2005 Paul Howarth <paul@city-fan.org> - 0.21-0.21.1
- spec file cosmetic cleanups
- incorporate some architecture tweaks from gcc package
- remove files we don't want packaged so that we can turn the unpackaged file
  check back on
- use fedora_ghdl as the machine vendor name to avoid namespace clashes with
  other packages
- own {%%{_libdir},%%{_libexecdir}}/gcc directories since this package does not
  depend on gcc
- add buildreq texinfo, needed to make info file
- don't include README, which is aimed at building ghdl rather than using it
- remove install-tools and munged header files, not needed for ghdl
- only run install-info if the info file is installed
- patch ghdl.texi to include info dir entry

* Fri Nov 11 2005 Thomas Sailer <t.sailer@alumni.ethz.ch> - 0.21-0.21
- update to 0.21pre, svn rev 21
- incorporate changes from Paul Howarth

* Sat Mar 12 2005 Thomas Sailer <t.sailer@alumni.ethz.ch> - 0.18-1
- update to 0.18

* Sat Feb 26 2005 Thomas Sailer <t.sailer@alumni.ethz.ch> - 0.17-1
- update to 0.17

* Tue Feb  8 2005 Thomas Sailer <t.sailer@alumni.ethz.ch> - 0.16-1
- Initial build.

