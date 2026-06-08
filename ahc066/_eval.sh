

# 引数
if [[ -z "$1" ]]; then
    echo "Usage: $0 <python_script>"
    exit 1
fi

python_script="$1"

mkdir out.$1

for infile in in/*.txt;do
    outfile=out.$1/$(basename $infile)
    python3 $python_script < $infile >> $outfile
    echo ""
done