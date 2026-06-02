import { useState,useEffect } from "react";
import axios from "axios";

function SkeletonCard(){
  return(
    <div className="bg-gray-800 rounded-xl"></div>
  )
}

function MetricCard({label,value}){
  return(
    <div className="bg-gray-800 rounded-xl p-6 w-48 text-center mt-2 mb-2">
      <p className="text-gray-400 text-sm mb-2">{label}</p>
      <p className="text-White text-2xl font-bold">
        {value !== null ? parseFloat(value).toFixed(2) : "N/A"}
      </p>
    </div>
  )
}

function App() {
  const [ticker , setTicker] = useState('');
  const [confirmedTicker , setConfirmedTicker]=useState('');
  const [metrics , setMetrics] =useState(null);
  const [loading , setLoading] = useState(false);
  const [error , setError] = useState(null);
  function handleAnalyze(){
    setConfirmedTicker(ticker.trim().toUpperCase());
  }
  useEffect(()=>{
    if(!confirmedTicker) return;
    setLoading(true);
    setError(null);
    setMetrics(null);
    axios.get(`http://localhost:8000/all-metrics?ticker=${confirmedTicker}`)
        .then(response => {
          setMetrics(response.data);
          setLoading(false);
        })
        .catch(()=>{
          setError("Invalid ticker or server error.");
          setLoading(false);
        });
    },[confirmedTicker])
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <nav className="bg-gray-900 px-6 py-4 border-b border-gray-800">
        <h1 className="text-xl font-bold text-blue-400">Hello StockIQ</h1>
      </nav>
      <main className="flex flex-col items-center justify-center mt-32">
        <h2 className="text-3xl font-bold mb-8">Analyse Any Stock</h2>
        <input 
        className="bg-gray-800 text-white px-4 py-3 rounded-lg w-80 outline-none"
        placeholder="Enter ticker (e.g. AAPL)"
        value={ticker}
        onChange={(e)=> setTicker(e.target.value)}
        onKeyDown={(e)=>{
          if (e.key==="Enter"){
            handleAnalyze()
          }
        }}
        />
        <button
        onClick={()=>handleAnalyze()}
        className="mt-4 bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-lg font-semibold"
        >
          Analyze
        </button>
        {confirmedTicker &&(
          <p className="mt-6 text-green-400 text-xl font-semibold">
            Analysing : {confirmedTicker}
          </p>
        )}
        {loading && (<div className="mt-8 w-10 h-10 border-4 border-blue-400 border-t-transparent rounded-full animate-spin"/>)}
        {error && <p className="mt-8 text-red-400 text-lg">{error}</p>}
        {!loading && metrics && (
          <div className="flex flex-wrap gap-4 justify-center mt-8" >
            <MetricCard label="Volatility" value={metrics.annual_volatility} />
            <MetricCard label="Sharpe Ratio" value={metrics.sharpe_ratio}/>
            <MetricCard label="Value at Risk" value={metrics.value_at_risk}/>
            <MetricCard label="P/E Ratio" value={metrics.pe_ratio[confirmedTicker]}/>
            <MetricCard label="Dividend Yield" value={metrics.dividend_yield} />
          </div>
        )
        }
      </main>
    </div>
  )
}

export default App