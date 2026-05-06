import sys
import time
import random


def select_top_k(values: list[int], k: int) -> int:
    """
    上位k個のインデックスからランダムに選ぶ
    kは1以上でなければならない
    """
    if k <= 0:
        raise ValueError("k must be greater than 0")
    sorted_indices = sorted(
        range(len(values)), key=lambda i: values[i] if values[i] > 0 else float("inf")
    )
    top_k_indices = sorted_indices[:k]
    return random.choice(top_k_indices)


def select_inverse(values: list[int]) -> int:
    """
    逆数を重みにしてインデックスを選ぶ
    0の値は選ばれないようにする
    totalが0になる場合には呼ばないことを保証する
    """
    v_min = min(v for v in values if v > 0)
    weights = [(1.0 / (v - v_min + 1)) if v > 0 else 0.0 for v in values]
    # weights = [(1.0 / v) if v > 0 else 0.0 for v in values]
    return random.choices(range(len(values)), weights=weights, k=1)[0]


def select_min(values: list[int]) -> int:
    """
    最小値を持つインデックスを選ぶ
    複数ある場合はランダムに選ぶ
    """

    min_value = min(v for v in values if v > 0)
    candidates = [i for i, v in enumerate(values) if v == min_value]
    return random.choice(candidates)


def solve(
    n: int,
    h: list[int],
    c: list[int],
    a: list[list[int]],
    use_random: bool,
) -> list[tuple[int, int]]:  # [(武器のindex, 宝箱のindex)]
    result = []

    chest_hp = list(h)
    weapon_hp = list(c)

    # 武器を使える場合は一番ダメージが大きい宝箱を攻撃する
    # 素手の場合は一番HPの低い宝箱を攻撃する
    while any(chest_hp[i] > 0 for i in range(n)):
        # 使える武器があるかを確認する
        usable_weapon_indices = [
            i for i in range(n) if weapon_hp[i] > 0 and chest_hp[i] <= 0
        ]

        for weapon_index in usable_weapon_indices:
            while weapon_hp[weapon_index] > 0 and any(
                chest_hp[i] > 0 for i in range(n)
            ):
                # 武器weapon_indexで攻撃する宝箱を選ぶ
                best_chest = -1
                best_damage = 0
                for chest_index in range(n):
                    if (
                        chest_hp[chest_index] > 0
                        and min(chest_hp[chest_index], a[weapon_index][chest_index])
                        > best_damage
                    ):
                        best_chest = chest_index
                        best_damage = min(
                            chest_hp[chest_index], a[weapon_index][chest_index]
                        )

                weapon_hp[weapon_index] -= 1
                chest_hp[best_chest] -= best_damage
                result.append((weapon_index, best_chest))

        # 宝箱が残っているかを確認する
        if not any(chest_hp[i] > 0 for i in range(n)):
            break

        # 使える武器がない場合は素手で攻撃する
        # 攻撃対象はHPが低いほど選ばれやすいようにする
        target_chest_index = (
            select_top_k(chest_hp, 3) if use_random else select_min(chest_hp)
        )
        result.extend(
            (-1, target_chest_index) for _ in range(chest_hp[target_chest_index])
        )
        chest_hp[target_chest_index] = 0

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

    best_result = solve(n, h, c, a, use_random=False)
    best_cost = len(best_result)
    print(f"Initial cost: {best_cost}", file=sys.stderr)
    iteration = 0
    while True:
        iteration += 1
        if iteration % 128 == 0:
            if time.perf_counter() - time_start > TIME_LIMIT:
                break

        result = solve(n, h, c, a, use_random=True)
        cost = len(result)
        if cost < best_cost:
            print(f"New best cost: {cost} (previous: {best_cost})", file=sys.stderr)
            best_cost = cost
            best_result = result

    print("\n".join(f"{w} {b}" for w, b in best_result))


if __name__ == "__main__":
    main()
