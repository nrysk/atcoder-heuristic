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

# 🚀【ユーザーさんのご指定】num_walls を n で割って整数（切り捨て）にしてグループ化
df["normalized_walls"] = df["num_walls"] // (df["n"] * df["n"] // 40)

# 保存用のフォルダを作成
OUTPUT_FOLDER = "plots_temp_by_walls"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 規格化された壁の数のユニークな値を抽出してソート (例: 0, 1, 2, 3...)
wall_groups = sorted(df["normalized_walls"].unique())

print(f"=== 📊 壁密度グループ(num_walls // n)ごとの温度分析を開始します ===")

for wall_val in wall_groups:
    # 特定の壁密度グループのデータだけを抽出
    sub_df = df[df["normalized_walls"] == wall_val].copy()

    if sub_df.empty:
        continue

    # 2. ⚡ 各ラベルグループ（0, 1, 2）の内側で、max_temperature の割合(%)を計算
    # これにより、件数の格差に潰されず「上位5%がどの温度を好むか」が1対1で目視できます
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
        f"Best Temperature Analysis (for num_walls // n = {wall_val})",
        fontsize=13,
        fontweight="bold",
    )
    plt.xlabel("Max Temperature (焼きなまし最高温度)", fontsize=10)
    plt.ylabel("Percentage within each label group (%)", fontsize=10)

    # 縦軸を 0% 〜 100% に固定してグループ間の比較を正確にする
    plt.ylim(0, 100)

    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.legend(title="Label Groups", loc="upper right")

    # 5. 画像として保存
    output_path = os.path.join(OUTPUT_FOLDER, f"temp_analysis_walls_{wall_val}.png")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    print(f" ➔ 保存完了: {output_path}")

print(
    f"\n=== 🎉 すべての可視化が完了しました！『{OUTPUT_FOLDER}』フォルダ内の画像を確認してください ==="
)
