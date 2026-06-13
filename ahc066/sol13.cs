// ルール
// 座標は全て y * width + x で表す

using System;
using System.Diagnostics;
using System.Net.NetworkInformation;
using System.Runtime.CompilerServices;
using System.Text;




int[] nmt = Console.ReadLine()!.Split().Select(int.Parse).ToArray();
int n = nmt[0];
int m = nmt[1];
int t = nmt[2];
var v = new List<string>();
for (int i = 0; i < n; i++) v.Add(Console.ReadLine()!);
var h = new List<string>();
for (int i = 0; i < n - 1; i++) h.Add(Console.ReadLine()!);
int[] ballPositions = new int[m];
int[] basketPositions = new int[m];
Console.Error.WriteLine($"n: {n}, m: {m}, t: {t}");
for (int i = 0; i < m; i++)
{
    int[] line = Console.ReadLine()!.Split().Select(int.Parse).ToArray();
    ballPositions[i] = line[0] * n + line[1];
    basketPositions[i] = line[2] * n + line[3];
}

var solver = new Solver(n, m, t, v, h, ballPositions, basketPositions);
var bestOperations = solver.Solve();
Console.Error.WriteLine(bestOperations.Length);
Console.WriteLine(bestOperations);


public static class Dir
{
    public const int Up = 0;
    public const int Left = 1;
    public const int Down = 2;
    public const int Right = 3;
}

public class FastArray2D<T>
{
    private readonly T[] _data;
    private readonly int _size1;

    public FastArray2D(int size0, int size1)
    {
        _data = new T[size0 * size1];
        _size1 = size1;
    }

    public T this[int i0, int i1]
    {
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        get => _data[i0 * _size1 + i1];
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        set => _data[i0 * _size1 + i1] = value;
    }

    public T[] RawData => _data;
}

public class LazyDistanceTable
{
    private static readonly int[] Dx = { 0, -1, 0, 1 };
    private static readonly int[] Dy = { -1, 0, 1, 0 };

    private readonly int _n;
    private readonly int _m;
    private readonly int _t;
    public string Macro { get; private set; }


    private readonly Queue<int> _queue;
    private readonly FastArray2D<int> _wallDist;
    private readonly int[] _macroNextState;
    private readonly FastArray2D<int> _dist;
    private readonly FastArray2D<int> _turn;
    private readonly FastArray2D<int> _prevState;
    private readonly FastArray2D<char> _prevOp;
    private readonly (char op, int state, int turn)[] _nextStates;

    private int _currentVersion;
    private readonly int[] _versionTable;
    private int _currentVisitedToken;
    private readonly int[] _visitedTokenTable;

    public LazyDistanceTable(
        int n,
        int m,
        int t,
        List<string> v,
        List<string> h,
        string macro
    )
    {
        _n = n; _m = m; _t = t;
        Macro = macro;

        int stateSize = _n * _n * 4;


        _wallDist = new FastArray2D<int>(_n * _n, 4);
        _macroNextState = new int[_n * _n * 4];

        PrecalcWallDist(v, h);
        PrecalcMacroNextState(macro);

        _queue = new Queue<int>(stateSize);
        _nextStates = new (char op, int state, int turn)[4];
        _dist = new FastArray2D<int>(stateSize, stateSize);
        _turn = new FastArray2D<int>(stateSize, stateSize);
        _prevState = new FastArray2D<int>(stateSize, stateSize);
        _prevOp = new FastArray2D<char>(stateSize, stateSize);

        _versionTable = new int[stateSize];
        _visitedTokenTable = new int[stateSize];
        Array.Fill(_versionTable, -1);
        Array.Fill(_visitedTokenTable, -1);
        _currentVersion = 0;
        _currentVisitedToken = 0;
    }

    public void ResetMacro(string macro)
    {
        Macro = macro;
        _currentVersion++;
        PrecalcMacroNextState(macro);
    }

    public (int y, int x) Forward(int y, int x, int dir, int times)
    {
        int fromPos = y * _n + x;
        int dist = Math.Min(times, _wallDist[fromPos, dir]);
        return (y + Dy[dir] * dist, x + Dx[dir] * dist);
    }

    public (int y, int x, int dir) PlayMacro(int y, int x, int dir)
    {
        foreach (char op in Macro)
        {
            switch (op)
            {
                case 'F': (y, x) = Forward(y, x, dir, 1); break;
                case 'L': dir = (dir + 1) % 4; break;
                case 'R': dir = (dir + 3) % 4; break;
            }
        }
        return (y, x, dir);
    }

    public (int y, int x, int dir) PlayOperations(int y, int x, int dir, string operations)
    {
        foreach (char op in operations)
        {
            switch (op)
            {
                case 'F': (y, x) = Forward(y, x, dir, 1); break;
                case 'L': dir = (dir + 1) % 4; break;
                case 'R': dir = (dir + 3) % 4; break;
                case 'P': (y, x, dir) = PlayMacro(y, x, dir); break;
            }
        }
        return (y, x, dir);
    }

    public (int dist, int turn, int toPos, int toDir) Get(int fromPos, int fromDir, int toPos)
    {
        int fromState = EncodeState(fromPos, fromDir);
        if (_versionTable[fromState] != _currentVersion)
        {
            ComputeBfs(fromPos, fromDir);
            _versionTable[fromState] = _currentVersion;
        }

        // 全ての toDir で最小の dist を探す
        var bestDist = int.MaxValue;
        var bestDir = -1;
        var bestTurn = -1;

        for (int toDir = 0; toDir < 4; toDir++)
        {
            int toState = EncodeState(toPos, toDir);
            if (_dist[fromState, toState] < bestDist)
            {
                bestDist = _dist[fromState, toState];
                bestDir = toDir;
                bestTurn = _turn[fromState, toState];
            }
        }

        return (bestDist, bestTurn, toPos, bestDir);
    }

    public (List<char> path, int toPos, int toDir) GetPath(int fromPos, int fromDir, int toPos)
    {
        var (_, _, _, toDir) = Get(fromPos, fromDir, toPos);

        int fromState = EncodeState(fromPos, fromDir);
        int currentState = EncodeState(toPos, toDir);
        var path = new List<char>();

        while (currentState != fromState)
        {
            char op = _prevOp[fromState, currentState];
            path.Add(op);
            currentState = _prevState[fromState, currentState];
        }
        path.Reverse();
        return (path, toPos, toDir);
    }

    private void PrecalcWallDist(
        List<string> v,
        List<string> h
    )
    {

        for (int y = 0; y < _n; y++)
        {
            for (int x = 0; x < _n; x++)
            {
                int pos = y * _n + x;
                // 上方向
                if (y == 0 || h[y - 1][x] == '1') _wallDist[pos, Dir.Up] = 0;
                else _wallDist[pos, Dir.Up] = _wallDist[(y - 1) * _n + x, Dir.Up] + 1;
                // 左方向
                if (x == 0 || v[y][x - 1] == '1') _wallDist[pos, Dir.Left] = 0;
                else _wallDist[pos, Dir.Left] = _wallDist[y * _n + x - 1, Dir.Left] + 1;
            }
        }
        for (int y = _n - 1; y >= 0; y--)
        {
            for (int x = _n - 1; x >= 0; x--)
            {
                int pos = y * _n + x;
                // 下方向
                if (y == _n - 1 || h[y][x] == '1') _wallDist[pos, Dir.Down] = 0;
                else _wallDist[pos, Dir.Down] = _wallDist[(y + 1) * _n + x, Dir.Down] + 1;
                // 右方向
                if (x == _n - 1 || v[y][x] == '1') _wallDist[pos, Dir.Right] = 0;
                else _wallDist[pos, Dir.Right] = _wallDist[y * _n + x + 1, Dir.Right] + 1;
            }
        }
    }

    private void PrecalcMacroNextState(string macro)
    {
        for (int y = 0; y < _n; y++)
        {
            for (int x = 0; x < _n; x++)
            {
                for (int dir = 0; dir < 4; dir++)
                {
                    var (ny, nx, ndir) = PlayMacro(y, x, dir);
                    _macroNextState[EncodeState(y * _n + x, dir)] = EncodeState(ny * _n + nx, ndir);
                }
            }
        }
    }

    private void ComputeBfs(int fromPos, int fromDir)
    {
        int macroLength = Macro.Length;
        int fromState = EncodeState(fromPos, fromDir);
        _dist[fromState, fromState] = 0;
        _turn[fromState, fromState] = 0;
        _currentVisitedToken++;
        _visitedTokenTable[fromState] = _currentVisitedToken;

        _queue.Clear();
        _queue.Enqueue(fromState);

        while (_queue.Count > 0)
        {
            int currentState = _queue.Dequeue();
            int currentPos = currentState / 4;
            int currentDir = currentState % 4;
            int y = currentPos / _n;
            int x = currentPos % _n;

            // 前進
            var (ny, nx) = Forward(y, x, currentDir, 1);
            _nextStates[0] = ('F', EncodeState(ny * _n + nx, currentDir), 1);

            // 左折
            _nextStates[1] = ('L', EncodeState(currentPos, (currentDir + 1) % 4), 1);

            // 右折
            _nextStates[2] = ('R', EncodeState(currentPos, (currentDir + 3) % 4), 1);

            // マクロ
            _nextStates[3] = ('P', _macroNextState[currentState], macroLength);

            foreach (var (op, nextState, turn) in _nextStates)
            {
                if (_visitedTokenTable[nextState] == _currentVisitedToken) continue;
                _visitedTokenTable[nextState] = _currentVisitedToken;

                _dist[fromState, nextState] = _dist[fromState, currentState] + 1;
                _turn[fromState, nextState] = _turn[fromState, currentState] + turn;
                _prevState[fromState, nextState] = currentState;
                _prevOp[fromState, nextState] = op;
                _queue.Enqueue(nextState);
            }
        }
    }

    private int EncodeState(int pos, int dir) => pos * 4 + dir;
}

public abstract class Simulator
{
    protected static readonly Random Rand = new Random(0);

    protected readonly int N;
    protected readonly int M;
    protected readonly int T;
    protected readonly int[] BallPositions;
    protected readonly int[] BasketPositions;
    protected readonly LazyDistanceTable DistanceTable;

    protected Simulator(
        int n,
        int m,
        int t,
        int[] ballPositions,
        int[] basketPositions,
        LazyDistanceTable distanceTable
    )
    {
        N = n; M = m; T = t;
        BallPositions = ballPositions;
        BasketPositions = basketPositions;
        DistanceTable = distanceTable;
    }

    protected (List<int> route, int score) InitializeRouteByGreedy(
        string macro
    )
    {
        int currentPos = 0;
        int currentDir = Dir.Right;
        int currentScore = macro.Length + 1; // 最初の 'P' を "M...M" に置き換えたときのコスト
        int currentTurn = currentScore;

        var route = new List<int>();
        var remainingBalls = new HashSet<int>(Enumerable.Range(0, M));

        int dist, turn;
        while (remainingBalls.Count > 0)
        {
            int bestBall = -1;
            int bestDist = int.MaxValue;

            foreach (int ball in remainingBalls)
            {
                (dist, _, _, _) = DistanceTable.Get(currentPos, currentDir, ball);
                if (dist < bestDist)
                {
                    bestDist = dist;
                    bestBall = ball;
                }
            }

            // ボールを取る
            (dist, turn, currentPos, currentDir) = DistanceTable.Get(currentPos, currentDir, BallPositions[bestBall]);
            currentScore += dist + 1;
            currentTurn += turn + 1;

            // 対応するカゴに入れに行く
            (dist, turn, currentPos, currentDir) = DistanceTable.Get(currentPos, currentDir, BasketPositions[bestBall]);
            currentScore += dist + 1;
            currentTurn += turn + 1;

            if (currentTurn > T)
            {
                currentScore = remainingBalls.Count * T;
                break;
            }

            route.Add(bestBall);
            remainingBalls.Remove(bestBall);
        }

        // ボールが入り切らなければ、ルートに足しておく
        foreach (int ball in remainingBalls)
        {
            route.Add(ball);
        }

        return (route, currentScore);
    }

    protected int EvaluateRoute(string macro, List<int> route)
    {

        int currentPos = 0;
        int currentDir = Dir.Right;
        int currentScore = macro.Length + 1; // 最初の 'P' を "M...M" に置き換えたときのコスト
        int currentTurn = currentScore;

        for (int i = 0; i < route.Count; i++)
        {
            int ball = route[i];

            // ボールを取る
            int dist, turn;
            (dist, turn, currentPos, currentDir) = DistanceTable.Get(currentPos, currentDir, BallPositions[ball]);
            currentScore += dist + 1;
            currentTurn += turn + 1;

            // 対応するカゴに入れに行く
            (dist, turn, currentPos, currentDir) = DistanceTable.Get(currentPos, currentDir, BasketPositions[ball]);
            currentScore += dist + 1;
            currentTurn += turn + 1;

            if (currentTurn > T)
            {
                return (M - i) * T;
            }
        }

        return currentScore;
    }
}

public class ClimbSimulator : Simulator
{
    private const int Steps = 256;

    private readonly List<int> _newRoute;

    public ClimbSimulator(int n, int m, int t, int[] ballPositions, int[] basketPositions, LazyDistanceTable distanceTable)
        : base(n, m, t, ballPositions, basketPositions, distanceTable)
    {
        _newRoute = new List<int>(new int[m]);
    }

    public int Evaluate(string macro)
    {
        if (DistanceTable.Macro != macro) DistanceTable.ResetMacro(macro);

        var (bestRoute, bestScore) = InitializeRouteByGreedy(macro);

        for (int step = 0; step < Steps; step++)
        {
            int i = Rand.Next(M);
            int j = (i + Rand.Next(1, M)) % M;

            for (int k = 0; k < M; k++) _newRoute[k] = bestRoute[k];
            double mode = Rand.NextDouble();

            if (mode < 0.2) // swap
            {
                (_newRoute[i], _newRoute[j]) = (_newRoute[j], _newRoute[i]);
            }
            else if (mode < 0.6) // reverse
            {
                if (i > j) (i, j) = (j, i);
                _newRoute.Reverse(i, j - i + 1);
            }
            else // insert
            {
                int ball = _newRoute[i];
                _newRoute.RemoveAt(i);
                _newRoute.Insert(j, ball);
            }

            int newScore = EvaluateRoute(macro, _newRoute);
            if (newScore < bestScore)
            {
                bestScore = newScore;
                for (int k = 0; k < M; k++) bestRoute[k] = _newRoute[k];
            }
        }

        return bestScore;
    }
}

public class AnnealSimulator : Simulator
{
    private const int Steps = 9000;
    private const double EndTemperature = 0.1;

    private readonly List<int> _newRoute;
    public AnnealSimulator(int n, int m, int t, int[] ballPositions, int[] basketPositions, LazyDistanceTable distanceTable)
        : base(n, m, t, ballPositions, basketPositions, distanceTable)
    {
        _newRoute = new List<int>(new int[m]);
    }

    public string CalcBestOperations(string macro)
    {
        if (DistanceTable.Macro != macro) DistanceTable.ResetMacro(macro);

        var (currentRoute, currentScore) = InitializeRouteByGreedy(macro);
        var bestRoute = new List<int>(currentRoute);
        int bestScore = currentScore;

        double startTemperature;
        if (M < 30)
        {
            startTemperature = 1.0;
        }
        else
        {
            startTemperature = 0.5;
        }

        for (int step = 0; step < Steps; step++)
        {
            double fraction = (double)step / Steps;
            double temperature = startTemperature + fraction * (EndTemperature - startTemperature);

            int i = Rand.Next(M);
            int j = (i + Rand.Next(1, M)) % M;

            for (int k = 0; k < M; k++) _newRoute[k] = currentRoute[k];

            // --- 今回のステップで試す初動 ---

            double mode = Rand.NextDouble();

            if (mode < 0.2) // swap 
            {
                (_newRoute[i], _newRoute[j]) = (_newRoute[j], _newRoute[i]);
            }
            else if (mode < 0.6) // reverse 
            {
                if (i > j) (i, j) = (j, i);
                _newRoute.Reverse(i, j - i + 1);
            }
            else // insert 
            {
                int ball = _newRoute[i];
                _newRoute.RemoveAt(i);
                _newRoute.Insert(j, ball);
            }


            int newScore = EvaluateRoute(macro, _newRoute);

            int delta = newScore - currentScore;

            if (delta < 0 || Math.Exp(-delta / temperature) > Rand.NextDouble())
            {
                currentScore = newScore;

                for (int k = 0; k < M; k++) currentRoute[k] = _newRoute[k];

                if (currentScore < bestScore)
                {
                    Console.Error.WriteLine($"New best score: {currentScore} at step {step} (macro: {macro})");
                    bestScore = currentScore;

                    for (int k = 0; k < M; k++) bestRoute[k] = currentRoute[k];
                }
            }
        }

        // --- 最終的に一番良かった初動と経路を渡す ---
        return BuildOperations(macro, bestRoute);
    }

    private string BuildOperations(string macro, List<int> route)
    {
        var operations = new List<char>();
        int currentPos = 0;
        int currentDir = Dir.Right;

        List<char> path;
        for (int i = 0; i < route.Count; i++)
        {
            int ball = route[i];

            // ボールを取る
            (path, currentPos, currentDir) = DistanceTable.GetPath(currentPos, currentDir, BallPositions[ball]);
            operations.AddRange(path);
            operations.Add('S'); // 取る

            // 対応するカゴに入れに行く
            (path, currentPos, currentDir) = DistanceTable.GetPath(currentPos, currentDir, BasketPositions[ball]);
            operations.AddRange(path);
            operations.Add('S'); // 入れる
        }

        // 最初に現れる 'P' をマクロに置き換える
        var sb = new StringBuilder();
        bool macroUsed = false;
        for (int i = 0; i < operations.Count; i++)
        {
            if (!macroUsed && operations[i] == 'P')
            {
                sb.Append('M');
                sb.Append(macro);
                sb.Append('M');
                macroUsed = true;
            }
            else
            {
                sb.Append(operations[i]);
            }
        }


        return sb.ToString();
    }
}

/// <summary>
/// BitDP で最短経路を求めるクラス
/// 計算量は O(2^M * M) で、M=16 なら十分高速に動くはず
/// メモ化再帰
/// </summary>
public class ShortestPathCalculator16Bit
{

    public ShortestPathCalculator16Bit(
        int n,
        int m,
        int t,


    )
}

public class Solver
{
    Random Rand = new Random();
    StringBuilder Sb = new StringBuilder();

    private readonly int _n, _m, _t, _numWalls;
    private readonly int[] _ballPositions, _basketPositions;
    private readonly LazyDistanceTable _distanceTable;

    public Solver(int n, int m, int t, List<string> v, List<string> h, int[] ballPositions, int[] basketPositions)
    {
        _n = n; _m = m; _t = t;
        _ballPositions = ballPositions;
        _basketPositions = basketPositions;
        _distanceTable = new LazyDistanceTable(n, m, t, v, h, "");
        foreach (var row in v) foreach (char c in row) if (c == '1') _numWalls++;
        foreach (var row in h) foreach (char c in row) if (c == '1') _numWalls++;
    }

    public string Solve()
    {
        int timeLimitMs = 1600;
        var sw = Stopwatch.StartNew();

        var climbSimulator = new ClimbSimulator(_n, _m, _t, _ballPositions, _basketPositions, _distanceTable);

        var uniqueMacros = new HashSet<string>();

        string bestMacro = "";
        int bestScore = int.MaxValue;

        int itr = 0;
        while (true)
        {
            if (itr % 32 == 0 && sw.ElapsedMilliseconds > timeLimitMs) break;
            itr++;

            string macro = GenerateRandomMacro();
            if (uniqueMacros.Contains(macro)) continue;
            uniqueMacros.Add(macro);

            int score = climbSimulator.Evaluate(macro);
            if (score < bestScore)
            {
                Console.Error.WriteLine($"New best score: {score} (macro: {macro})");
                bestScore = score;
                bestMacro = macro;
            }
        }

        Console.Error.WriteLine($"Total iterations: {itr} within {sw.ElapsedMilliseconds} ms");

        var annealSimulator = new AnnealSimulator(_n, _m, _t, _ballPositions, _basketPositions, _distanceTable);
        var bestOperations = annealSimulator.CalcBestOperations(bestMacro);

        return bestOperations;
    }

    private string GenerateRandomMacro()
    {
        Sb.Clear();

        double avg = _n * 0.7;
        double std = _n * 0.5;
        int numForward = (int)Rand.NextGaussianClt(avg, std);
        numForward = Math.Clamp(numForward, 5, 22);
        int numTurn;
        if (_numWalls < _n * 2) // 壁が少ない場合はターン不要
        {
            numTurn = 1;
        }
        else if (_numWalls < _n * 6)
        {
            numTurn = Rand.Next(0, 2) * 2 + 1; // 1 or 3
        }
        else // 壁が多い場合はターン多め
        {
            numTurn = 3;
        }

        int[] points = new int[numForward];
        for (int i = 0; i < numForward; i++) { points[i] = i; }
        Rand.Shuffle(points);

        for (int i = 0; i < numForward; i++)
        {
            if (points[i] < numTurn)
            {
                if (Rand.NextDouble() < 0.5) { Sb.Append('L'); }
                else { Sb.Append('R'); }
            }
            Sb.Append('F');
        }

        double suffixProbability = Rand.NextDouble();
        if (suffixProbability < 0.7) { Sb.Append("RR"); }
        else if (suffixProbability < 0.8) { Sb.Append('R'); }
        else if (suffixProbability < 0.9) { Sb.Append('L'); }


        return Sb.ToString();
    }
}

public static class RandomExtensions
{
    /// <summary>
    /// 中心極限定理を利用した正規分布に従う乱数を生成します。
    /// </summary>

    public static double NextGaussianClt(this Random rand, double mean = 0, double stddev = 1)
    {
        // 中心極限定理を利用して、12個の一様乱数の合計から正規分布に従う乱数を生成
        double sum = 0;
        for (int i = 0; i < 12; i++)
        {
            sum += rand.NextDouble();
        }
        return mean + stddev * (sum - 6); // 平均を引いて標準偏差をかける
    }
}