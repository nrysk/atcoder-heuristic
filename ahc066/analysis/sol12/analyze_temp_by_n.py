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
OUTPUT_FOLDER = "plots_by_n"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 2. データセットに含まれる n のユニークな値を抽出してソート (10から20まで)
n_values = sorted(df["n"].unique())

print(f"=== 📊 nの各値に対する温度分布の生成を開始します (対象n: {n_values}) ===")

for n_val in n_values:
    # 特定の n のデータだけを抽出
    sub_df = df[df["n"] == n_val].copy()

    if sub_df.empty:
        continue

    # 3. ⚡【重要】データ数の差を無くすため、各ラベルグループ内での温度の「割合(%)」を計算
    # 例：ラベル0（上位5%）の中で、温度4.0が何%を占めているか
    counts = (
        sub_df.groupby(["label", "max_temperature"]).size().reset_index(name="count")
    )
    totals = sub_df.groupby("label").size().reset_index(name="total")
    merged = pd.merge(counts, totals, on="label")
    merged["percentage"] = (merged["count"] / merged["total"]) * 100

    # 凡例（レジェンド）を人間が見て一瞬でわかるようにリネーム
    merged["label_name"] = merged["label"].map(
        {0: "0: Top 5% (Elite)", 1: "1: Top 15% (Good)", 2: "2: Others"}
    )

    # 4. 🚀 グラフの描画（横並びの棒グラフ: グループド・バーチャート）
    plt.figure(figsize=(9, 5), dpi=150)  # 高解像度で出力

    sns.barplot(
        data=merged,
        x="max_temperature",
        y="percentage",
        hue="label_name",
        palette="muted",  # 見やすいクリーンな配色
        edgecolor="black",  # 棒の輪郭線をくっきりさせる
        linewidth=0.7,
    )

    # 5. 見た目の装飾・見やすさの調整
    plt.title(
        f"Temperature Distribution Comparison (Grid Size n = {n_val})",
        fontsize=13,
        fontweight="bold",
    )
    plt.xlabel("Max Temperature (焼きなまし最高温度)", fontsize=10)
    plt.ylabel("Percentage within each group (%)", fontsize=10)

    # 縦軸を 0% 〜 100% に完全固定（nが変わってもスケールがブレないため、目視比較が劇的に楽になります）
    plt.ylim(0, 100)

    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.legend(title="Label Groups", loc="upper right")

    # 6. 画像として保存
    output_path = os.path.join(OUTPUT_FOLDER, f"temp_dist_n{n_val}.png")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    print(f" ➔ 保存完了: {output_path}")

print(
    f"\n=== 🎉 すべての可視化が完了しました！『{OUTPUT_FOLDER}』フォルダ内の画像を確認してください ==="
)
