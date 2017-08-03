#!/usr/bin/perl -w

BEGIN {
    require "/etc/emulab/paths.pm";
    import emulabpaths;
}
use libsetup;

my $FINDIF = "$BINDIR/findif";
# lans that this node is a member of.
#
my %ifmap = ();
my @ifconfigs = ();

if (getifconfig(\@ifconfigs) != 0) {
	warn "Could not fetch Emulab interfaces configuration!";
	return undef;
}

foreach my $ifconfig (@ifconfigs) {
	my $ip  = $ifconfig->{IPADDR};
	my $mac = $ifconfig->{MAC};
	my $lan = $ifconfig->{LAN};

	next unless $mac && $lan;

	#print "Debug: checking interface: $mac/$ip/$lan\n"

	my $iface = `$FINDIF -m $mac`;
	chomp $iface;
	if ($? != 0 || !$iface) {
    		warn "Emulab's findif tool failed for ip address: $ip\n";
    		next;
	}
	print "$lan -> $iface -> $ip -> $mac\n";
}

