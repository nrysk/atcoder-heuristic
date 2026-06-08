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

# 🚀【ユーザーさんの仮説】nを介在させず、単純に m // 2 で絶対数グループ化
df["m_absolute_group"] = df["m"] // 2

# 保存用のフォルダを作成
OUTPUT_FOLDER = "plots_temp_by_m_absolute"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# グループのユニークな値を抽出してソート
m_absolute_groups = sorted(df["m_absolute_group"].unique())

print(f"=== 📊 ボール絶対数グループ(m // 2)ごとの温度分析を開始します ===")
print(f"検出されたグループ（m // 2 の値）: {m_absolute_groups}")

for m_val in m_absolute_groups:
    # 特定のMグループのデータだけを抽出
    sub_df = df[df["m_absolute_group"] == m_val].copy()

    if sub_df.empty:
        continue

    # 実際の一番小さなMと大きなMの範囲をタイトル用につかむ (例: m // 2 = 5 なら M=10〜11)
    min_m = sub_df["m"].min()
    max_m = sub_df["m"].max()

    # 2. ⚡ 各ラベルグループ（0, 1, 2）の内側で、max_temperature の割合(%)を計算
    counts = (
        sub_df.groupby(["label", "max_temperature"]).size().reset_index(name="count")
    )
    totals = sub_df.groupby("label").size().reset_index(name="total")
    merged = pd.merge(counts, totals, on="label")
    merged["percentage"] = (merged["count"] / merged["total"]) * 100

    # 凡例をわかりやすくリネーム
    merged["label_name"] = merged["label"].map(
        {0: "0: Top 5% (Elite)", 1: "1: Top 15% (Good)", 2: "2: Others"}
    )

    # 3. 🚀 グラフの描画（横軸を max_temperature に完全固定）
    plt.figure(figsize=(9, 5), dpi=150)

    sns.barplot(
        data=merged,
        x="max_temperature",
        y="percentage",
        hue="label_name",
        palette="muted",
        edgecolor="black",
        linewidth=0.7,
    )

    # 4. 見た目の装飾・見やすさの調整
    plt.title(
        f"Absolute M Analysis (m // 2 = {m_val} -> M is {min_m} to {max_m})",
        fontsize=13,
        fontweight="bold",
    )
    plt.xlabel("Max Temperature (焼きなまし最高温度)", fontsize=10)
    plt.ylabel("Percentage within each label group (%)", fontsize=10)

    # 縦軸を 0% 〜 100% に固定して正確に比較
    plt.ylim(0, 100)

    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.legend(title="Label Groups", loc="upper right")

    # 5. 画像として保存
    output_path = os.path.join(OUTPUT_FOLDER, f"temp_analysis_m_abs_{m_val}.png")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    print(f" ➔ 保存完了: {output_path}")

print(
    f"\n=== 🎉 可視化が完了しました！『{OUTPUT_FOLDER}』フォルダ内の画像を確認してください ==="
)
