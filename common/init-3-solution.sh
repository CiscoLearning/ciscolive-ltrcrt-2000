# Copy solution into home and let student know about it

SOLLINK="$HOME/solution"
if [ -L $SOLLINK ]; then
	rm -f $SOLLINK
fi
if [ ! -e $SOLLINK ] && [ -d $LAB/solution ]; then
	echo "Note: If you get stuck, solution files are provided in $SOLLINK"
	ln -s $LAB/solution $SOLLINK
fi
