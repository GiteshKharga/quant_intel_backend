'use client'

import { useState } from 'react'
import { MarketWeatherCard } from '@/components/dashboard/market-weather'
import { AdvancedChart } from '@/components/dashboard/advanced-chart'
import { Search, Activity, Zap, TrendingUp, AlertTriangle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'

export default function Dashboard() {
  const [symbol, setSymbol] = useState('AAPL')
  const [searchInput, setSearchInput] = useState('')

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchInput) {
      setSymbol(searchInput.toUpperCase())
    }
  }

  return (
    <div className="flex flex-col min-h-screen">
      {/* Ticker Tape */}
      <div className="bg-black/40 border-b border-white/5 py-2 px-4 flex items-center gap-8 overflow-hidden whitespace-nowrap text-xs font-mono text-muted-foreground">
        <span className="flex items-center gap-2"><span className="text-green-500">▲</span> SPX 4,783.45 (+0.45%)</span>
        <span className="flex items-center gap-2"><span className="text-red-500">▼</span> NIFTY 21,456.10 (-0.23%)</span>
        <span className="flex items-center gap-2"><span className="text-green-500">▲</span> VIX 12.45 (-1.2%)</span>
        <span className="flex items-center gap-2"><span className="text-green-500">▲</span> BTC 43,210.00 (+2.1%)</span>
        <span className="flex items-center gap-2 text-cyan-400">⚡ SYSTEM: LOW LATENCY (12ms)</span>
      </div>

      <header className="px-6 py-4 flex flex-col md:flex-row justify-between items-center gap-4 bg-black/20 backdrop-blur-sm sticky top-0 z-50 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="bg-cyan-500/10 p-2 rounded-lg border border-cyan-500/20">
            <Zap className="w-6 h-6 text-cyan-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent tracking-tight">
              QUANT<span className="text-cyan-400">INTEL</span>
            </h1>
            <p className="text-[10px] text-muted-foreground uppercase tracking-[0.2em]">Institutional Terminal v1.0</p>
          </div>
        </div>

        <form onSubmit={handleSearch} className="relative w-full md:w-auto">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="SEARCH ASSET (e.g. RELIANCE.NS)"
            className="pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-1 focus:ring-cyan-500/50 w-full md:w-96 text-sm text-foreground placeholder:text-muted-foreground/50 transition-all focus:bg-white/10"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-1">
            <Badge variant="outline" className="text-[10px] h-5 bg-black/50 border-white/10 text-muted-foreground">CMD+K</Badge>
          </div>
        </form>

        <div className="flex items-center gap-3">
          <Badge variant="neon" className="hidden md:flex animate-pulse">LIVE FEED</Badge>
          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 border border-white/20" />
        </div>
      </header>

      <main className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-4 gap-6 max-w-[1600px] mx-auto w-full">
        {/* Left Column: Key Stats */}
        <div className="space-y-6 lg:col-span-1">
          <MarketWeatherCard symbol={symbol} />

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-black/40 border border-white/10 rounded-xl p-4 backdrop-blur-sm">
              <div className="text-xs text-muted-foreground mb-1 flex items-center gap-1"><Activity className="w-3 h-3" /> VOLATILITY</div>
              <div className="text-xl font-mono text-white">14.2%</div>
              <div className="text-xs text-green-500 mt-1">-2.1% (24h)</div>
            </div>
            <div className="bg-black/40 border border-white/10 rounded-xl p-4 backdrop-blur-sm">
              <div className="text-xs text-muted-foreground mb-1 flex items-center gap-1"><TrendingUp className="w-3 h-3" /> FLOW</div>
              <div className="text-xl font-mono text-green-400">+₹450Cr</div>
              <div className="text-xs text-muted-foreground mt-1">Net Buy</div>
            </div>
          </div>

          <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-4">
            <h3 className="text-sm font-bold text-red-400 flex items-center gap-2 mb-3">
              <AlertTriangle className="w-4 h-4" /> AI DANGER ALERTS
            </h3>
            <div className="space-y-3">
              <div className="text-xs text-white/80 p-2 bg-red-500/10 rounded border border-red-500/10">
                <span className="font-bold">IDEA.NS</span>: Ladder attack pattern detected (Confidence: 85%)
              </div>
              <div className="text-xs text-white/80 p-2 bg-red-500/10 rounded border border-red-500/10">
                <span className="font-bold">ADANIENT</span>: High gamma exposure zone at 3200
              </div>
            </div>
          </div>
        </div>

        {/* Center/Right: Charts & Visuals */}
        <div className="lg:col-span-3 space-y-6">
          <AdvancedChart symbol={symbol} />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 h-64">
            <div className="bg-black/40 border border-white/10 rounded-xl p-6 backdrop-blur-sm md:col-span-2 flex flex-col items-center justify-center text-muted-foreground border-dashed relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <span className="text-3xl mb-3">🐋</span>
              <p className="font-mono text-sm">INSTITUTIONAL HEATMAP</p>
              <Badge variant="outline" className="mt-2 text-[10px] bg-black/50">COMING SOON</Badge>
            </div>
            <div className="bg-black/40 border border-white/10 rounded-xl p-6 backdrop-blur-sm flex flex-col items-center justify-center text-muted-foreground border-dashed">
              <span className="text-3xl mb-3">🌪️</span>
              <p className="font-mono text-sm">STRESS TEST</p>
              <Badge variant="outline" className="mt-2 text-[10px] bg-black/50">COMING SOON</Badge>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
