%define modname email_admin

Summary: Issabel Email Module
Name:    issabel-%{modname}
Version: 4.0.0
Release: 1
License: GPL
Group:   Applications/System
Source0: %{modname}_%{version}-%{release}.tgz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
BuildArch: noarch
Requires(pre): issabel-framework >= 4.0.0-1
Requires(pre): RoundCubeMail
Requires(pre): php-imap
Requires(pre): postfix, spamassassin, cyrus-imapd
Requires: mailman >= 2.1.9
Requires: php-jpgraph
Requires: php-PHPMailer

# sieveshell requires at least plain authentication method
Requires: cyrus-sasl-plain

Requires: /usr/sbin/saslpasswd2

Requires(pre): /usr/sbin/saslauthd

Obsoletes: elastix-email_admin

%description
Issabel Email Module

%prep
%setup -n %{name}_%{version}-%{release}

%install
rm -rf $RPM_BUILD_ROOT

# ** /etc path ** #
mkdir -p    $RPM_BUILD_ROOT/etc/postfix
mkdir -p    $RPM_BUILD_ROOT/usr/local/bin/
mkdir -p    $RPM_BUILD_ROOT/usr/share/issabel/module_installer/%{name}-%{version}-%{release}/
mkdir -p    $RPM_BUILD_ROOT/var/www/html/libs/
mkdir -p    $RPM_BUILD_ROOT/etc/cron.d/
mkdir -p    $RPM_BUILD_ROOT/usr/local/issabel/
mkdir -p    $RPM_BUILD_ROOT/usr/share/issabel/privileged
mkdir -p    $RPM_BUILD_ROOT/var/www/

# ** libs ** #
mv setup/paloSantoEmail.class.php        $RPM_BUILD_ROOT/var/www/html/libs/
mv setup/cyradm.php                      $RPM_BUILD_ROOT/var/www/html/libs/
mv setup/checkSpamFolder.php             $RPM_BUILD_ROOT/var/www/
mv setup/deleteSpam.php                  $RPM_BUILD_ROOT/var/www/
mv setup/disable_vacations.php           $RPM_BUILD_ROOT/var/www/
mv setup/stats/postfix_stats.cron        $RPM_BUILD_ROOT/etc/cron.d/
mv setup/stats/postfix_stats.php         $RPM_BUILD_ROOT/usr/local/issabel/
mv setup/usr/share/issabel/privileged/*  $RPM_BUILD_ROOT/usr/share/issabel/privileged
rmdir setup/stats

# ** dando los permisos a los archivos que usara postfix stats
chmod 644 $RPM_BUILD_ROOT/usr/local/issabel/postfix_stats.php

# ** dando permisos de ejecucion ** #
chmod +x $RPM_BUILD_ROOT/var/www/checkSpamFolder.php
chmod +x $RPM_BUILD_ROOT/var/www/deleteSpam.php
chmod +x $RPM_BUILD_ROOT/var/www/disable_vacations.php
chmod +x $RPM_BUILD_ROOT/usr/share/issabel/privileged/*

# Files provided by all Elastix modules
mkdir -p    $RPM_BUILD_ROOT/var/www/html/
mv modules/ $RPM_BUILD_ROOT/var/www/html/

# Additional (module-specific) files that can be handled by RPM
#mkdir -p $RPM_BUILD_ROOT/opt/issabel/
#mv setup/dialer

# The following folder should contain all the data that is required by the installer,
# that cannot be handled by RPM.

# ** postfix config ** #
mv setup/etc/postfix/virtual.db               $RPM_BUILD_ROOT/usr/share/issabel/

# Remplazo archivos de Postfix y Cyrus
mv setup/etc/imapd.conf.issabel               $RPM_BUILD_ROOT/etc/
mv setup/etc/postfix/main.cf.issabel          $RPM_BUILD_ROOT/etc/postfix/
mv setup/etc/cyrus.conf.issabel               $RPM_BUILD_ROOT/etc/

# ** /usr/local/ files ** #
mv setup/usr/local/bin/spamfilter.sh          $RPM_BUILD_ROOT/usr/local/bin/

rmdir setup/etc/postfix setup/etc
rmdir setup/usr/share/issabel/privileged setup/usr/share/issabel setup/usr/share
rmdir setup/usr/local/bin setup/usr/local setup/usr

mv setup/   $RPM_BUILD_ROOT/usr/share/issabel/module_installer/%{name}-%{version}-%{release}/
mv menu.xml $RPM_BUILD_ROOT/usr/share/issabel/module_installer/%{name}-%{version}-%{release}/

%pre
# ****Agregar el usuario cyrus con el comando saslpasswd2:
#echo "palosanto" | /usr/sbin/saslpasswd2 -c cyrus -u example.com

mkdir -p /usr/share/issabel/module_installer/%{name}-%{version}-%{release}/
touch /usr/share/issabel/module_installer/%{name}-%{version}-%{release}/preversion_%{modname}.info
if [ $1 -eq 2 ]; then
    rpm -q --queryformat='%{VERSION}-%{RELEASE}' %{name} > /usr/share/issabel/module_installer/%{name}-%{version}-%{release}/preversion_%{modname}.info
fi

%post
# Habilito inicio automático de servicios necesarios
chkconfig --level 345 saslauthd on
chkconfig --level 345 cyrus-imapd on
chkconfig --level 345 postfix on

# Cambiar permisos del archivo /etc/sasldb2 a 644
#chmod 644 /etc/sasldb2


# Creo el archivo /etc/postfix/network_table if not exixts
if [ ! -f "/etc/postfix/network_table" ]; then
    touch /etc/postfix/network_table
    echo "127.0.0.1/32" >  /etc/postfix/network_table
fi

# Verifo si existe virtual.db para previa installation
if [ ! -f /etc/postfix/virtual.db ]; then
   mv /usr/share/issabel/virtual.db /etc/postfix/virtual.db
   chown root:root /etc/postfix/virtual.db
else
   rm -f /usr/share/issabel/virtual.db
fi

# TODO: TAREA DE POST-INSTALACIÓN
# Cambio archivos de Postfix e Imapd con los de Elastix
# Only replace main.cf on install  and user spamfilter create
if [ $1 -eq 1 ]; then
    mv /etc/imapd.conf /etc/imapd.conf.orig
    cp /etc/imapd.conf.issabel /etc/imapd.conf

    mv /etc/postfix/main.cf  /etc/postfix/main.cf.orig
    cp /etc/postfix/main.cf.issabel /etc/postfix/main.cf

    mv /etc/cyrus.conf /etc/cyrus.conf.orig
    cp /etc/cyrus.conf.issabel /etc/cyrus.conf

    # Create the user spamfilter
    /usr/sbin/useradd spamfilter
fi

pathModule="/usr/share/issabel/module_installer/%{name}-%{version}-%{release}"
# Run installer script to fix up ACLs and add module to Elastix menus.
issabel-menumerge /usr/share/issabel/module_installer/%{name}-%{version}-%{release}/menu.xml

pathSQLiteDB="/var/www/db"
mkdir -p $pathSQLiteDB
preversion=`cat $pathModule/preversion_%{modname}.info`
rm -f $pathModule/preversion_%{modname}.info

if [ $1 -eq 1 ]; then #install
  # The installer database
    issabel-dbprocess "install" "$pathModule/setup/db"
elif [ $1 -eq 2 ]; then #update
    issabel-dbprocess "update"  "$pathModule/setup/db" "$preversion"
fi

# add string localhost first in /etc/hosts
if [ -f /etc/hosts  ] ; then
   sed -ie '/127.0.0.1/s/[\t| ]localhost[^\.]/ /g'  /etc/hosts  # busca el patron 127.0.0.1 y reemplaza [\t| ]localhost[^\.] por " "
   sed -ie 's/127.0.0.1/127.0.0.1\tlocalhost/'  /etc/hosts      # reemplaza 127.0.0.1 por 127.0.0.1\tlocalhost
fi

# The installer script expects to be in /tmp/new_module
mkdir -p /tmp/new_module/%{modname}
cp -r /usr/share/issabel/module_installer/%{name}-%{version}-%{release}/* /tmp/new_module/%{modname}/
chown -R asterisk.asterisk /tmp/new_module/%{modname}

php /tmp/new_module/%{modname}/setup/installer.php
rm -rf /tmp/new_module

%clean
rm -rf $RPM_BUILD_ROOT

%preun
pathModule="/usr/share/issabel/module_installer/%{name}-%{version}-%{release}"
if [ $1 -eq 0 ] ; then # Validation for desinstall this rpm
  echo "Delete Email menus"
  issabel-menuremove "%{modname}"

  echo "Dump and delete %{name} databases"
  issabel-dbprocess "delete" "$pathModule/setup/db"
fi

%files
%defattr(-, root, root)
%{_localstatedir}/www/html/*
/usr/share/issabel/module_installer/*
/usr/local/bin/spamfilter.sh
/etc/imapd.conf.issabel
/etc/postfix/main.cf.issabel
/etc/cyrus.conf.issabel
/usr/share/issabel/virtual.db
/var/www/checkSpamFolder.php
/var/www/deleteSpam.php
/usr/local/issabel/postfix_stats.php
/var/www/disable_vacations.php
%defattr(644, root, root)
/etc/cron.d/postfix_stats.cron
%defattr(755, root, root)
/usr/share/issabel/privileged/*

%changelog
