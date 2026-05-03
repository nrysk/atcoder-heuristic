"""
ショップにアイスクリームを納品するヒューリスティック問題
t回のアクションを行い、各ショップに納品されたアイスクリーム文字列の種類数の合計を最大化する問題
Score = ∑(ショップiに納品されたアイスクリームの種類数)


グラフの頂点は、ショップとアイスクリームの木を表す
    ショップ：0, 1, ..., k-1
    アイスクリームの木：k, k+1, ..., n-1

可能なアクション：
    1. （移動先がアイスクリームの木である場合）移動してアイスクリームを取る：移動先を出力
    2. （移動先がショップである場合）移動してアイスクリームを納品する：移動先を出力
    3. （現在地点がアイスクリームの木である場合）アイスクリームの木をストロベリーにする：-1を出力

ルールと制約：
    2秒以内
    後戻り禁止
    既にストロベリーにされた木を再度ストロベリーにすることは禁止
    n = 100
    mは少ない
    k = 10
    t = 10000
"""

import time
import random


# まずは、制約に従いつつランダムに移動してみる
# 経路とスコアを返す
def solve1(
    n: int,
    m: int,
    k: int,
    t: int,
    g: list[list[int]],
) -> tuple[list[int], int]:
    STRAWBERRYED_PROBABILITY = 0.02

    strawberryed = [False] * n
    actions = []
    previous_pos = -1
    current_pos = 0
    current_ice = ""  # ex: "WWWR", "RWW", Wはバニラ、Rはストロベリー
    shop_ice = [set() for _ in range(k)]  # 納品されたアイスクリームの種類

    for i in range(t):
        # 現在地がアイスクリームかつバニラの木であれば、ストロベリーにするか決める
        if current_pos >= k and not strawberryed[current_pos]:
            if random.random() < STRAWBERRYED_PROBABILITY:
                actions.append(-1)
                strawberryed[current_pos] = True
                continue

        # 後戻りしないように、移動先を選ぶ
        next_pos = random.choice(g[current_pos])
        while next_pos == previous_pos:
            next_pos = random.choice(g[current_pos])
        actions.append(next_pos)
        previous_pos = current_pos
        current_pos = next_pos

        # アイスクリームを取るか、納品するか
        if current_pos >= k:
            # アイスクリームの木に移動した場合、アイスクリームを取る
            current_ice += "R" if strawberryed[current_pos] else "W"
        else:
            # ショップに移動した場合、アイスクリームを納品する
            shop_ice[current_pos].add(current_ice)
            current_ice = ""

    # スコアを計算
    score = sum(len(ice_types) for ice_types in shop_ice)

    return actions, score


def main():
    # 開始時間を記録
    TIME_LIMIT = 1.8  # 2秒の制限時間の少し前に終了するように設定
    start_time = time.perf_counter()

    # 入力受け取り
    n, m, k, t = map(int, input().split())
    g = [[] for _ in range(n)]
    for _ in range(m):
        a, b = map(int, input().split())
        g[a].append(b)
        g[b].append(a)

    best_actions, best_score = solve1(n, m, k, t, g)
    current_itr = 0
    while True:
        if current_itr % 64 == 0:
            if time.perf_counter() - start_time > TIME_LIMIT:
                break
        current_itr += 1

        actions, score = solve1(n, m, k, t, g)
        if score > best_score:
            best_actions, best_score = actions, score

    # 結果出力
    for action in best_actions:
        print(action)
    print(f"Score: {best_score}")


if __name__ == "__main__":
    main()
