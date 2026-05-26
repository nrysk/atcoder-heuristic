def move(
    n: int,
    current_idx: int,
    target_idx: int,
    operations: list[str],
) -> int:
    current_y, current_x = divmod(current_idx, n)
    target_y, target_x = divmod(target_idx, n)

    if current_y < target_y:
        operations.extend(["D"] * (target_y - current_y))
    else:
        operations.extend(["U"] * (current_y - target_y))

    if current_x < target_x:
        operations.extend(["R"] * (target_x - current_x))
    else:
        operations.extend(["L"] * (current_x - target_x))

    return target_idx


def solve(
    n: int,
    m: int,
    start_idx: int,
    flag_idxs: list[int],
) -> list[str]:

    current_idx = start_idx
    operations = []

    for flag_idx in flag_idxs:
        current_idx = move(n, current_idx, flag_idx, operations)

    return operations


def main():
    n, m = map(int, input().split())
    start_y, start_x = map(int, input().split())
    start_idx = start_y * n + start_x
    flag_idxs = []
    for _ in range(m - 1):
        y, x = map(int, input().split())
        flag_idxs.append(y * n + x)

    result = solve(n, m, start_idx, flag_idxs)

    print("\n".join(result))


if __name__ == "__main__":
    main()
