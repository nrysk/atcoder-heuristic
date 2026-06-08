import os
import glob
import sys
import pandas as pd

# 🚀 ディレクトリの設定
INPUT_DIR = "out_extract_temp"
OUTPUT_DIR = "out_label_temp"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 🚀 ユーザーさんが取得したCSVのカラム構成（ヘッダーなしを想定）
COLUMNS = [
    "n",
    "m",
    "num_h_walls",
    "num_v_walls",
    "macro",
    "score",
    "num_forward",
    "num_turn",
    "ends_look_back",
    "max_temperature",
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

        q08 = df["score"].quantile(0.08)
        q20 = df["score"].quantile(0.20)

        # 3. 条件に従ってラベリング (デフォルトを 2:その他 に設定)
        df["label"] = 2

        df.loc[df["score"] <= q20, "label"] = 1
        df.loc[df["score"] <= q08, "label"] = 0

        # 4. out_label ディレクトリに同じ名前で保存
        # 今後の分析効率化のため、ここからはヘッダー(列名)付きで保存します
        output_path = os.path.join(OUTPUT_DIR, file_name)
        df.to_csv(output_path, index=False, header=True)

    except Exception as e:
        print(f"❌ エラーが発生しました ({file_name}): {e}")

print("=== 🎉 すべてのファイルのラベリングが完了しました！ ===")
