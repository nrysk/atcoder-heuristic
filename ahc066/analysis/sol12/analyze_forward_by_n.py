import os
import glob
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 1. ラベル済みの全CSVファイルを1つに結合
label_files = glob.glob("out_label/*.csv")
if not label_files:
    print(
        "❌ out_label ディレクトリ内にCSVファイルが見つかりません。_label.py を先に実行してください。"
    )
    exit()

df_list = [pd.read_csv(f) for f in label_files]
df = pd.concat(df_list, ignore_index=True)

# 保存用のフォルダを作成
OUTPUT_FOLDER = "plots_forward_by_n"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# データセットに含まれる n のユニークな値を抽出してソート (10から20まで)
n_values = sorted(df["n"].unique())

print(f"=== 📊 nの各値に対する num_forward の分布生成を開始します ===")

for n_val in n_values:
    # 特定の n のデータだけを抽出
    sub_df = df[df["n"] == n_val].copy()

    if sub_df.empty:
        continue

    # 2. ⚡ 各ラベルグループ（0, 1, 2）の内側で、num_forward の割合(%)を計算
    counts = sub_df.groupby(["label", "num_forward"]).size().reset_index(name="count")
    totals = sub_df.groupby("label").size().reset_index(name="total")
    merged = pd.merge(counts, totals, on="label")
    merged["percentage"] = (merged["count"] / merged["total"]) * 100

    # 凡例をわかりやすくリネーム
    merged["label_name"] = merged["label"].map(
        {0: "0: Top 5% (Elite)", 1: "1: Top 15% (Good)", 2: "2: Others"}
    )

    # 3. 🚀 グラフの描画（横軸を num_forward に完全固定）
    plt.figure(figsize=(10, 5), dpi=150)

    sns.barplot(
        data=merged,
        x="num_forward",
        y="percentage",
        hue="label_name",
        palette="muted",
        edgecolor="black",
        linewidth=0.7,
    )

    # 4. 見た目の装飾・見やすさの調整
    plt.title(
        f"Best num_forward Analysis (for n = {n_val})", fontsize=13, fontweight="bold"
    )
    plt.xlabel("num_forward (マクロ内での直進数)", fontsize=10)
    plt.ylabel("Percentage within each label group (%)", fontsize=10)

    # 縦軸を 0% 〜 100% に固定して正確に比較
    plt.ylim(0, 100)

    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.legend(title="Label Groups", loc="upper right")

    # 5. 画像として保存
    output_path = os.path.join(OUTPUT_FOLDER, f"forward_analysis_n_{n_val}.png")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    print(f" ➔ 保存完了: {output_path}")

print(
    f"\n=== 🎉 すべての可視化が完了しました！『{OUTPUT_FOLDER}』フォルダ内の画像を確認してください ==="
)
