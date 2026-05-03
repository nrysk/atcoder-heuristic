

def get_snake_path(n: int, start_corner: tuple[int, int], vertical_first: bool) -> list[tuple[int, int]]:
    path = []
    for i in range(n):
        if vertical_first:
            row = start_corner[0] + (i if start_corner[0] == 0 else -i)
            cols = range(n) if (i % 2 == 0) else range(n-1, -1, -1)
        else:
            col = start_corner[1] + (i if start_corner[1] == 0 else -i)
            rows = range(n) if (i % 2 == 0) else range(n-1, -1, -1)

        for j in (cols if vertical_first else rows):
            path.append((row, j) if vertical_first else (j, col))
    
    return path

def solve_naive(n: int, a: list[list[int]]) -> list[tuple[int, int]]:
    # 全ての蛇行パターンでスコアが最大になるものを探す
    best_score = -1
    best_path = []
    for start_corner in [(0, 0), (0, n-1), (n-1, 0), (n-1, n-1)]:
        for vertical_first in [True, False]:
            path = get_snake_path(n, start_corner, vertical_first)
            score = sum(a[i][j] * (k) for k, (i, j) in enumerate(path))
            if score > best_score:
                best_score = score
                best_path = path

    return best_path

def main():
    n = int(input())
    a = []
    for _ in range(n):
        a.append(list(map(int, input().split())))
    
    ans = "\n".join(f"{i} {j}" for i, j in solve_naive(n, a))
    print(ans)

if __name__ == "__main__":
    main()