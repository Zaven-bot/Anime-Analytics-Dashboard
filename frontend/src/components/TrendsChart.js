import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Skeleton } from './ui/skeleton';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import AnimeAnalyticsAPI from '../lib/api';
import { TrendingUp, Calendar, RefreshCw, AlertCircle, Activity, BarChart3 } from 'lucide-react';

const TrendsChart = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [chartType, setChartType] = useState('line');
  const [metric, setMetric] = useState('score');

  const metrics = [
    { value: 'score', label: 'Average Score', key: 'avg_score', color: '#ff6b9d' },
    { value: 'popularity', label: 'Popularity', key: 'avg_popularity', color: '#4da3ff' },
    { value: 'members', label: 'Members', key: 'avg_members', color: '#6bcf7e' },
    { value: 'count', label: 'Anime Count', key: 'anime_count', color: '#ffd93d' }
  ];

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch data for all snapshot types using the correct API method
      const [topData, currentData, upcomingData, moviesData] = await Promise.all([
        AnimeAnalyticsAPI.getOverviewStats('top'),
        AnimeAnalyticsAPI.getOverviewStats('seasonal_current'),
        AnimeAnalyticsAPI.getOverviewStats('upcoming'),
        AnimeAnalyticsAPI.getOverviewStats('popular_movies')
      ]);

      // Combine data for trends
      const trendData = [
        {
          category: 'Top Rated',
          anime_count: topData.total_anime || 0,
          avg_score: topData.average_score || 0,
          avg_popularity: topData.average_popularity || 0,
          avg_members: topData.average_members || 0,
          snapshot_date: topData.snapshot_date || 'N/A'
        },
        {
          category: 'Airing',
          anime_count: currentData.total_anime || 0,
          avg_score: currentData.average_score || 0,
          avg_popularity: currentData.average_popularity || 0,
          avg_members: currentData.average_members || 0,
          snapshot_date: currentData.snapshot_date || 'N/A'
        },
        {
          category: 'Upcoming',
          anime_count: upcomingData.total_anime || 0,
          avg_score: upcomingData.average_score || 0,
          avg_popularity: upcomingData.average_popularity || 0,
          avg_members: upcomingData.average_members || 0,
          snapshot_date: upcomingData.snapshot_date || 'N/A'
        },
        {
          category: 'Movies',
          anime_count: moviesData.total_anime || 0,
          avg_score: moviesData.average_score || 0,
          avg_popularity: moviesData.average_popularity || 0,
          avg_members: moviesData.average_members || 0,
          snapshot_date: moviesData.snapshot_date || 'N/A'
        }
      ];

      setData(trendData);
    } catch (err) {
      setError('Failed to load trends data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleMetricChange = (newMetric) => {
    console.log('Changing metric to:', newMetric);
    setMetric(newMetric);
  };

  const handleChartTypeChange = (newChartType) => {
    console.log('Changing chart type to:', newChartType);
    setChartType(newChartType);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const currentMetric = metrics.find(m => m.value === metric);

  const formatValue = (value, metricType) => {
    if (metricType === 'score') {
      return value.toFixed(2);
    } else if (metricType === 'members' || metricType === 'popularity') {
      return value >= 1000000 ? `${(value / 1000000).toFixed(1)}M` : 
             value >= 1000 ? `${(value / 1000).toFixed(1)}K` : 
             value.toFixed(0);
    } else {
      return value.toLocaleString();
    }
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-800 border border-slate-600 rounded-lg p-3 shadow-lg">
          <p className="text-white font-semibold mb-2">{label}</p>
          <p className="text-anime-blue text-sm">
            Snapshot: {data.snapshot_date}
          </p>
          <p className="text-anime-pink">
            {currentMetric.label}: {formatValue(payload[0].value, metric)}
          </p>
          <p className="text-anime-cyan text-sm">
            Total Anime: {data.anime_count.toLocaleString()}
          </p>
        </div>
      );
    }
    return null;
  };

  const LoadingSkeleton = () => (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-8 w-24" />
      </div>
      <Skeleton className="h-80 w-full" />
    </div>
  );

  const ErrorState = () => (
    <div className="flex items-center justify-center p-8 text-destructive error-shake">
      <div className="text-center">
        <AlertCircle className="h-12 w-12 mx-auto mb-4" />
        <p className="mb-4">{error}</p>
        <Button variant="outline" onClick={fetchData}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </div>
    </div>
  );

  const getHighestValue = () => {
    if (!data) return null;
    const values = data.map(d => d[currentMetric.key]);
    const maxValue = Math.max(...values);
    const maxItem = data.find(d => d[currentMetric.key] === maxValue);
    return { value: maxValue, category: maxItem.category };
  };

  const getLowestValue = () => {
    if (!data) return null;
    const values = data.map(d => d[currentMetric.key]);
    const minValue = Math.min(...values);
    const minItem = data.find(d => d[currentMetric.key] === minValue);
    return { value: minValue, category: minItem.category };
  };

  return (
    <Card className="card-glow bg-gradient-to-br from-slate-900 to-slate-800 border-slate-700">
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <CardTitle className="gradient-text text-2xl font-bold flex items-center">
              <TrendingUp className="h-6 w-6 mr-2" />
              Category Comparison
            </CardTitle>
            <CardDescription className="text-slate-400">
              Compare metrics across different anime categories
            </CardDescription>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-2">
            {/* Metric Selector */}
            <div className="flex flex-wrap gap-1">
              {metrics.map((m) => (
                <Button
                  key={m.value}
                  variant={metric === m.value ? "anime" : "outline"}
                  size="sm"
                  onClick={() => handleMetricChange(m.value)}
                  className="transition-all duration-300"
                >
                  {m.label}
                </Button>
              ))}
            </div>
            
            {/* Chart Type Toggle */}
            <div className="flex rounded-lg border border-slate-600 overflow-hidden">
              <Button
                variant={chartType === 'line' ? 'anime' : 'ghost'}
                size="sm"
                onClick={() => handleChartTypeChange('line')}
                className="rounded-none"
              >
                <Activity className="h-4 w-4" />
              </Button>
              <Button
                variant={chartType === 'area' ? 'anime' : 'ghost'}
                size="sm"
                onClick={() => handleChartTypeChange('area')}
                className="rounded-none"
              >
                <BarChart3 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        {loading && <LoadingSkeleton />}
        {error && !loading && <ErrorState />}
        {data && !loading && !error && (
          <div className="space-y-4">
            {/* Stats Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                <div className="text-anime-pink font-bold text-lg">
                  {getHighestValue()?.category || 'N/A'}
                </div>
                <div className="text-xs text-slate-400">Highest {currentMetric.label}</div>
                <div className="text-xs text-anime-pink">
                  {getHighestValue() && formatValue(getHighestValue().value, metric)}
                </div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                <div className="text-anime-blue font-bold text-lg">
                  {getLowestValue()?.category || 'N/A'}
                </div>
                <div className="text-xs text-slate-400">Lowest {currentMetric.label}</div>
                <div className="text-xs text-anime-blue">
                  {getLowestValue() && formatValue(getLowestValue().value, metric)}
                </div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                <div className="text-anime-purple font-bold text-lg">
                  {data.reduce((sum, item) => sum + item.anime_count, 0).toLocaleString()}
                </div>
                <div className="text-xs text-slate-400">Total Anime</div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                <div className="text-anime-cyan font-bold text-lg">
                  4
                </div>
                <div className="text-xs text-slate-400">Categories</div>
              </div>
            </div>

            {/* Chart */}
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                {chartType === 'line' ? (
                  <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis 
                      dataKey="category" 
                      stroke="#94a3b8" 
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis 
                      stroke="#94a3b8" 
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) => formatValue(value, metric)}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Line 
                      type="monotone" 
                      dataKey={currentMetric.key}
                      stroke={currentMetric.color}
                      strokeWidth={3}
                      dot={{ fill: currentMetric.color, strokeWidth: 2, r: 6 }}
                      activeDot={{ r: 8, fill: currentMetric.color }}
                    />
                  </LineChart>
                ) : (
                  <AreaChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis 
                      dataKey="category" 
                      stroke="#94a3b8" 
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis 
                      stroke="#94a3b8" 
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) => formatValue(value, metric)}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Area 
                      type="monotone" 
                      dataKey={currentMetric.key}
                      stroke={currentMetric.color}
                      strokeWidth={2}
                      fill={currentMetric.color}
                      fillOpacity={0.3}
                    />
                  </AreaChart>
                )}
              </ResponsiveContainer>
            </div>

            {/* Category Legend */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {data.map((item, index) => (
                <div key={item.category} className="bg-slate-800/30 rounded-lg p-3 text-center">
                  <div className="font-semibold text-white text-sm mb-1">
                    {item.category}
                  </div>
                  <div className="text-xs text-slate-400 mb-1">
                    {item.anime_count.toLocaleString()} anime
                  </div>
                  <div 
                    className="text-sm font-bold"
                    style={{ color: currentMetric.color }}
                  >
                    {formatValue(item[currentMetric.key], metric)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default TrendsChart;
