'use client'

import { createChart, ColorType, ISeriesApi, CrosshairMode } from 'lightweight-charts';
import React, { useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { AlertCircle } from 'lucide-react';
import { Card } from '@/components/ui/card';

export const AdvancedChart = ({ symbol }: { symbol: string }) => {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

    const { data: ohlcvData } = useQuery({
        queryKey: ['ohlcv', symbol],
        queryFn: async () => {
            // In a real app, this would be a historical data endpoint
            // For now, we mock it or fetch a small subset if available
            // Using regime endpoint as proxy for now until we have dedicated history endpoint
            const res = await axios.get(`/analytics/intraday-regime?symbol=${symbol}`)
            // transform single data point to fake history for visual demo if needed
            // but ideally we need array. 
            // For MVP premium visualisation, let's generate realistic procedural data based on current price
            const currentPrice = res.data?.current_price || 150;
            return generateData(currentPrice);
        }
    });

    const { data: dangerZones } = useQuery({
        queryKey: ['danger-zones', symbol],
        queryFn: async () => {
            const res = await axios.get(`/analytics/options-danger-zones?symbol=${symbol}`)
            return res.data?.danger_zones || []
        }
    });

    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: 'transparent' },
                textColor: '#D9D9D9',
            },
            grid: {
                vertLines: { color: 'rgba(42, 46, 57, 0.5)' },
                horzLines: { color: 'rgba(42, 46, 57, 0.5)' },
            },
            width: chartContainerRef.current.clientWidth,
            height: 400,
            crosshair: {
                mode: CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: 'rgba(197, 203, 206, 0.8)',
            },
            timeScale: {
                borderColor: 'rgba(197, 203, 206, 0.8)',
            },
        });

        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        });

        candlestickSeriesRef.current = candlestickSeries;

        if (ohlcvData) {
            candlestickSeries.setData(ohlcvData);
        }

        // Add Danger Zones as Price Lines
        if (dangerZones && dangerZones.length > 0) {
            dangerZones.forEach((zone: any) => {
                // Create a price line
                candlestickSeries.createPriceLine({
                    price: zone.level,
                    color: '#FF0000', // Red for danger
                    lineWidth: 2,
                    lineStyle: 2, // Dashed
                    axisLabelVisible: true,
                    title: `⛔ DANGER ZONE (${zone.type})`,
                });
            });
        }

        const handleResize = () => {
            if (chartContainerRef.current) {
                chart.applyOptions({ width: chartContainerRef.current.clientWidth });
            }
        };

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
        };
    }, [ohlcvData, dangerZones]);

    return (
        <Card className="p-4 h-[450px] relative overflow-hidden group">
            <div className="absolute top-4 left-4 z-10 flex items-center space-x-2">
                <h3 className="text-lg font-bold text-white tracking-widest">{symbol}USD</h3>
                <span className="text-xs text-muted-foreground bg-accent/20 px-2 py-0.5 rounded">1D</span>
            </div>
            <div ref={chartContainerRef} className="w-full h-full" />
        </Card>
    );
};

// Helper to generate realistic looking chart data
function generateData(startPrice: number) {
    const res = [];
    const time = new Date();
    time.setHours(0, 0, 0, 0); // start of today
    time.setDate(time.getDate() - 100);

    let open = startPrice;

    for (let i = 0; i < 100; i++) {
        time.setDate(time.getDate() + 1);
        const vol = (Math.random() * 0.05) - 0.025; // Random move
        const close = open * (1 + vol);
        const high = Math.max(open, close) * (1 + Math.random() * 0.01);
        const low = Math.min(open, close) * (1 - Math.random() * 0.01);

        res.push({
            time: time.toISOString().split('T')[0],
            open: open,
            high: high,
            low: low,
            close: close,
        });

        open = close;
    }
    return res;
}
