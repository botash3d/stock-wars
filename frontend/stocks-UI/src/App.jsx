import { useState, useEffect } from "react";
import axios from "axios";
import { LineChart, Line,BarChart,Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,Legend } from "recharts";
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';


const RANGES = ["1D", "5D", "1M", "6M", "YTD", "1Y", "5Y", "MAX"];

function MetricCard({ label, value }) {
  return (
    <div className="bg-gray-800 rounded-xl p-6 w-48 text-center mt-2 mb-2">
      <p className="text-gray-400 text-sm mb-2">{label}</p>
      <p className="text-white text-2xl font-bold">
        {value !== null ? parseFloat(value).toFixed(2) : "N/A"}
      </p>
    </div>
  );
}
function FundamentalCard({ label, values, unit = "percent" }) {
  if (!values || values.length === 0) {
    return (
      <div className="bg-gray-800 rounded-xl p-4 w-48 text-center mt-2 mb-2">
        <p className="text-gray-400 text-sm mb-2">{label}</p>
        <p className="text-white text-xl font-bold">N/A</p>
      </div>
    );
  }

  const latest = values[0];
  const chronological = [...values].reverse().map((v, i) => ({ idx: i, value: v }));

  const formatValue = (v) => {
    const sign = v < 0 ? "-" : "";
    const abs = Math.abs(v);
    if (unit === "percent") return `${v.toFixed(2)}%`;
    if (unit === "ratio") return `${v.toFixed(2)}x`;
    if (unit === "currency") {
      if (abs >= 1e9) return `${sign}$${(abs / 1e9).toFixed(2)}B`;
      if (abs >= 1e6) return `${sign}$${(abs / 1e6).toFixed(2)}M`;
      return `${sign}$${abs.toFixed(2)}`;
    }
    return v.toFixed(2);
  };

  return (
    <div className="bg-gray-800 rounded-xl p-4 w-48 text-center mt-2 mb-2">
      <p className="text-gray-400 text-sm mb-1">{label}</p>
      <p className="text-white text-xl font-bold mb-2">{formatValue(latest)}</p>
      {chronological.length > 1 && (
        <ResponsiveContainer width="100%" height={40}>
          <LineChart data={chronological}>
            <Line type="monotone" dataKey="value" stroke="#60a5fa" dot={false} strokeWidth={1.5} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

function PredictionCard({ data , name }) {
  const isUp = data.direction_absolute === "up";
  const beats = data.direction === "outperform";

  return (
    <div className="bg-gray-800 rounded-xl p-5 w-64 text-center">
      <p className="text-gray-400 text-sm mb-1">30-Day Prediction</p>
      <p className="text-white font-semibold text-sm mb-2">{name}</p>
      <p className="text-2xl font-bold mb-1" style={{ color: isUp ? "#34d399" : "#f87171" }}>
        {isUp ? "▲" : "▼"} {Math.abs(data.absolute_pct)}%
      </p>
      <p className="text-sm mb-2" style={{ color: beats ? "#34d399" : "#f87171" }}>
        {beats ? "↑ Outperforms" : "↓ Underperforms"} SPY by {Math.abs(data.relative_pct)}%
      </p>
      <p className="text-xs text-gray-500">SPY expected: {data.spy_pct}%</p>
      <p className="text-xs text-gray-600 mt-1">vs next 30 days</p>
    </div>
  );
}

function CompareVerdictCard({ ticker1, pred1, name1, ticker2, pred2, name2 }) {
  const winner = pred1.relative_pct > pred2.relative_pct ? ticker1 : ticker2;
  const winnerPred = pred1.relative_pct > pred2.relative_pct ? pred1 : pred2;
  const loserPred = pred1.relative_pct > pred2.relative_pct ? pred2 : pred1;
  const loser = pred1.relative_pct > pred2.relative_pct ? ticker2 : ticker1;

  return (
    <div className="bg-gray-900 rounded-2xl p-6 w-full max-w-3xl mt-4">
      <h3 className="text-lg font-bold text-center mb-4 text-white">30-Day Prediction</h3>
      <div className="flex justify-center gap-6 mb-4">
        <PredictionCard data={pred1} name={name1} />
        <PredictionCard data={pred2} name={name2} />
      </div>
      <div className="bg-gray-700 rounded-xl p-4 text-center">
        <p className="text-gray-400 text-sm mb-1">Verdict</p>
        <p className="text-white font-bold text-lg">
          <span style={{ color: "#34d399" }}>{winner}</span> has higher upside
        </p>
        <p className="text-gray-400 text-sm mt-1">
          {winner} beats SPY by <span className="text-green-400">{Math.abs(winnerPred.relative_pct)}%</span>
          {" · "}
          {loser} beats SPY by <span style={{ color: loserPred.relative_pct < 0 ? "#f87171" : "#34d399" }}>
            {loserPred.relative_pct}%
          </span>
        </p>
      </div>
    </div>
  );
}

function App() {
  const [ticker, setTicker] = useState('');
  const [confirmedTicker, setConfirmedTicker] = useState('');
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [compareTicker, setCompareTicker] = useState('');
  const [confirmedCompareTicker, setConfirmedCompareTicker] = useState('');
  const [range, setRange] = useState("1Y");
  const [chartData, setChartData] = useState([]);
  const [chartLoading, setChartLoading] = useState(false);
  const [chartError, setChartError] = useState(null);
  const [companyInfo, setCompanyInfo] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [comparePrediction, setComparePrediction] = useState(null);
  const [predictionLoading, setPredictionLoading] = useState(false);
  const [predictionError, setPredictionError] = useState(null);

  async function handleAnalyze() {
  setPrediction(null);
  setComparePrediction(null);
  setPredictionError(null);
  const t = ticker.trim().toUpperCase();
  if (!t) return;
  setConfirmedTicker(t);
  setConfirmedCompareTicker(compareTicker.trim().toUpperCase());
}

async function handlePredict() {
  if (!confirmedTicker) return;
  setPredictionLoading(true);
  setPredictionError(null);
  setPrediction(null);
  setComparePrediction(null);

  try {
    const res1 = await axios.get(`${API}/predict?ticker=${confirmedTicker}`);
    setPrediction(res1.data);

    if (confirmedCompareTicker) {
      const res2 = await axios.get(`${API}/predict?ticker=${confirmedCompareTicker}`);
      setComparePrediction(res2.data);
    }
  } catch (e) {
    setPredictionError("Prediction failed. Try again.");
  } finally {
    setPredictionLoading(false);
  }
}

  useEffect(() => {
  if (!confirmedTicker) return;
  setCompanyInfo(null);
  axios.get(`${API}/company-info?ticker=${confirmedTicker}`)
    .then(r => setCompanyInfo(r.data))
    .catch(() => setCompanyInfo({ name: confirmedTicker, sector: "N/A", market_cap: "N/A", price: null, currency: "" }));
}, [confirmedTicker]);

  useEffect(() => {
  if (!confirmedTicker) return;
  setChartLoading(true);
  setChartError(null);

  if (confirmedCompareTicker) {
    axios.get(`${API}/compare?ticker1=${confirmedTicker}&ticker2=${confirmedCompareTicker}&rng=${range}`)
      .then(response => {
        const { dates, ...series } = response.data;
        const [k1, k2] = Object.keys(series).filter(k => !k.endsWith('_vol'));
        setChartData(dates.map((d, i) => ({
          date: d,
          [k1]: series[k1][i],
          [k2]: series[k2][i],
          [`${k1}_vol`]: series[`${k1}_vol`][i],
          [`${k2}_vol`]: series[`${k2}_vol`][i],
        })));
        setChartLoading(false);
      })
      .catch(() => {
        setChartError("Couldn't load comparison data.");
        setChartLoading(false);
      });
  } else {
    axios.get(`${API}/price-history?ticker=${confirmedTicker}&rng=${range}`)
      .then(response => {
        const { dates, price,volume } = response.data;
        setChartData(dates.map((d, i) => ({ date: d, price: price[i],volume:volume[i] })));
        setChartLoading(false);
      })
      .catch(() => {
        setChartError("Couldn't load chart data.");
        setChartLoading(false);
      });
  }
}, [confirmedTicker, confirmedCompareTicker, range]);
useEffect(() => {
  if (!confirmedTicker) return;
  setLoading(true);
  setError(null);
  setMetrics(null);
  axios.get(`${API}/all-metrics?ticker=${confirmedTicker}`)
    .then(response => {
      setMetrics(response.data);
      setLoading(false);
    })
    .catch(() => {
      setError("Invalid ticker or server error.");
      setLoading(false);
    });
}, [confirmedTicker]);
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <nav className="bg-gray-900 px-6 py-4 border-b border-gray-800">
        <h1 className="text-xl font-bold text-blue-400">Hello StockIQ</h1>
      </nav>

      <main className="flex flex-col items-center justify-center mt-32 px-4">
        <h2 className="text-3xl font-bold mb-8">Analyse Any Stock</h2>
        <input
          className="bg-gray-800 text-white px-4 py-3 rounded-lg w-80 outline-none"
          placeholder="Enter ticker (e.g. AAPL)"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") handleAnalyze(); }}
        />
        <button
          onClick={() => handleAnalyze()}
          className="mt-4 bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-lg font-semibold"
        >
          Analyze
        </button>
        <div className="flex gap-2 mt-3">
        <input
          className="bg-gray-800 text-white px-4 py-2 rounded-lg w-56 outline-none text-sm"
          placeholder="Compare with (optional, e.g. MSFT)"
          value={compareTicker}
          onChange={(e) => setCompareTicker(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") handleAnalyze(); }}
        />
        {compareTicker && (
          <button
            onClick={() => { setCompareTicker(''); setConfirmedCompareTicker(''); }}
            className="bg-gray-800 text-gray-400 hover:text-white px-3 rounded-lg text-sm"
          >
            ✕
          </button>
        )}
      </div>
        {confirmedTicker && (
          <div className="mt-8 w-full max-w-3xl bg-gray-900 rounded-2xl px-6 py-4 flex items-center gap-4">
            {companyInfo?.logo && (
              <img
                src={companyInfo.logo}
                alt="logo"
                className="w-10 h-10 rounded-lg object-contain bg-white p-1"
                onError={(e) => e.target.style.display = 'none'}
              />
            )}
            <div className="flex-1 min-w-0">
              {companyInfo ? (
                <>
                  <h2 className="text-lg font-bold text-white truncate">{companyInfo.name}</h2>
                  <p className="text-sm text-gray-400">
                    {companyInfo.sector}
                    <span className="mx-2 text-gray-600">·</span>
                    Market Cap: <span className="text-gray-300">{companyInfo.market_cap}</span>
                  </p>
                </>
              ) : (
                <div className="animate-pulse">
                  <div className="h-4 bg-gray-700 rounded w-48 mb-2" />
                  <div className="h-3 bg-gray-700 rounded w-64" />
                </div>
              )}
            </div>
            {companyInfo?.price && (
              <div className="text-right shrink-0">
                <p className="text-xl font-bold text-white">{companyInfo.currency} {companyInfo.price}</p>
                <p className="text-xs text-gray-500">Current Price</p>
              </div>
            )}
          </div>
        )}

        {confirmedTicker && (
          <div className="mt-8 w-full max-w-3xl">
            <div className="flex gap-2 justify-center mb-4 flex-wrap">
              {RANGES.map((r) => (
                <button
                  key={r}
                  onClick={() => setRange(r)}
                  className={`px-3 py-1 rounded-md text-sm font-semibold transition ${
                    range === r ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>

            {chartLoading && (
              <div className="h-72 flex items-center justify-center">
                <div className="w-10 h-10 border-4 border-blue-400 border-t-transparent rounded-full animate-spin" />
              </div>
            )}

            {chartError && <p className="text-red-400 text-center">{chartError}</p>}

            {!chartLoading && !chartError && chartData.length > 0 && (
              <>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid stroke="#1f2937" strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#9ca3af" }} minTickGap={40} />
                  <YAxis
                    domain={['auto', 'auto']}
                    tick={{ fontSize: 10, fill: "#9ca3af" }}
                    tickFormatter={(v) => confirmedCompareTicker ? `${v}%` : v}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#1f2937", border: "none" }}
                    formatter={(value) => confirmedCompareTicker ? [`${value}%`, ''] : [value, 'Price']}
                  />
                  {confirmedCompareTicker ? (
                    <>
                      <Legend wrapperStyle={{ fontSize: '12px' }} />
                      <Line type="monotone" dataKey={confirmedTicker} stroke="#60a5fa" dot={false} strokeWidth={2} />
                      <Line type="monotone" dataKey={confirmedCompareTicker} stroke="#f87171" dot={false} strokeWidth={2} />
                    </>
                  ) : (
                    <Line type="monotone" dataKey="price" stroke="#60a5fa" dot={false} strokeWidth={2} />
                  )}
                </LineChart>
              </ResponsiveContainer>
              <ResponsiveContainer width="100%" height={80} className="mt-1">
                <BarChart data={chartData} barCategoryGap="20%">
                  <XAxis dataKey="date" hide />
                  <YAxis hide domain={['auto', 'auto']} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#1f2937", border: "none" }}
                    formatter={(value, name) => {
                      const label = confirmedCompareTicker
                        ? name.replace('_vol', '')
                        : "Volume";
                      const formatted = value >= 1_000_000
                        ? `${(value / 1_000_000).toFixed(1)}M`
                        : value >= 1_000
                        ? `${(value / 1_000).toFixed(1)}K`
                        : value;
                      return [formatted, label];
                    }}
                  />
                  {confirmedCompareTicker ? (
                    <>
                      <Bar dataKey={`${confirmedTicker}_vol`} fill="#60a5fa" opacity={0.5} />
                      <Bar dataKey={`${confirmedCompareTicker}_vol`} fill="#f87171" opacity={0.5} />
                    </>
                  ) : (
                    <Bar dataKey="volume" fill="#3b82f6" opacity={0.5} />
                  )}
                </BarChart>
              </ResponsiveContainer>
            </>
            )}
            
          </div>
        )}

        {confirmedTicker && (
          <div className="mt-6 flex flex-col items-center w-full max-w-3xl">
            <button
              onClick={handlePredict}
              disabled={predictionLoading}
              className="bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 disabled:text-gray-500 text-white px-6 py-3 rounded-lg font-semibold transition"
            >
              {predictionLoading ? "Predicting... (this may take 20s)" : "⚡ Predict Next 30 Days"}
            </button>

            {predictionError && (
              <p className="text-red-400 text-sm mt-3">{predictionError}</p>
            )}

            {prediction && !comparePrediction && (
              <div className="mt-4">
                <PredictionCard data={prediction} name={companyInfo?.name} />
              </div>
            )}

            {prediction && comparePrediction && (
              <CompareVerdictCard
                ticker1={confirmedTicker}
                pred1={prediction}
                name1={companyInfo?.name || confirmedTicker}
                ticker2={confirmedCompareTicker}
                pred2={comparePrediction}
                name2={confirmedCompareTicker}
              />
            )}
          </div>
        )}

        {loading && (<div className="mt-8 w-10 h-10 border-4 border-blue-400 border-t-transparent rounded-full animate-spin"/>)}
        {error && <p className="mt-8 text-red-400 text-lg">{error}</p>}
        {!loading && metrics && (
          <div className="flex flex-wrap gap-4 justify-center mt-8">
            <MetricCard label="Volatility" value={metrics.annual_volatility} />
            <MetricCard label="Sharpe Ratio" value={metrics.sharpe_ratio} />
            <MetricCard label="Value at Risk" value={metrics.value_at_risk} />
            <MetricCard label="P/E Ratio" value={metrics.pe_ratio} />
            <MetricCard label="Dividend Yield" value={metrics.dividend_yield} />
          </div>
        )}
        {!loading && metrics && (
          <div className="mt-12 w-full max-w-4xl">
            <h3 className="text-xl font-bold mb-4 text-center">Fundamentals</h3>
            <div className="flex flex-wrap gap-4 justify-center">
              <FundamentalCard label="Revenue Growth" values={metrics.revenue_growth} unit="percent" />
              <FundamentalCard label="Earnings Growth" values={metrics.earnings_growth} unit="percent" />
              <FundamentalCard label="Profit Margin" values={metrics.profit_margin} unit="percent" />
              <FundamentalCard label="Gross Margin" values={metrics.gross_margin} unit="percent" />
              <FundamentalCard label="ROE" values={metrics.roe} unit="percent" />
              <FundamentalCard label="Debt to Equity" values={metrics.debt_to_equity} unit="ratio" />
              <FundamentalCard label="Asset Turnover" values={metrics.asset_turnover} unit="ratio" />
              <FundamentalCard label="P/B Ratio" values={metrics.pb_ratio} unit="ratio" />
              <FundamentalCard label="P/S Ratio" values={metrics.ps_ratio} unit="ratio" />
              <FundamentalCard label="Operating Cash Flow" values={metrics.operating_cash_flow} unit="currency" />
              <FundamentalCard label="Free Cash Flow" values={metrics.free_cash_flow} unit="currency" />
              <FundamentalCard label="FCF Growth" values={metrics.free_cash_flow_growth} unit="percent" />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;