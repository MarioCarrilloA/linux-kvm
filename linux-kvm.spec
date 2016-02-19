#
# This is a special configuration of the Linux kernel, aimed exclusively
# for running inside a KVM virtual machine
# This specialization allows us top optimize memory footprint and boot time.
#

Name:           linux-kvm
Version:        4.4.2
Release:        139
License:        GPL-2.0
Summary:        The Linux kernel optimized for running inside KVM
Url:            http://www.kernel.org/
Group:          kernel
Source0:        https://www.kernel.org/pub/linux/kernel/v4.x/linux-4.4.2.tar.xz
Source1:        config
Source2:        cmdline

%define kversion %{version}-%{release}.kvm

BuildRequires:  bash >= 2.03
BuildRequires:  bc
# For bfd support in perf/trace
BuildRequires:  binutils-dev
BuildRequires:  elfutils
BuildRequires:  elfutils-dev
BuildRequires:  kmod
BuildRequires:  make >= 3.78
BuildRequires:  openssl-dev
BuildRequires:  flex
BuildRequires:  bison

# don't srip .ko files!
%global __os_install_post %{nil}
%define debug_package %{nil}
%define __strip /bin/true

Patch1:  0001-msleep.patch
Patch2:  0002-cpuidle-skip-synchronize_rcu-on-single-CPU-systems.patch
Patch3:  0003-sysrq-skip-synchronize_rcu-if-there-is-no-old-op.patch
Patch4:  0004-fbcon-enable-no-blink-by-default.patch
Patch5:  0005-vmstats-wakeups.patch
Patch6:  0006-pci-probe.patch
Patch7:  0007-cgroup.patch
Patch8:  0008-smpboot.patch
Patch9:  0009-perf.patch
Patch10:  0010-sched-fair-tweak-the-scheduler-to-favor-CPU-0.patch
Patch11: 0011-pci-probe-identify-known-devices.patch
Patch12: 0012-init-no-wait-for-the-known-devices.patch
Patch13: 0013-fork-turn-mmput-into-an-async-function.patch
Patch14: 0014-perf-ptdamage.patch

#cpuidle: small improvements & fixes for menu governor
Patch15: 0015-cpuidle-x86-increase-forced-cut-off-for-polling-to-2.patch
Patch16: 0016-cpuidle-menu-use-interactivity_req-to-disable-pollin.patch
Patch17: 0017-cpuidle-menu-smooth-out-measured_us-calculation.patch

Patch18: 0018-init-do_mounts-recreate-dev-root.patch


%description
The Linux kernel.

%package extra
License:        GPL-2.0
Summary:        The Linux kernel kvm extra files
Group:          kernel

%description extra
Linux kernel extra files

%prep
%setup -q -n linux-4.4.2

# Use when needed
# Added a warning to msleep (our local patch) to catch where it is used
# not all uses are bug
#%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p1
%patch6 -p1
%patch7 -p1
%patch8 -p1
%patch9 -p1
%patch10 -p1
%patch11 -p1
%patch12 -p1

%patch13 -p1
%patch14 -p1

#cpuidle: small improvements & fixes for menu governor
%patch15 -p1
%patch16 -p1
%patch17 -p1

%patch18 -p1

cp %{SOURCE1} .

%build
BuildKernel() {
    MakeTarget=$1

    Arch=x86_64
    ExtraVer="-%{release}.kvm"

    perl -p -i -e "s/^EXTRAVERSION.*/EXTRAVERSION = ${ExtraVer}/" Makefile

    make -s mrproper
    cp config .config

    make -s ARCH=$Arch oldconfig > /dev/null
    make -s CONFIG_DEBUG_SECTION_MISMATCH=y %{?_smp_mflags} ARCH=$Arch $MakeTarget %{?sparse_mflags}
    make -s CONFIG_DEBUG_SECTION_MISMATCH=y %{?_smp_mflags} ARCH=$Arch modules %{?sparse_mflags} || exit 1
}

BuildKernel bzImage

%install

InstallKernel() {
    KernelImage=$1

    Arch=x86_64
    KernelVer=%{kversion}
    KernelDir=%{buildroot}/usr/lib/kernel

    mkdir   -p ${KernelDir}
    install -m 644 .config    ${KernelDir}/config-${KernelVer}
    install -m 644 System.map ${KernelDir}/System.map-${KernelVer}
    install -m 644 %{SOURCE2} ${KernelDir}/cmdline-${KernelVer}
    cp  $KernelImage ${KernelDir}/org.clearlinux.kvm.%{version}-%{release}
    chmod 755 ${KernelDir}/org.clearlinux.kvm.%{version}-%{release}

    mkdir -p %{buildroot}/usr/lib/modules/$KernelVer
    make -s ARCH=$Arch INSTALL_MOD_PATH=%{buildroot}/usr modules_install KERNELRELEASE=$KernelVer

    rm -f %{buildroot}/usr/lib/modules/$KernelVer/build
    rm -f %{buildroot}/usr/lib/modules/$KernelVer/source

    # Erase some modules index
    for i in alias ccwmap dep ieee1394map inputmap isapnpmap ofmap pcimap seriomap symbols usbmap softdep devname
    do
        rm -f %{buildroot}/usr/lib/modules/${KernelVer}/modules.${i}*
    done
    rm -f %{buildroot}/usr/lib/modules/${KernelVer}/modules.*.bin
}

InstallKernel arch/x86/boot/bzImage

rm -rf %{buildroot}/usr/lib/firmware

# Recreate modules indices
depmod -a -b %{buildroot}/usr %{kversion}

ln -s org.clearlinux.kvm.%{version}-%{release} %{buildroot}/usr/lib/kernel/default-kvm

%files
%dir /usr/lib/kernel
%dir /usr/lib/modules/%{kversion}
/usr/lib/kernel/config-%{kversion}
/usr/lib/kernel/cmdline-%{kversion}
/usr/lib/kernel/org.clearlinux.kvm.%{version}-%{release}
/usr/lib/kernel/default-kvm
/usr/lib/modules/%{kversion}/kernel
/usr/lib/modules/%{kversion}/modules.*

%files extra
%dir /usr/lib/kernel
/usr/lib/kernel/System.map-%{kversion}
