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

int di[] = {-1, 0, 1, 0}; // UP, RIGHT, DOWN, LEFT
int dj[] = {0, 1, 0, -1};

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
                if (dir == 2 && horizontal_gates[ci][cj] != -1)
                    has_gate = true;
                if (dir == 3 && vertical_gates[ni][nj] != -1)
                    has_gate = true;
                if (dir == 1 && vertical_gates[ci][cj] != -1)
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
            if (dir == 2 && horizontal_gates[ui][uj] != -1)
                gate_g = horizontal_gates[ui][uj];
            if (dir == 3 && vertical_gates[ni][nj] != -1)
                gate_g = vertical_gates[ni][nj];
            if (dir == 1 && vertical_gates[ui][uj] != -1)
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

struct TunnelResult
{
    bool valid;
    vector<Gate> gates;
    Switch sw;
    int cost;
    vector<pair<int, int>> used_cells;
};

// 任意の場所に指定の長さの袋小路を作れるかテストする関数
TunnelResult check_tunnel(int r, int c, int dir, int L, int logic1, int logic2, int s_val, const vector<vector<bool>> &used)
{
    TunnelResult res;
    res.valid = false;
    vector<pair<int, int>> cells;
    for (int k = 0; k <= L; ++k)
    {
        int nr = r + k * di[dir], nc = c + k * dj[dir];
        if (nr < 0 || nr >= N || nc < 0 || nc >= N || grid[nr][nc] == '#' || used[nr][nc])
            return res;
        cells.push_back({nr, nc});
    }

    vector<Gate> gates;
    int cost = 0;
    auto add_wall = [&](int r1, int c1, int r2, int c2)
    {
        if (r1 < 0 || r1 >= N || c1 < 0 || c1 >= N || r2 < 0 || r2 >= N || c2 < 0 || c2 >= N)
            return;
        if (grid[r1][c1] == '#' || grid[r2][c2] == '#')
            return;
        gates.push_back(get_edge_gate({r1, c1}, {r2, c2}, WALL_GATE_TYPE));
        cost++;
    };

    int back_dir = (dir + 2) % 4;
    add_wall(r, c, r + di[back_dir], c + dj[back_dir]);

    for (int k = 0; k < L; ++k)
    {
        int cr = r + k * di[dir], cc = c + k * dj[dir];
        int left_dir = (dir + 3) % 4, right_dir = (dir + 1) % 4;
        add_wall(cr, cc, cr + di[left_dir], cc + dj[left_dir]);
        add_wall(cr, cc, cr + di[right_dir], cc + dj[right_dir]);
    }

    if (L >= 1)
        gates.push_back(get_edge_gate(cells[0], cells[1], logic1));
    if (L >= 2)
        gates.push_back(get_edge_gate(cells[1], cells[2], logic2));

    res.valid = true;
    res.cost = cost;
    res.gates = gates;
    res.sw = {r, c, s_val};
    res.used_cells = cells;
    return res;
}

// ユーザーのアイデア「長さ違いの袋小路」を全自動で探索・配置する関数
bool build_dynamic_quest(vector<Gate> &best_g, vector<Switch> &best_s)
{
    for (int attempt = 0; attempt < 5000; ++attempt)
    {
        vector<vector<bool>> used(N, vector<bool>(N, false));
        used[0][0] = true;

        vector<Gate> cand_gates;
        vector<Switch> cand_switches;

        auto add_res = [&](const TunnelResult &res)
        {
            for (auto &g : res.gates)
                cand_gates.push_back(g);
            if (res.sw.s != -1)
                cand_switches.push_back(res.sw);
            for (auto &c : res.used_cells)
                used[c.first][c.second] = true;
        };

        // 1. 玉座の袋小路 (長さ1)
        TunnelResult t_throne;
        t_throne.cost = INF;
        for (int dir = 0; dir < 4; ++dir)
        {
            auto r = check_tunnel(19, 19, dir, 1, 1, -1, -1, used); // 扉(S0=ON)
            if (r.valid && r.cost < t_throne.cost)
                t_throne = r;
        }
        if (!t_throne.valid)
            continue;
        add_res(t_throne);

        bool fail = false;
        // 2. S0~S6の袋小路 (長さ2)
        for (int k = 0; k <= 6; ++k)
        {
            TunnelResult best_t;
            best_t.cost = INF;
            for (int r = 0; r < N; ++r)
            {
                for (int c = 0; c < N; ++c)
                {
                    for (int dir = 0; dir < 4; ++dir)
                    {
                        auto res = check_tunnel(r, c, dir, 2, 2 * (k + 1) + 1, 2 * (k + 1) + 2, k, used);
                        if (res.valid)
                        {
                            int score = res.cost * 100 + (rng() % 200); // 最少の壁で済む場所（隅っこなど）を優先
                            if (score < best_t.cost * 100)
                                best_t = res;
                        }
                    }
                }
            }
            if (!best_t.valid)
            {
                fail = true;
                break;
            }
            add_res(best_t);
        }
        if (fail)
            continue;

        // 3. S7の袋小路 (長さ1)
        TunnelResult best_s7;
        best_s7.cost = INF;
        for (int r = 0; r < N; ++r)
        {
            for (int c = 0; c < N; ++c)
            {
                for (int dir = 0; dir < 4; ++dir)
                {
                    auto res = check_tunnel(r, c, dir, 1, 17, -1, 7, used);
                    if (res.valid)
                    {
                        int score = res.cost * 100 + (rng() % 200);
                        if (score < best_s7.cost * 100)
                            best_s7 = res;
                    }
                }
            }
        }
        if (!best_s7.valid)
            continue;
        add_res(best_s7);

        // 4. S8 (扉なしの空きマス)
        TunnelResult best_s8;
        best_s8.cost = INF;
        for (int r = 0; r < N; ++r)
        {
            for (int c = 0; c < N; ++c)
            {
                if (!used[r][c] && grid[r][c] == '.')
                {
                    TunnelResult res;
                    res.valid = true;
                    res.cost = 0;
                    res.sw = {r, c, 8};
                    res.used_cells.push_back({r, c});
                    best_s8 = res;
                    break;
                }
            }
            if (best_s8.valid)
                break;
        }
        if (!best_s8.valid)
            continue;
        add_res(best_s8);

        // 重複した壁ゲート（隣接する袋小路が共有している壁）を整理して無駄を省く
        vector<Gate> final_gates;
        for (auto &g : cand_gates)
        {
            bool dup = false;
            for (auto &fg : final_gates)
                if (fg.d == g.d && fg.i == g.i && fg.j == g.j)
                {
                    dup = true;
                    break;
                }
            if (!dup)
                final_gates.push_back(g);
        }

        if (final_gates.size() > M)
            continue;

        // 生成されたトラップが完璧かシミュレータで確認
        for (int i = 0; i < N; ++i)
            for (int j = 0; j < N; ++j)
            {
                horizontal_gates[i][j] = -1;
                vertical_gates[i][j] = -1;
                switch_type[i][j] = -1;
            }
        for (auto &g : final_gates)
        {
            if (g.d == 0)
                horizontal_gates[g.i][g.j] = g.g;
            else
                vertical_gates[g.i][g.j] = g.g;
        }
        for (auto &s : cand_switches)
            switch_type[s.p][s.q] = s.s;

        int score = evaluate();
        if (score != -1)
        {
            best_g = final_gates;
            best_s = cand_switches;
            return true;
        }
    }
    return false;
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

    vector<Gate> fixed_gates;
    vector<Switch> fixed_switches;

    // 【ユーザー発案：究極の袋小路トラップ構築】
    if (!build_dynamic_quest(fixed_gates, fixed_switches))
    {
        cerr << "Failed to build quest." << endl;
        return 0; // 万が一見つからなかった場合（通常は数回で成功します）
    }

    int initial_T = evaluate();
    long long current_score = calculate_true_score(initial_T);
    long long best_score = current_score;

    int max_extra_walls = M - fixed_gates.size();
    vector<Gate> extra_walls;
    vector<Gate> best_extra_walls;

    cerr << "--- Genius Base Score: " << current_score << " ---" << endl;
    cerr << "Remaining Walls for SA: " << max_extra_walls << endl;

    // --- 【フェーズ】焼きなましによる追加の嫌がらせ壁配置 ---
    auto sa_start_time = chrono::steady_clock::now();
    double sa_time_limit = 1850.0;
    double start_temp = 10000.0, end_temp = 10.0;
    uniform_real_distribution<double> prob(0.0, 1.0);
    int iterations = 0;

    // トラップの構造（fixed_gates と fixed_switches）は絶対に壊さず、残りの壁だけを動かして蛇行迷路を作る
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