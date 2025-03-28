#!/usr/bin/perl -w
use strict;
use warnings;
my$counter=0;
my$id=100000;
open(DAT,"<Gap_list_all_updated.csv");
unlink "targetlist.csv";
open(OUT,">>targetlist.csv");
print OUT"Id;Kingdom;Phylum;Class;Order;Family;Genus;Species;SpeciesTotal;AriseBarcodes;OtherBarcodes;SpeciesLocality;SpeciesOccurrenceStatus\n";
while(<DAT>){
	my$line=$_;
	chomp$line;
	if($counter==0){
		$counter++;
		next;
	}
	my@array=split(";",$line);
	unless($array[1]=~/\w+/){
		next;
	}
	my$kingdom="Animalia";
	my$phylum=$array[1];
	my$class=$array[2];
	my$order=$array[3];
	my$family=$array[4];
	my$genus;
	if($array[0]=~/^(\w+)\s/){
		$genus=$1;
	}
	my$species=$array[0];
	my$speciestotal=$array[7]; #specimens
	unless ($speciestotal=~/^.+/){$speciestotal=0}; 
	my$arisebarcode=$array[6];	#specimens barcoded
	unless ($arisebarcode=~/^.+/){$arisebarcode=0}; 	
	my$otherbarcode=$array[8];	#public bins
	unless ($otherbarcode=~/^.+/){$otherbarcode=0};
	my$specieslocality=$array[5]; #source
	my$SpeciesOccurrence=$array[10]; #status 
	print OUT"$id;$kingdom;$phylum;$class;$order;$family;$genus;$species;$speciestotal;$arisebarcode;$otherbarcode;$specieslocality;$SpeciesOccurrence";
	$id++;
	print OUT "\n";
}