import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from './ui/card';
import { Button } from './ui/button';
import { Skeleton } from './ui/skeleton';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  ComposedChart,
  Bar,
} from 'recharts';
import AnimeAnalyticsAPI from '../lib/api';
import {
  TrendingUp,
  Calendar,
  RefreshCw,
  AlertCircle,
  Activity,
  BarChart3,
  Users,
  Star,
  Heart,
  Eye,
  Hash,
} from 'lucide-react';

const TrendsChart = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [chartType, setChartType] = useState('line');
  const [metric, setMetric] = useState('avg_score');
  const [timeRange, setTimeRange] = useState('all');

  const metrics = [
    {
      value: 'avg_score',
      label: 'Quality Score',
      key: 'avg_score',
      color: '#ff6b9d',
      icon: Star,
      format: (v) => v?.toFixed(2) || 'N/A',
      description: 'Average anime rating (1-10)',
    },
    {
      value: 'anime_count',
      label: 'Release Volume',
      key: 'anime_count',
      color: '#4da3ff',
      icon: BarChart3,
      format: (v) => v?.toLocaleString() || '0',
      description: 'Number of anime released',
    },
    {
      value: 'avg_members',
      label: 'Audience Size',
      key: 'avg_members',
      color: '#6bcf7e',
      icon: Users,
      format: (v) => (v ? `${(v / 1000).toFixed(0)}K` : 'N/A'),
      description: 'Average members per anime',
    },
    {
      value: 'avg_popularity',
      label: 'Visibility Rank',
      key: 'avg_popularity',
      color: '#ffd93d',
      icon: Eye,
      format: (v) => (v ? `#${Math.round(v).toLocaleString()}` : 'N/A'),
      description: 'Average popularity ranking (lower is better)',
      invert: true,
    },
    {
      value: 'total_favorites',
      label: 'Total Love',
      key: 'total_favorites',
      color: '#c44bd1',
      icon: Heart,
      format: (v) => (v ? `${(v / 1000).toFixed(0)}K` : '0'),
      description: 'Total favorites across all anime',
    },
  ];

  const timeRanges = [
    { value: 'all', label: 'All Time' },
    { value: '1', label: 'Last Year' },
    { value: '2', label: 'Last 2 Years' },
    { value: '3', label: 'Last 3 Years' },
    { value: '5', label: 'Last 5 Years' },
    { value: 'current', label: 'Current Year' },
  ];

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await AnimeAnalyticsAPI.getSeasonalTrends();

      // Process and sort the data
      const processedData = response.trends
        .map((trend) => ({
          ...trend,
          // Create a readable season-year label
          period: `${trend.season.charAt(0).toUpperCase() + trend.season.slice(1)} ${trend.year}`,
          // Create a sortable key
          sortKey: trend.year * 10 + getSeasonOrder(trend.season),
          // Handle null values for display
          displayValues: {
            avg_score: trend.avg_score || null,
            anime_count: trend.anime_count,
            avg_members: trend.avg_members || null,
            avg_popularity: trend.avg_popularity || null,
            total_favorites: trend.total_favorites || 0,
          },
        }))
        .sort((a, b) => a.sortKey - b.sortKey);

      setData(processedData);
    } catch (err) {
      setError('Failed to load seasonal trends');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  const getSeasonOrder = (season) => {
    const order = { winter: 1, spring: 2, summer: 3, fall: 4 };
    return order[season] || 0;
  };

  const getFilteredData = () => {
    if (!data) return [];

    const now = new Date();
    const currentYear = now.getFullYear();

    switch (timeRange) {
      case 'current':
        return data.filter((d) => d.year === currentYear);
      case 'all':
        return data;
      default: {
        // Handle numeric year ranges (1, 2, 3, 5)
        const yearsBack = parseInt(timeRange);
        if (!isNaN(yearsBack)) {
          return data.filter((d) => d.year >= currentYear - yearsBack + 1);
        }
        return data;
      }
    }
  };

  const currentMetric = metrics.find((m) => m.value === metric);
  const IconComponent = currentMetric?.icon || TrendingUp;

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleMetricChange = (newMetric) => {
    console.log('Changing metric to:', newMetric);
    setMetric(newMetric);
  };

  const handleChartTypeChange = (newChartType) => {
    console.log('Changing chart type to:', newChartType);
    setChartType(newChartType);
  };

  const handleTimeRangeChange = (newRange) => {
    console.log('Changing time range to:', newRange);
    setTimeRange(newRange);
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const value = payload[0].value;

      return (
        <div className="bg-slate-800 border border-slate-600 rounded-lg p-4 shadow-lg">
          <p className="text-white font-semibold mb-2">{label}</p>
          <div className="space-y-1">
            <p className="text-anime-pink">
              <IconComponent className="h-4 w-4 inline mr-2" />
              {currentMetric.label}: {currentMetric.format(value)}
            </p>
            <p className="text-anime-blue text-sm">
              {data.anime_count} anime released
            </p>
            <p className="text-anime-cyan text-sm">
              Updated: {data.latest_snapshot_date}
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  const LoadingSkeleton = () => (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <Skeleton className="h-8 w-40" />
        <div className="flex gap-2">
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-8 w-20" />
        </div>
      </div>
      <Skeleton className="h-80 w-full" />
      <div className="grid grid-cols-3 gap-4">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-20" />
        ))}
      </div>
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

  const filteredData = getFilteredData();
  const hasValidData = filteredData.some(
    (d) =>
      d.displayValues[metric] !== null && d.displayValues[metric] !== undefined
  );

  const renderChart = () => {
    if (!hasValidData) {
      return (
        <div className="flex items-center justify-center h-80 text-slate-400">
          <div className="text-center">
            <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No data available for {currentMetric.label}</p>
            <p className="text-sm">Try a different metric or time range</p>
          </div>
        </div>
      );
    }

    const chartData = filteredData
      .map((d) => ({
        ...d,
        value: d.displayValues[metric],
      }))
      .filter((d) => d.value !== null && d.value !== undefined);

    const chartProps = {
      data: chartData,
      margin: { top: 20, right: 30, left: 20, bottom: 60 },
    };

    switch (chartType) {
      case 'area':
        return (
          <AreaChart {...chartProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="period"
              stroke="#94a3b8"
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
            />
            <YAxis
              stroke="#94a3b8"
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => currentMetric.format(value)}
              scale={currentMetric.invert ? 'log' : 'auto'}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="value"
              stroke={currentMetric.color}
              strokeWidth={2}
              fill={currentMetric.color}
              fillOpacity={0.3}
            />
          </AreaChart>
        );
      case 'scatter':
        return (
          <ComposedChart {...chartProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="period"
              stroke="#94a3b8"
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
            />
            <YAxis
              yAxisId="left"
              stroke="#94a3b8"
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => currentMetric.format(value)}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              stroke="#4da3ff"
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `${value} anime`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar
              dataKey="anime_count"
              fill="#4da3ff"
              opacity={0.3}
              yAxisId="right"
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={currentMetric.color}
              strokeWidth={3}
              dot={{ fill: currentMetric.color, strokeWidth: 2, r: 6 }}
              yAxisId="left"
            />
          </ComposedChart>
        );
      default: // line
        return (
          <LineChart {...chartProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="period"
              stroke="#94a3b8"
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
            />
            <YAxis
              stroke="#94a3b8"
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => currentMetric.format(value)}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="value"
              stroke={currentMetric.color}
              strokeWidth={3}
              dot={{ fill: currentMetric.color, strokeWidth: 2, r: 6 }}
              activeDot={{ r: 8, fill: currentMetric.color }}
            />
          </LineChart>
        );
    }
  };

  return (
    <Card className="card-glow bg-gradient-to-br from-slate-900 to-slate-800 border-slate-700">
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div>
            <CardTitle className="gradient-text text-2xl font-bold flex items-center">
              <TrendingUp className="h-6 w-6 mr-2" />
              Seasonal Trends
            </CardTitle>
            <CardDescription className="text-slate-400">
              {currentMetric.description} • {filteredData.length} periods
            </CardDescription>
          </div>

          <div className="flex flex-col gap-3">
            {/* Time Range Selector */}
            <div className="flex flex-wrap gap-1">
              {timeRanges.map((range) => (
                <Button
                  key={range.value}
                  variant={timeRange === range.value ? 'anime' : 'outline'}
                  size="sm"
                  onClick={() => handleTimeRangeChange(range.value)}
                  className="transition-all duration-300"
                >
                  <Calendar className="h-4 w-4 mr-1" />
                  {range.label}
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
                title="Line Chart"
              >
                <Activity className="h-4 w-4" />
              </Button>
              <Button
                variant={chartType === 'area' ? 'anime' : 'ghost'}
                size="sm"
                onClick={() => handleChartTypeChange('area')}
                className="rounded-none"
                title="Area Chart"
              >
                <BarChart3 className="h-4 w-4" />
              </Button>
              <Button
                variant={chartType === 'scatter' ? 'anime' : 'ghost'}
                size="sm"
                onClick={() => handleChartTypeChange('scatter')}
                className="rounded-none"
                title="Combined Chart"
              >
                <Hash className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Metric Selector */}
        <div className="flex flex-wrap gap-2 mt-4">
          {metrics.map((m) => {
            const MetricIcon = m.icon;
            return (
              <Button
                key={m.value}
                variant={metric === m.value ? 'anime' : 'outline'}
                size="sm"
                onClick={() => handleMetricChange(m.value)}
                className="transition-all duration-300 flex items-center"
              >
                <MetricIcon className="h-4 w-4 mr-2" />
                {m.label}
              </Button>
            );
          })}
        </div>
      </CardHeader>

      <CardContent>
        {loading && <LoadingSkeleton />}
        {error && !loading && <ErrorState />}
        {data && !loading && !error && (
          <div className="space-y-6">
            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {data.length > 0 && (
                <>
                  <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                    <div className="text-anime-pink font-bold text-lg">
                      {data
                        .reduce((sum, item) => sum + item.anime_count, 0)
                        .toLocaleString()}
                    </div>
                    <div className="text-xs text-slate-400">Total Anime</div>
                  </div>
                  <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                    <div className="text-anime-blue font-bold text-lg">
                      {filteredData.length}
                    </div>
                    <div className="text-xs text-slate-400">Time Periods</div>
                  </div>
                  <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                    <div className="text-anime-purple font-bold text-lg">
                      {Math.max(...data.map((d) => d.year)) -
                        Math.min(...data.map((d) => d.year)) +
                        1}
                    </div>
                    <div className="text-xs text-slate-400">Years Covered</div>
                  </div>
                  <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                    <div className="text-anime-cyan font-bold text-lg">
                      {hasValidData ? '✓' : '⚠'}
                    </div>
                    <div className="text-xs text-slate-400">Data Quality</div>
                  </div>
                </>
              )}
            </div>

            {/* Chart */}
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                {renderChart()}
              </ResponsiveContainer>
            </div>

            {/* Data Quality Notice */}
            {filteredData.length > 0 && (
              <div className="text-xs text-slate-500 bg-slate-800/30 rounded p-3">
                <p>
                  <strong>Note:</strong> Future seasons may show limited data
                  (scores, rankings) as anime haven&apos;t been released yet.
                  Member counts and favorites reflect anticipation levels.
                </p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default TrendsChart;
