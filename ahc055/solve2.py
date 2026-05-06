import time
import random


def solve(
    n: int,
    h: list[int],
    c: list[int],
    a: list[list[int]],
    order: list[int],  # 宝箱を攻撃する順番
) -> list[tuple[int, int]]:  # [(武器のindex, 宝箱のindex)]
    result = []

    chest_hp = list(h)
    weapon_hp = list(c)

    # ナイーブに順番に攻撃していく
    # 武器は使えるものから順番に使う
    for chest_index in order:
        # 宝箱chest_indexに最もダメージを与える武器を選ぶ
        best_weapon = -1
        best_damage = 1

        while chest_hp[chest_index] > 0:
            # 武器を選ぶ
            best_weapon = -1
            best_damage = 1
            for weapon_index in range(n):
                if (
                    chest_hp[weapon_index] <= 0
                    and weapon_hp[weapon_index] > 0
                    and a[weapon_index][chest_index] > best_damage
                ):
                    best_weapon = weapon_index
                    best_damage = a[weapon_index][chest_index]
            if best_weapon == -1:
                result.extend((-1, chest_index) for _ in range(chest_hp[chest_index]))
                chest_hp[chest_index] = 0
            else:
                result.append((best_weapon, chest_index))
                weapon_hp[best_weapon] -= 1
                chest_hp[chest_index] -= a[best_weapon][chest_index]

    return result


def main():
    TIME_LIMIT = 0.8
    time_start = time.perf_counter()
    n = int(input())  # 宝箱の個数
    h = list(map(int, input().split()))  # 宝箱のHP 宝箱iを壊せば武器iが手に入る
    c = list(map(int, input().split()))  # 武器の耐久値
    a = [
        list(map(int, input().split())) for _ in range(n)
    ]  # 武器iで宝箱jを攻撃したときのダメージ 武器=-1で攻撃力1の素手

    # # 0からn-1の順番で攻撃する
    # order = list(range(n))
    # best_result = solve(n, h, c, a, order)

    # # orderを乱択する
    # best_cost = float("inf")
    # best_result = []
    # iteration = 0
    # while True:
    #     if iteration % 128 == 0:
    #         time_elapsed = time.perf_counter() - time_start
    #         if time_elapsed > TIME_LIMIT:
    #             break
    #     iteration += 1

    #     order = list(range(n))
    #     random.shuffle(order)
    #     result = solve(n, h, c, a, order)
    #     cost = len(result)
    #     if cost < best_cost:
    #         best_cost = cost
    #         best_result = result

    # orderを山登りする
    best_order = list(range(n))
    best_result = solve(n, h, c, a, best_order)
    best_cost = len(best_result)
    iteration = 0
    while True:
        if iteration % 128 == 0:
            time_elapsed = time.perf_counter() - time_start
            if time_elapsed > TIME_LIMIT:
                break
        iteration += 1

        # best_orderを少し変更する
        # 変更の種類：2点の入れ替え、2スライスに分割して入れ替え
        if random.random() < 1:
            # 2点の入れ替え
            i, j = random.sample(range(n), 2)
            new_order = best_order[:]
            new_order[i], new_order[j] = new_order[j], new_order[i]
        else:
            # 3スライスに分割して入れ替え
            i, j = sorted(random.sample(range(n), 2))
            if random.random() < 0.5:
                # スライス1とスライス2を入れ替え
                new_order = best_order[i:j] + best_order[:i] + best_order[j:]
            else:
                # スライス2とスライス3を入れ替え
                new_order = best_order[:i] + best_order[j:] + best_order[i:j]

        new_result = solve(n, h, c, a, new_order)
        new_cost = len(new_result)
        if new_cost < best_cost:
            best_cost = new_cost
            best_order = new_order
            best_result = new_result

    print("\n".join(f"{w} {b}" for w, b in best_result))


if __name__ == "__main__":
    main()
