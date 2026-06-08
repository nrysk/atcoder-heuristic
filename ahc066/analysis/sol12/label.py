import os
import glob
import sys
import pandas as pd

# 🚀 ディレクトリの設定
INPUT_DIR = "out_extract"
OUTPUT_DIR = "out_label"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 🚀 ユーザーさんが取得したCSVのカラム構成（ヘッダーなしを想定）
COLUMNS = [
    "n",
    "m",
    "num_walls",
    "macro",
    "score",
    "num_forward",
    "num_turn",
    "ends_look_back",
    # "max_temperature",
]

# out_extract 以下のすべてのCSVファイルを取得
csv_files = glob.glob(os.path.join(INPUT_DIR, "*.csv"))

print(f"=== 🌟 ラベリング処理を開始します (総ファイル数: {len(csv_files)}) ===")

for file_path in csv_files:
    file_name = os.path.basename(file_path)

    try:
        # 1. ヘッダーなしのCSVとして読み込み、定義したカラム名を割り当てる
        df = pd.read_csv(file_path, header=None, names=COLUMNS, engine="python")

        if df.empty:
            continue

        # 2. ⚡【重要】この盤面（ファイル内）でのスコアの上位5%点、15%点の閾値を計算
        # スコアは小さいほど良いため、quantile(0.05)が最もスコアが良い（小さい）側の閾値になります
        q05 = df["score"].quantile(0.05)
        q15 = df["score"].quantile(0.15)

        # 3. 条件に従ってラベリング (デフォルトを 2:その他 に設定)
        df["label"] = 2

        # 上位15%以内（q15以下）なら 1 を割り当て
        df.loc[df["score"] <= q15, "label"] = 1

        # 上位5%以内（q05以下）なら 0 を上書き
        df.loc[df["score"] <= q05, "label"] = 0

        # 4. out_label ディレクトリに同じ名前で保存
        # 今後の分析効率化のため、ここからはヘッダー(列名)付きで保存します
        output_path = os.path.join(OUTPUT_DIR, file_name)
        df.to_csv(output_path, index=False, header=True)

    except Exception as e:
        print(f"❌ エラーが発生しました ({file_name}): {e}")

print("=== 🎉 すべてのファイルのラベリングが完了しました！ ===")
