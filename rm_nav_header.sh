#!/bin/bash
# Not portable!! Lol!! Get urself some ag!!
for f in `ag Navigation -l`; do
	sed -i '' 's|^<h3>Navigation</h3>$|<br>|' $f
done

