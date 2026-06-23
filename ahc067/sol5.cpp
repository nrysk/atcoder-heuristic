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
const int K = 10;
const int INF = 1e9;
const int MAX_SWITCHES = 25;

const int WALL_GATE_TYPE = 19;
const int QUEST_SWITCHES = 9;

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

bool can_place_gate(int d, int i, int j)
{
    if (d == 0)
    {
        if (i < 0 || i >= N - 1 || j < 0 || j >= N)
            return false;
        if (grid[i][j] == '#' || grid[i + 1][j] == '#')
            return false;
        if (horizontal_gates[i][j] != -1)
            return false;
    }
    else
    {
        if (i < 0 || i >= N || j < 0 || j >= N - 1)
            return false;
        if (grid[i][j] == '#' || grid[i][j + 1] == '#')
            return false;
        if (vertical_gates[i][j] != -1)
            return false;
    }
    return true;
}

vector<vector<int>> get_distances(int start_r, int start_c)
{
    vector<vector<int>> d(N, vector<int>(N, -1));
    queue<pair<int, int>> q;
    q.push({start_r, start_c});
    d[start_r][start_c] = 0;

    while (!q.empty())
    {
        auto [r, c] = q.front();
        q.pop();
        for (int dir = 0; dir < 4; ++dir)
        {
            int nr = r + di[dir], nc = c + dj[dir];
            if (nr < 0 || nr >= N || nc < 0 || nc >= N || grid[nr][nc] == '#')
                continue;

            bool has_gate = false;
            if (dir == 0 && horizontal_gates[nr][nc] != -1)
                has_gate = true;
            if (dir == 1 && horizontal_gates[r][c] != -1)
                has_gate = true;
            if (dir == 2 && vertical_gates[nr][nc] != -1)
                has_gate = true;
            if (dir == 3 && vertical_gates[r][c] != -1)
                has_gate = true;

            if (has_gate)
                continue;

            if (d[nr][nc] == -1)
            {
                d[nr][nc] = d[r][c] + 1;
                q.push({nr, nc});
            }
        }
    }
    return d;
}

int evaluate()
{
    vector<int> check_pos;
    check_pos.push_back(0);
    check_pos.push_back(N * N - 1);
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
        vector<vector<int>> d = get_distances(si, sj);
        for (int i = 0; i < N; ++i)
        {
            for (int j = 0; j < N; ++j)
            {
                if (d[i][j] > 0)
                {
                    int cid = pos_to_id[i * N + j];
                    if (cid != -1 && cid != u)
                        adj[u].push_back({cid, d[i][j]});
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

// クエスト初期解の構築
void build_quest_initial_state(vector<Gate> &best_g, vector<Switch> &best_s)
{
    for (int attempt = 0; attempt < 500; ++attempt)
    {
        best_g.clear();
        best_s.clear();
        for (int i = 0; i < N; ++i)
            for (int j = 0; j < N; ++j)
            {
                horizontal_gates[i][j] = -1;
                vertical_gates[i][j] = -1;
                switch_type[i][j] = -1;
            }

        auto dist_start = get_distances(0, 0);
        bool top_ok = (N - 2 >= 0 && dist_start[N - 2][N - 1] != -1);
        bool left_ok = (N - 2 >= 0 && dist_start[N - 1][N - 2] != -1);

        if (!top_ok && !left_ok)
            continue;

        // 玉座ロック
        if (top_ok && left_ok)
        {
            if (rng() % 2 == 0)
            {
                horizontal_gates[N - 2][N - 1] = 1;
                best_g.push_back({0, N - 2, N - 1, 1});
                vertical_gates[N - 1][N - 2] = WALL_GATE_TYPE;
                best_g.push_back({1, N - 1, N - 2, WALL_GATE_TYPE});
            }
            else
            {
                horizontal_gates[N - 2][N - 1] = WALL_GATE_TYPE;
                best_g.push_back({0, N - 2, N - 1, WALL_GATE_TYPE});
                vertical_gates[N - 1][N - 2] = 1;
                best_g.push_back({1, N - 1, N - 2, 1});
            }
        }
        else if (top_ok)
        {
            horizontal_gates[N - 2][N - 1] = 1;
            best_g.push_back({0, N - 2, N - 1, 1});
        }
        else if (left_ok)
        {
            vertical_gates[N - 1][N - 2] = 1;
            best_g.push_back({1, N - 1, N - 2, 1});
        }

        int current_r = N - 1, current_c = N - 1;
        bool failed = false;

        for (int k = 0; k < QUEST_SWITCHES; ++k)
        {
            // ★バグ修正：S0の場合は密室の玉座からではなく、(0,0)から遠い場所を探す！
            auto dist_from_target = (k == 0) ? get_distances(0, 0) : get_distances(current_r, current_c);

            vector<pair<int, pair<int, int>>> candidates;
            for (int i = 0; i < N; ++i)
            {
                for (int j = 0; j < N; ++j)
                {
                    if (dist_from_target[i][j] != -1 && switch_type[i][j] == -1 && (i != 0 || j != 0) && (i != N - 1 || j != N - 1))
                    {
                        int score = dist_from_target[i][j] + (rng() % 5);
                        candidates.push_back({score, {i, j}});
                    }
                }
            }

            if (candidates.empty())
            {
                failed = true;
                break;
            }
            sort(candidates.begin(), candidates.end(), [](const auto &a, const auto &b)
                 { return a.first > b.first; });

            bool placed = false;
            for (auto &cand : candidates)
            {
                int r = cand.second.first, c = cand.second.second;
                int g = (k == QUEST_SWITCHES - 1) ? -1 : 2 * (k + 1) + 1;

                vector<Gate> temp_gates;
                if (g != -1)
                {
                    vector<int> dirs = {0, 1, 2, 3};
                    shuffle(dirs.begin(), dirs.end(), rng);
                    for (int dir : dirs)
                    {
                        int edge_d = -1, edge_i = -1, edge_j = -1;
                        if (dir == 0 && can_place_gate(0, r - 1, c))
                        {
                            edge_d = 0;
                            edge_i = r - 1;
                            edge_j = c;
                        }
                        if (dir == 1 && can_place_gate(0, r, c))
                        {
                            edge_d = 0;
                            edge_i = r;
                            edge_j = c;
                        }
                        if (dir == 2 && can_place_gate(1, r, c - 1))
                        {
                            edge_d = 1;
                            edge_i = r;
                            edge_j = c - 1;
                        }
                        if (dir == 3 && can_place_gate(1, r, c))
                        {
                            edge_d = 1;
                            edge_i = r;
                            edge_j = c;
                        }

                        if (edge_d != -1)
                        {
                            if (edge_d == 0)
                            {
                                horizontal_gates[edge_i][edge_j] = g;
                                temp_gates.push_back({0, edge_i, edge_j, g});
                            }
                            else
                            {
                                vertical_gates[edge_i][edge_j] = g;
                                temp_gates.push_back({1, edge_i, edge_j, g});
                            }
                            break;
                        }
                    }
                }

                auto check_d = get_distances(0, 0);
                bool route_ok = true;
                if (check_d[N - 1][N - 1] == -1)
                    route_ok = false;
                if (check_d[r][c] == -1)
                    route_ok = false;
                for (auto &s : best_s)
                {
                    if (check_d[s.p][s.q] == -1)
                    {
                        route_ok = false;
                        break;
                    }
                }

                if (route_ok)
                {
                    switch_type[r][c] = k;
                    best_s.push_back({r, c, k});
                    for (auto &tg : temp_gates)
                        best_g.push_back(tg);
                    current_r = r;
                    current_c = c;
                    placed = true;
                    break;
                }
                else
                {
                    for (auto &tg : temp_gates)
                    {
                        if (tg.d == 0)
                            horizontal_gates[tg.i][tg.j] = -1;
                        else
                            vertical_gates[tg.i][tg.j] = -1;
                    }
                }
            }
            if (!placed)
            {
                failed = true;
                break;
            }
        }
        if (!failed && evaluate() != -1)
            break; // 成功！
    }
}

// ★ユーザー様のアイデア：交互に壁を置いて「蛇行迷路」を作る
void build_zigzag_walls(vector<Gate> &wall_gates, int max_wall_gates)
{
    int row = 2;
    bool from_left = true;

    while (wall_gates.size() < max_wall_gates && row < N - 2)
    {
        int max_len = 12; // 壁の長さ（隙間を空けて通れるようにする）
        for (int c = 0; c < max_len && wall_gates.size() < max_wall_gates; ++c)
        {
            int j = from_left ? c : (N - 1 - c);
            if (can_place_gate(0, row, j))
            {
                horizontal_gates[row][j] = WALL_GATE_TYPE;
                wall_gates.push_back({0, row, j, WALL_GATE_TYPE});

                // もしこの壁を置いたせいでクエストが破綻（到達不能）したら、即キャンセル
                if (evaluate() == -1)
                {
                    horizontal_gates[row][j] = -1;
                    wall_gates.pop_back();
                }
            }
        }
        row += 3; // 3行おきに交互の壁を作る
        from_left = !from_left;
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

    vector<Gate> gimmick_gates;
    vector<Switch> switches;
    build_quest_initial_state(gimmick_gates, switches);

    int max_wall_gates = M - gimmick_gates.size();
    if (max_wall_gates < 0)
        max_wall_gates = 0;

    vector<Gate> wall_gates;

    // 焼きなましの前に、強力な「蛇行迷路」を初期配置する
    build_zigzag_walls(wall_gates, max_wall_gates);
    vector<Gate> best_wall_gates = wall_gates;

    int initial_T = evaluate();
    long long current_score = calculate_true_score(initial_T);
    long long best_score = current_score;

    cerr << "--- Initialization Complete ---" << endl;
    cerr << "Gimmick Gates Used: " << gimmick_gates.size() << endl;
    cerr << "Wall Gates Used: " << wall_gates.size() << " / " << max_wall_gates << endl;
    cerr << "Switches Used: " << switches.size() << endl;
    cerr << "Initial Base Score: " << current_score << endl;

    auto start_time = chrono::steady_clock::now();
    double time_limit = 2000.0;
    double start_temp = 10000.0, end_temp = 10.0;
    uniform_real_distribution<double> prob(0.0, 1.0);
    int iterations = 0;

    // 残りの時間で、壁の位置を微調整してさらにスコアを絞り出す
    while (true)
    {
        if (iterations % 16 == 0)
        {
            auto now = chrono::steady_clock::now();
            if (chrono::duration_cast<chrono::milliseconds>(now - start_time).count() > time_limit)
                break;
        }
        iterations++;

        double temp = start_temp + (end_temp - start_temp) * (chrono::duration_cast<chrono::milliseconds>(chrono::steady_clock::now() - start_time).count() / time_limit);

        int op = rng() % 2;
        Gate removed_gate = {0, 0, 0, 0};
        int d = -1, i = -1, j = -1, idx = -1;

        if (op == 0)
        {
            if (wall_gates.size() >= max_wall_gates)
                continue;
            d = rng() % 2;
            i = rng() % N;
            j = rng() % N;
            if (!can_place_gate(d, i, j))
                continue;
            if (d == 0)
                horizontal_gates[i][j] = WALL_GATE_TYPE;
            else
                vertical_gates[i][j] = WALL_GATE_TYPE;
            wall_gates.push_back({d, i, j, WALL_GATE_TYPE});
        }
        else if (op == 1)
        {
            if (wall_gates.empty())
                continue;
            idx = rng() % wall_gates.size();
            removed_gate = wall_gates[idx];
            if (removed_gate.d == 0)
                horizontal_gates[removed_gate.i][removed_gate.j] = -1;
            else
                vertical_gates[removed_gate.i][removed_gate.j] = -1;
            wall_gates.erase(wall_gates.begin() + idx);
        }

        int new_T = evaluate();
        bool accept = false;

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
                    best_wall_gates = wall_gates;
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
                wall_gates.pop_back();
            }
            else if (op == 1)
            {
                if (removed_gate.d == 0)
                    horizontal_gates[removed_gate.i][removed_gate.j] = WALL_GATE_TYPE;
                else
                    vertical_gates[removed_gate.i][removed_gate.j] = WALL_GATE_TYPE;
                wall_gates.insert(wall_gates.begin() + idx, removed_gate);
            }
        }
    }

    cerr << "--- Finished ---" << endl;
    cerr << "Final Best Score: " << best_score << endl;

    cout << gimmick_gates.size() + best_wall_gates.size() << "\n";
    for (const auto &g : gimmick_gates)
        cout << g.d << " " << g.i << " " << g.j << " " << g.g << "\n";
    for (const auto &g : best_wall_gates)
        cout << g.d << " " << g.i << " " << g.j << " " << g.g << "\n";

    cout << switches.size() << "\n";
    for (const auto &s : switches)
        cout << s.p << " " << s.q << " " << s.s << "\n";

    return 0;
}