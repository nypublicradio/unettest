#!/bin/bash
# Not portable!! Lol!! Get urself some ack!!
for f in `ack Navigation -l`; do
	sed -i.bak 's|^<h3>Navigation</h3>$|<br>|' $f
done

