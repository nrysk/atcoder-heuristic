#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <queue>
#include <chrono>
#include <random>
#include <cmath>

using namespace std;

const int N = 20;
const int M = 50;
const int INF = 1e9;

// K=10のうち、S0~S8をギミックに使用。S9は「絶対開かない壁(型19)」として利用。
const int QUEST_SWITCHES = 9;
const int WALL_GATE_TYPE = 19;

struct Gate
{
    int d, i, j, g;
};
struct Switch
{
    int p, q, s;
};

char grid[N][N];
int horizontal_gates[N][N];
int vertical_gates[N][N];
int switch_type[N][N];

int di[] = {-1, 1, 0, 0};
int dj[] = {0, 0, -1, 1};

mt19937 rng(42);

bool is_gate_open(int g, int mask)
{
    int k = g / 2;
    int is_odd = g % 2;
    int active = (mask >> k) & 1;
    return is_odd ? (active == 1) : (active == 0);
}

Gate get_edge_gate(pair<int, int> p1, pair<int, int> p2, int g_type)
{
    if (p1.first == p2.first)
        return {1, p1.first, min(p1.second, p2.second), g_type};
    else
        return {0, min(p1.first, p2.first), p1.second, g_type};
}

// 評価関数（マクログラフ）
int evaluate()
{
    vector<int> check_pos = {0, N * N - 1};
    for (int i = 0; i < N; ++i)
    {
        for (int j = 0; j < N; ++j)
        {
            if (switch_type[i][j] != -1)
                check_pos.push_back(i * N + j);
            if (horizontal_gates[i][j] != -1)
            {
                check_pos.push_back(i * N + j);
                check_pos.push_back((i + 1) * N + j);
            }
            if (vertical_gates[i][j] != -1)
            {
                check_pos.push_back(i * N + j);
                check_pos.push_back(i * N + (j + 1));
            }
        }
    }
    sort(check_pos.begin(), check_pos.end());
    check_pos.erase(unique(check_pos.begin(), check_pos.end()), check_pos.end());

    int P = check_pos.size();
    vector<int> pos_to_id(N * N, -1);
    for (int i = 0; i < P; ++i)
        pos_to_id[check_pos[i]] = i;

    vector<vector<pair<int, int>>> adj(P);
    for (int u = 0; u < P; ++u)
    {
        int si = check_pos[u] / N, sj = check_pos[u] % N;
        vector<vector<int>> d(N, vector<int>(N, INF));
        queue<pair<int, int>> q;
        d[si][sj] = 0;
        q.push({si, sj});

        while (!q.empty())
        {
            auto [ci, cj] = q.front();
            q.pop();
            int cid = pos_to_id[ci * N + cj];
            if (cid != -1 && cid != u)
                adj[u].push_back({cid, d[ci][cj]});

            for (int dir = 0; dir < 4; ++dir)
            {
                int ni = ci + di[dir], nj = cj + dj[dir];
                if (ni < 0 || ni >= N || nj < 0 || nj >= N || grid[ni][nj] == '#')
                    continue;
                bool has_gate = false;
                if (dir == 0 && horizontal_gates[ni][nj] != -1)
                    has_gate = true;
                if (dir == 1 && horizontal_gates[ci][cj] != -1)
                    has_gate = true;
                if (dir == 2 && vertical_gates[ni][nj] != -1)
                    has_gate = true;
                if (dir == 3 && vertical_gates[ci][cj] != -1)
                    has_gate = true;
                if (has_gate)
                    continue;
                if (d[ni][nj] == INF)
                {
                    d[ni][nj] = d[ci][cj] + 1;
                    q.push({ni, nj});
                }
            }
        }
    }

    int num_states = 1 << QUEST_SWITCHES;
    vector<vector<int>> dist(P, vector<int>(num_states, INF));
    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<pair<int, int>>> pq;
    int start_id = pos_to_id[0], goal_id = pos_to_id[N * N - 1];

    dist[start_id][0] = 0;
    pq.push({0, start_id * num_states + 0});

    while (!pq.empty())
    {
        auto [d, state] = pq.top();
        pq.pop();
        int u = state / num_states, mask = state % num_states;
        if (d > dist[u][mask])
            continue;
        if (u == goal_id)
            return d;

        int ui = check_pos[u] / N, uj = check_pos[u] % N;
        if (switch_type[ui][uj] != -1)
        {
            int s = switch_type[ui][uj];
            int next_mask = mask ^ (1 << s);
            if (d + 1 < dist[u][next_mask])
            {
                dist[u][next_mask] = d + 1;
                pq.push({d + 1, u * num_states + next_mask});
            }
        }

        for (auto &edge : adj[u])
        {
            int v = edge.first, cost = edge.second;
            if (d + cost < dist[v][mask])
            {
                dist[v][mask] = d + cost;
                pq.push({d + cost, v * num_states + mask});
            }
        }

        for (int dir = 0; dir < 4; ++dir)
        {
            int ni = ui + di[dir], nj = uj + dj[dir];
            if (ni < 0 || ni >= N || nj < 0 || nj >= N || grid[ni][nj] == '#')
                continue;

            int gate_g = -1;
            if (dir == 0 && horizontal_gates[ni][nj] != -1)
                gate_g = horizontal_gates[ni][nj];
            if (dir == 1 && horizontal_gates[ui][uj] != -1)
                gate_g = horizontal_gates[ui][uj];
            if (dir == 2 && vertical_gates[ni][nj] != -1)
                gate_g = vertical_gates[ni][nj];
            if (dir == 3 && vertical_gates[ui][uj] != -1)
                gate_g = vertical_gates[ui][uj];

            if (gate_g != -1 && is_gate_open(gate_g, mask))
            {
                int v = pos_to_id[ni * N + nj];
                if (v != -1 && d + 1 < dist[v][mask])
                {
                    dist[v][mask] = d + 1;
                    pq.push({d + 1, v * num_states + mask});
                }
            }
        }
    }
    return -1;
}

long long calculate_true_score(int T)
{
    if (T == -1)
        return 1;
    return round(1000000.0 * log2((double)T / (double)N));
}

// 動的モジュール生成（ユーザーの「袋小路」アイデアを具現化）
struct Triplet
{
    pair<int, int> A, B, C;
    vector<Gate> walls;
    int cost;
};

void build_hanoi_quest(vector<Gate> &best_g, vector<Switch> &best_s)
{
    vector<Triplet> all_triplets;
    for (int r = 0; r < N; ++r)
    {
        for (int c = 0; c < N; ++c)
        {
            if (grid[r][c] == '#')
                continue;
            pair<int, int> A = {r, c};
            for (int d1 = 0; d1 < 4; ++d1)
            {
                int rB = r + di[d1], cB = c + dj[d1];
                if (rB < 0 || rB >= N || cB < 0 || cB >= N || grid[rB][cB] == '#')
                    continue;
                pair<int, int> B = {rB, cB};
                for (int d2 = 0; d2 < 4; ++d2)
                {
                    int rC = rB + di[d2], cC = cB + dj[d2];
                    if (rC < 0 || rC >= N || cC < 0 || cC >= N || grid[rC][cC] == '#')
                        continue;
                    pair<int, int> C = {rC, cC};
                    if (A == C)
                        continue;

                    // 周囲を永久壁（型19）で塞ぎ、A-B-Cという一直線の袋小路を作る
                    vector<Gate> walls;
                    auto add_wall = [&](pair<int, int> pos, pair<int, int> exc1, pair<int, int> exc2)
                    {
                        for (int d = 0; d < 4; ++d)
                        {
                            int nr = pos.first + di[d], nc = pos.second + dj[d];
                            if (nr < 0 || nr >= N || nc < 0 || nc >= N || grid[nr][nc] == '#')
                                continue;
                            if ((nr == exc1.first && nc == exc1.second) || (nr == exc2.first && nc == exc2.second))
                                continue;
                            walls.push_back(get_edge_gate(pos, {nr, nc}, WALL_GATE_TYPE));
                        }
                    };
                    add_wall(A, B, B);
                    add_wall(B, A, C);

                    // コスト（必要な永久壁の数）を計算
                    all_triplets.push_back({A, B, C, walls, (int)walls.size()});
                }
            }
        }
    }

    // 玉座モジュールと8個のスイッチモジュールを重複なく選ぶ
    for (int attempt = 0; attempt < 5000; ++attempt)
    {
        vector<vector<bool>> used(N, vector<bool>(N, false));
        used[0][0] = true; // スタート地点の保護
        vector<Triplet> selected_mods;
        int total_walls = 0;

        // 玉座 (19,19) の袋小路を確保
        vector<Triplet> t_cands;
        for (auto &t : all_triplets)
            if (t.A.first == 19 && t.A.second == 19)
                t_cands.push_back(t);
        Triplet throne_mod = t_cands[rng() % t_cands.size()];
        used[throne_mod.A.first][throne_mod.A.second] = true;
        used[throne_mod.B.first][throne_mod.B.second] = true;
        used[throne_mod.C.first][throne_mod.C.second] = true;
        selected_mods.push_back(throne_mod);
        total_walls += throne_mod.cost;

        // 残り8個のスイッチ（S0〜S7）用の袋小路を確保
        vector<pair<int, int>> cand_indices;
        for (int i = 0; i < all_triplets.size(); ++i)
        {
            if (all_triplets[i].A.first == 19 && all_triplets[i].A.second == 19)
                continue;
            if (all_triplets[i].A.first == 0 && all_triplets[i].A.second == 0)
                continue;
            cand_indices.push_back({all_triplets[i].cost + (rng() % 5), i}); // コストが安い（壁が少なくて済む辺や角）を優先
        }
        sort(cand_indices.begin(), cand_indices.end());

        for (auto &ci : cand_indices)
        {
            auto &t = all_triplets[ci.second];
            if (used[t.A.first][t.A.second] || used[t.B.first][t.B.second] || used[t.C.first][t.C.second])
                continue;
            used[t.A.first][t.A.second] = true;
            used[t.B.first][t.B.second] = true;
            used[t.C.first][t.C.second] = true;
            total_walls += t.cost;
            selected_mods.push_back(t);
            if (selected_mods.size() == 9)
                break;
        }

        // ゲート数上限チェック (ギミック用18枚 + 永久壁 <= 50)
        if (selected_mods.size() < 9 || total_walls > (M - 18))
            continue;

        // S8の配置場所（ただの空きマス）
        pair<int, int> s8_pos = {-1, -1};
        vector<pair<int, int>> empty_cells;
        for (int i = 0; i < N; ++i)
            for (int j = 0; j < N; ++j)
                if (!used[i][j] && grid[i][j] != '#')
                    empty_cells.push_back({i, j});
        if (empty_cells.empty())
            continue;
        s8_pos = empty_cells[rng() % empty_cells.size()];
        used[s8_pos.first][s8_pos.second] = true;

        // 盤面に仮配置
        for (int i = 0; i < N; ++i)
            for (int j = 0; j < N; ++j)
            {
                horizontal_gates[i][j] = -1;
                vertical_gates[i][j] = -1;
                switch_type[i][j] = -1;
            }
        best_g.clear();
        best_s.clear();

        auto place_gate = [&](Gate g)
        {
            bool duplicate = false;
            for (auto &existing : best_g)
                if (existing.d == g.d && existing.i == g.i && existing.j == g.j)
                    duplicate = true;
            if (!duplicate)
            {
                if (g.d == 0)
                    horizontal_gates[g.i][g.j] = g.g;
                else
                    vertical_gates[g.i][g.j] = g.g;
                best_g.push_back(g);
            }
        };

        // 永久壁を配置
        for (auto &mod : selected_mods)
        {
            for (auto &w : mod.walls)
                place_gate(w);
        }

        // 経路チェック（スタートからすべての袋小路の入り口Cに行けるか？）
        queue<pair<int, int>> q;
        q.push({0, 0});
        vector<vector<bool>> vis(N, vector<bool>(N, false));
        vis[0][0] = true;
        while (!q.empty())
        {
            auto [r, c] = q.front();
            q.pop();
            for (int d = 0; d < 4; ++d)
            {
                int nr = r + di[d], nc = c + dj[d];
                if (nr < 0 || nr >= N || nc < 0 || nc >= N || grid[nr][nc] == '#' || vis[nr][nc])
                    continue;
                bool has_wall = false;
                if (d == 0 && horizontal_gates[nr][nc] != -1)
                    has_wall = true;
                if (d == 1 && horizontal_gates[r][c] != -1)
                    has_wall = true;
                if (d == 2 && vertical_gates[nr][nc] != -1)
                    has_wall = true;
                if (d == 3 && vertical_gates[r][c] != -1)
                    has_wall = true;
                if (!has_wall)
                {
                    vis[nr][nc] = true;
                    q.push({nr, nc});
                }
            }
        }

        bool all_reachable = true;
        for (auto &mod : selected_mods)
            if (!vis[mod.C.first][mod.C.second])
                all_reachable = false;
        if (!vis[s8_pos.first][s8_pos.second])
            all_reachable = false;

        if (all_reachable)
        {
            // 完璧な袋小路が完成！ロジックゲートとスイッチを配置する
            // Throne (index 0)
            place_gate(get_edge_gate(selected_mods[0].A, selected_mods[0].B, 1)); // S0=1
            place_gate(get_edge_gate(selected_mods[0].B, selected_mods[0].C, 2)); // S1=0

            // S0 ~ S7 (index 1 to 8)
            for (int k = 0; k <= 7; ++k)
            {
                place_gate(get_edge_gate(selected_mods[k + 1].A, selected_mods[k + 1].B, 2 * (k + 1) + 1)); // S_{k+1}=1
                place_gate(get_edge_gate(selected_mods[k + 1].B, selected_mods[k + 1].C, 2 * (k + 1) + 2)); // S_{k+2}=0
                switch_type[selected_mods[k + 1].A.first][selected_mods[k + 1].A.second] = k;
                best_s.push_back({selected_mods[k + 1].A.first, selected_mods[k + 1].A.second, k});
            }
            // S8
            switch_type[s8_pos.first][s8_pos.second] = 8;
            best_s.push_back({s8_pos.first, s8_pos.second, 8});

            if (evaluate() != -1)
            {
                cerr << "Genius Trap Built successfully on attempt " << attempt << endl;
                return;
            }
        }
    }
}

int main()
{
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int dummy_N, dummy_M, dummy_K;
    if (!(cin >> dummy_N >> dummy_M >> dummy_K))
        return 0;

    for (int i = 0; i < N; ++i)
    {
        for (int j = 0; j < N; ++j)
        {
            cin >> grid[i][j];
            horizontal_gates[i][j] = -1;
            vertical_gates[i][j] = -1;
            switch_type[i][j] = -1;
        }
    }

    vector<Gate> fixed_gates;      // 絶対にいじらないギミック＋袋小路の壁
    vector<Switch> fixed_switches; // 絶対にいじらないスイッチ

    // 【極悪トラップ構築】
    build_hanoi_quest(fixed_gates, fixed_switches);

    int initial_T = evaluate();
    long long current_score = calculate_true_score(initial_T);
    long long best_score = current_score;

    int max_extra_walls = M - fixed_gates.size();
    vector<Gate> extra_walls;
    vector<Gate> best_extra_walls;

    cerr << "--- Genius Base Score: " << current_score << " ---" << endl;

    // --- 【フェーズ】焼きなましによる追加の嫌がらせ壁配置 ---
    auto sa_start_time = chrono::steady_clock::now();
    double sa_time_limit = 1900.0;
    double start_temp = 10000.0, end_temp = 100.0;
    uniform_real_distribution<double> prob(0.0, 1.0);
    int iterations = 0;

    while (true)
    {
        if (iterations % 16 == 0)
        {
            auto now = chrono::steady_clock::now();
            double elapsed = chrono::duration_cast<chrono::milliseconds>(now - sa_start_time).count();
            if (elapsed > sa_time_limit)
                break;
        }
        iterations++;

        double temp = start_temp + (end_temp - start_temp) * (chrono::duration_cast<chrono::milliseconds>(chrono::steady_clock::now() - sa_start_time).count() / sa_time_limit);

        int op = rng() % 2;
        Gate removed_gate = {0, 0, 0, 0};
        int d = -1, i = -1, j = -1, idx = -1;

        if (op == 0)
        { // 壁追加
            if (extra_walls.size() >= max_extra_walls)
                continue;
            d = rng() % 2;
            i = rng() % N;
            j = rng() % N;
            if (d == 0)
            {
                if (i < 0 || i >= N - 1 || j < 0 || j >= N)
                    continue;
                if (grid[i][j] == '#' || grid[i + 1][j] == '#')
                    continue;
                if (horizontal_gates[i][j] != -1)
                    continue;
            }
            else
            {
                if (i < 0 || i >= N || j < 0 || j >= N - 1)
                    continue;
                if (grid[i][j] == '#' || grid[i][j + 1] == '#')
                    continue;
                if (vertical_gates[i][j] != -1)
                    continue;
            }
            if (d == 0)
                horizontal_gates[i][j] = WALL_GATE_TYPE;
            else
                vertical_gates[i][j] = WALL_GATE_TYPE;
            extra_walls.push_back({d, i, j, WALL_GATE_TYPE});
        }
        else if (op == 1)
        { // 壁削除
            if (extra_walls.empty())
                continue;
            idx = rng() % extra_walls.size();
            removed_gate = extra_walls[idx];
            if (removed_gate.d == 0)
                horizontal_gates[removed_gate.i][removed_gate.j] = -1;
            else
                vertical_gates[removed_gate.i][removed_gate.j] = -1;
            extra_walls.erase(extra_walls.begin() + idx);
        }

        bool accept = false;
        int new_T = evaluate();

        if (new_T != -1)
        {
            long long eval_score = calculate_true_score(new_T);
            double delta = (double)(eval_score - current_score);

            if (delta >= 0)
                accept = true;
            else if (prob(rng) < exp(delta / temp))
                accept = true;

            if (accept)
            {
                current_score = eval_score;
                if (eval_score > best_score)
                {
                    best_score = eval_score;
                    best_extra_walls = extra_walls;
                }
            }
        }

        if (!accept)
        {
            if (op == 0)
            {
                if (d == 0)
                    horizontal_gates[i][j] = -1;
                else
                    vertical_gates[i][j] = -1;
                extra_walls.pop_back();
            }
            else if (op == 1)
            {
                if (removed_gate.d == 0)
                    horizontal_gates[removed_gate.i][removed_gate.j] = WALL_GATE_TYPE;
                else
                    vertical_gates[removed_gate.i][removed_gate.j] = WALL_GATE_TYPE;
                extra_walls.insert(extra_walls.begin() + idx, removed_gate);
            }
        }
    }

    cerr << "Final Best Score: " << best_score << endl;

    // 出力
    cout << fixed_gates.size() + best_extra_walls.size() << "\n";
    for (const auto &g : fixed_gates)
        cout << g.d << " " << g.i << " " << g.j << " " << g.g << "\n";
    for (const auto &g : best_extra_walls)
        cout << g.d << " " << g.i << " " << g.j << " " << g.g << "\n";

    cout << fixed_switches.size() << "\n";
    for (const auto &s : fixed_switches)
        cout << s.p << " " << s.q << " " << s.s << "\n";

    return 0;
}