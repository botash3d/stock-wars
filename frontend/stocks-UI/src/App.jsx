import { useState, useEffect } from "react";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,Legend } from "recharts";

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

  function handleAnalyze() {
    setConfirmedTicker(ticker.trim().toUpperCase());
    setConfirmedCompareTicker(compareTicker.trim().toUpperCase());
  }

  useEffect(() => {
  if (!confirmedTicker) return;
  setChartLoading(true);
  setChartError(null);

  if (confirmedCompareTicker) {
    axios.get(`http://localhost:8000/compare?ticker1=${confirmedTicker}&ticker2=${confirmedCompareTicker}&rng=${range}`)
      .then(response => {
        const { dates, ...series } = response.data;
        const [k1, k2] = Object.keys(series);
        setChartData(dates.map((d, i) => ({
          date: d,
          [k1]: series[k1][i],
          [k2]: series[k2][i],
        })));
        setChartLoading(false);
      })
      .catch(() => {
        setChartError("Couldn't load comparison data.");
        setChartLoading(false);
      });
  } else {
    axios.get(`http://localhost:8000/price-history?ticker=${confirmedTicker}&rng=${range}`)
      .then(response => {
        const { dates, price } = response.data;
        setChartData(dates.map((d, i) => ({ date: d, price: price[i] })));
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
  axios.get(`http://localhost:8000/all-metrics?ticker=${confirmedTicker}`)
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
          <p className="mt-6 text-green-400 text-xl font-semibold">
            Analysing : {confirmedTicker}
          </p>
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