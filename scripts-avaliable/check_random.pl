#!/usr/bin/perl

use strict;
use warnings;

my $range = 100;

my $random_number1 = int(rand($range));
my $random_number2 = int(rand($range));

print "perl_rand2 $random_number1 my_perl_random1 rate\n";
print "perl_rand1 $random_number2 my_perl_random2 rate";

