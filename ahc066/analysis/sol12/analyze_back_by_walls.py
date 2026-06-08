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

# 🚀 num_walls を n で割って整数（切り捨て）にしてグループ化
df["normalized_walls"] = df["num_walls"] // df["n"]

# 保存用のフォルダを作成
OUTPUT_FOLDER = "plots_ends_look_back_by_walls"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 規格化された壁の数のユニークな値を抽出してソート
wall_groups = sorted(df["normalized_walls"].unique())

print(f"=== 📊 壁密度グループごとの ends_look_back 分析を開始します ===")

for wall_val in wall_groups:
    # 特定の壁密度グループのデータだけを抽出
    sub_df = df[df["normalized_walls"] == wall_val].copy()

    if sub_df.empty:
        continue

    # 2. ⚡ 各ラベルグループ（0, 1, 2）の内側で、ends_look_back（True/False）の割合(%)を計算
    counts = (
        sub_df.groupby(["label", "ends_look_back"]).size().reset_index(name="count")
    )
    totals = sub_df.groupby("label").size().reset_index(name="total")
    merged = pd.merge(counts, totals, on="label")
    merged["percentage"] = (merged["count"] / merged["total"]) * 100

    # 凡例をわかりやすくリネーム
    merged["label_name"] = merged["label"].map(
        {0: "0: Top 5% (Elite)", 1: "1: Top 15% (Good)", 2: "2: Others"}
    )

    # 3. 🚀 グラフの描画（横軸を ends_look_back に完全固定）
    plt.figure(figsize=(8, 5), dpi=150)

    sns.barplot(
        data=merged,
        x="ends_look_back",
        y="percentage",
        hue="label_name",
        palette="muted",
        edgecolor="black",
        linewidth=0.7,
        order=[False, True],  # 左にFalse、右にTrueを固定配置
    )

    # 4. 見た目の装飾・見やすさの調整
    plt.title(
        f"Best ends_look_back Analysis (for num_walls // n = {wall_val})",
        fontsize=13,
        fontweight="bold",
    )
    plt.xlabel("ends_look_back (マクロ末尾にRRを追加したか)", fontsize=10)
    plt.ylabel("Percentage within each label group (%)", fontsize=10)

    # 縦軸を 0% 〜 100% に固定して正確に比較
    plt.ylim(0, 100)

    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.legend(title="Label Groups", loc="upper right")

    # 5. 画像として保存
    output_path = os.path.join(OUTPUT_FOLDER, f"ends_look_back_walls_{wall_val}.png")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    print(f" ➔ 保存完了: {output_path}")

print(
    f"\n=== 🎉 すべての可視化が完了しました！『{OUTPUT_FOLDER}』フォルダ内の画像を確認してください ==="
)
