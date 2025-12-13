'use client'

import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { AlertTriangle, CloudRain, Sun, Wind, CloudLightning } from 'lucide-react'
import { cn, formatPercentage } from '@/lib/utils'

interface MarketWeather {
    symbol: string
    price: number
    analysis: {
        volatility_score: number
        momentum_score: number
        liquidity_score: number
        safety_score: number
        market_condition: string
        regime: string
    }
    recommendation: {
        action: string
        confidence: number
    }
}

export function MarketWeatherCard({ symbol }: { symbol: string }) {
    const { data, isLoading, error } = useQuery({
        queryKey: ['market-weather', symbol],
        queryFn: async () => {
            const res = await axios.get(`/market/weather?symbol=${symbol}`)
            return res.data
        }
    })

    if (isLoading) return <div className="animate-pulse h-64 bg-card rounded-xl border border-border" />
    if (error) return <div className="h-64 bg-destructive/10 rounded-xl border border-destructive flex items-center justify-center text-destructive">Failed to load weather data</div>

    const weather = data as MarketWeather
    const score = weather?.analysis?.safety_score || 0

    // Determine color based on safety score
    const getScoreColor = (s: number) => {
        if (s > 80) return "text-green-500"
        if (s > 50) return "text-yellow-500"
        return "text-red-500"
    }

    const getWeatherIcon = (condition: string) => {
        switch (condition?.toLowerCase()) {
            case 'sunny': return <Sun className="w-12 h-12 text-yellow-400" />
            case 'cloudy': return <CloudRain className="w-12 h-12 text-gray-400" />
            case 'stormy': return <CloudLightning className="w-12 h-12 text-purple-500" />
            case 'windy': return <Wind className="w-12 h-12 text-blue-400" />
            default: return <AlertTriangle className="w-12 h-12 text-orange-500" />
        }
    }

    return (
        <div className="bg-card border border-border rounded-xl p-6 shadow-lg">
            <div className="flex justify-between items-start mb-6">
                <div>
                    <h2 className="text-xl font-bold text-foreground">Market Weather</h2>
                    <p className="text-muted-foreground text-sm uppercase tracking-wider">{symbol}</p>
                </div>
                <div className="bg-accent/50 p-2 rounded-lg">
                    {getWeatherIcon(weather?.analysis?.market_condition)}
                </div>
            </div>

            <div className="flex items-center justify-center py-6 relative">
                {/* Gauge Placeholder Visualization */}
                <div className="relative w-40 h-40 flex items-center justify-center rounded-full border-8 border-accent">
                    <div className="flex flex-col items-center">
                        <span className={cn("text-4xl font-bold", getScoreColor(score))}>
                            {score.toFixed(0)}
                        </span>
                        <span className="text-xs text-muted-foreground mt-1">SAFETY SCORE</span>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mt-6">
                <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">REGIME</p>
                    <p className="font-semibold text-foreground">{weather?.analysis?.regime?.replace('_', ' ').toUpperCase()}</p>
                </div>
                <div className="space-y-1 text-right">
                    <p className="text-xs text-muted-foreground">RECOMMENDATION</p>
                    <div className={cn("font-bold px-2 py-1 rounded inline-block text-xs",
                        weather?.recommendation?.action === "BUY" ? "bg-green-500/20 text-green-500" :
                            weather?.recommendation?.action === "SELL" ? "bg-red-500/20 text-red-500" :
                                "bg-yellow-500/20 text-yellow-500"
                    )}>
                        {weather?.recommendation?.action}
                    </div>
                </div>
            </div>
        </div>
    )
}
