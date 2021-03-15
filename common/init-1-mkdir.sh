# Create main lab directory and backup the old one if it exists

safe_move() {
	if [ -e $1 ]; then
		DEST=`mktemp -du $1.XXXX`
		echo "Existing lab directory found, moving it to $DEST"
		mv $1 $DEST
	fi
	if [ -e $1 ]; then
		echo "FAILED, aborting."
		exit 1
	fi
}

safe_move $LABDIR
mkdir -p $LABDIR


if [ "$LABLINK" ]; then
	if [ -L $LABLINK ]; then
		rm -f $LABLINK
	fi
	if [ ! -e $LABLINK ]; then
		ln -s $LABDIR $LABLINK
	fi
fi
