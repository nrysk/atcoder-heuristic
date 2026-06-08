

NUM_PROC=8

mkdir -p out_extract

echo "Starting Data Collection"

for f in in/*.txt; do
    name=${f:t:r}

    python3 extract.py < $f > out_extract/${name}.csv &

    echo "Started processing $f"
    
    # 🚀 修正：サブシェルを使わず、zsh固有の変数でジョブ数を安全にチェック
    while (( ${#jobstates} >= NUM_PROC )); do
        sleep 0.1
    done

done

wait

echo "Data Collection Completed"
