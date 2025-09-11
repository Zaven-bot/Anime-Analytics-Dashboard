import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Skeleton } from './ui/skeleton';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import AnimeAnalyticsAPI from '../lib/api';
import { Palette, BarChart3, PieChart as PieChartIcon, RefreshCw, AlertCircle, Eye, Hash } from 'lucide-react';

const GenreChart = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedType, setSelectedType] = useState('top');
  const [chartType, setChartType] = useState('bar');
  const [viewMode, setViewMode] = useState('anime'); // 'anime' or 'mention'

  const snapshotTypes = [
    { value: 'top', label: 'Top Rated' },
    { value: 'seasonal_current', label: 'Airing' },
    { value: 'upcoming', label: 'Upcoming' },
    { value: 'popular_movies', label: 'Movies' },
  ];

  // Anime-inspired color palette
  const colors = [
    '#ff6b9d', '#c44bd1', '#4da3ff', '#4dd9ff', '#ff8c42', 
    '#ffd93d', '#6bcf7e', '#ff5722', '#9c27b0', '#2196f3',
    '#00bcd4', '#4caf50', '#ff9800', '#795548', '#607d8b'
  ];

  const fetchData = async (type = selectedType) => {
    try {
      setLoading(true);
      setError(null);
      const response = await AnimeAnalyticsAPI.getGenreDistribution(type);
      setData(response);
    } catch (err) {
      setError('Failed to load genre data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedType]);

  const handleTypeChange = (type) => {
    console.log('Changing snapshot type to:', type);
    setSelectedType(type);
  };

  const handleViewModeChange = (mode) => {
    console.log('Changing view mode to:', mode);
    setViewMode(mode);
  };

  const handleChartTypeChange = (type) => {
    console.log('Changing chart type to:', type);
    setChartType(type);
  };

  const getChartData = () => {
    if (!data?.genres) return [];
    
    return data.genres
      .slice(0, 15) // Top 15 genres
      .map((genre, index) => ({
        ...genre,
        value: viewMode === 'anime' ? genre.anime_count : genre.mention_count,
        percentage: viewMode === 'anime' ? genre.anime_percentage : genre.mention_percentage,
        fill: colors[index % colors.length]
      }));
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-800 border border-slate-600 rounded-lg p-3 shadow-lg">
          <p className="text-white font-semibold">{label}</p>
          <p className="text-anime-blue">
            {viewMode === 'anime' ? 'Anime Count' : 'Mentions'}: {data.value}
          </p>
          <p className="text-anime-pink">
            Percentage: {data.percentage.toFixed(1)}%
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
        <Button variant="outline" onClick={() => fetchData()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </div>
    </div>
  );

  return (
    <Card className="card-glow bg-gradient-to-br from-slate-900 to-slate-800 border-slate-700">
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <CardTitle className="gradient-text text-2xl font-bold flex items-center">
              <Palette className="h-6 w-6 mr-2" />
              Genre Distribution
            </CardTitle>
            <CardDescription className="text-slate-400">
              {viewMode === 'anime' ? 'Anime coverage' : 'Genre frequency'} across categories
            </CardDescription>
          </div>
          <div className="flex flex-col sm:flex-row gap-2">
            {/* View Mode Toggle */}
            <div className="flex rounded-lg border border-slate-600 overflow-hidden">
              <Button
                variant={viewMode === 'anime' ? 'anime' : 'ghost'}
                size="sm"
                onClick={() => handleViewModeChange('anime')}
                className="rounded-none"
              >
                <Eye className="h-4 w-4 mr-2" />
                Coverage
              </Button>
              <Button
                variant={viewMode === 'mention' ? 'anime' : 'ghost'}
                size="sm"
                onClick={() => handleViewModeChange('mention')}
                className="rounded-none"
              >
                <Hash className="h-4 w-4 mr-2" />
                Frequency
              </Button>
            </div>
            
            {/* Chart Type Toggle */}
            <div className="flex rounded-lg border border-slate-600 overflow-hidden">
              <Button
                variant={chartType === 'bar' ? 'anime' : 'ghost'}
                size="sm"
                onClick={() => handleChartTypeChange('bar')}
                className="rounded-none"
              >
                <BarChart3 className="h-4 w-4" />
              </Button>
              <Button
                variant={chartType === 'pie' ? 'anime' : 'ghost'}
                size="sm"
                onClick={() => handleChartTypeChange('pie')}
                className="rounded-none"
              >
                <PieChartIcon className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
        
        {/* Snapshot Type Selector */}
        <div className="flex flex-wrap gap-2 mt-4">
          {snapshotTypes.map((type) => (
            <Button
              key={type.value}
              variant={selectedType === type.value ? "anime" : "outline"}
              size="sm"
              onClick={() => handleTypeChange(type.value)}
              className="transition-all duration-300"
            >
              {type.label}
            </Button>
          ))}
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
                <div className="text-anime-blue font-bold text-lg">
                  {data.total_anime?.toLocaleString()}
                </div>
                <div className="text-xs text-slate-400">Total Anime</div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                <div className="text-anime-pink font-bold text-lg">
                  {data.total_genre_mentions?.toLocaleString()}
                </div>
                <div className="text-xs text-slate-400">Genre Mentions</div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                <div className="text-anime-purple font-bold text-lg">
                  {data.genres?.length}
                </div>
                <div className="text-xs text-slate-400">Unique Genres</div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                <div className="text-anime-cyan font-bold text-lg">
                  {data.snapshot_date}
                </div>
                <div className="text-xs text-slate-400">Snapshot Date</div>
              </div>
            </div>

            {/* Chart */}
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                {chartType === 'bar' ? (
                  <BarChart data={getChartData()} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis 
                      dataKey="genre" 
                      stroke="#94a3b8" 
                      tick={{ fontSize: 12 }}
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar 
                      dataKey="value" 
                      fill="#8884d8"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                ) : (
                  <PieChart>
                    <Pie
                      data={getChartData().slice(0, 10)} // Top 10 for pie chart
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      innerRadius={40}
                      dataKey="value"
                      label={({ genre, percentage }) => `${genre} (${percentage.toFixed(1)}%)`}
                      labelLine={false}
                    >
                      {getChartData().slice(0, 10).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                  </PieChart>
                )}
              </ResponsiveContainer>
            </div>

            {/* Legend for top genres */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2 text-xs">
              {getChartData().slice(0, 10).map((genre, index) => (
                <div key={genre.genre} className="flex items-center space-x-2">
                  <div 
                    className="w-3 h-3 rounded"
                    style={{ backgroundColor: genre.fill }}
                  />
                  <span className="text-slate-300 truncate">{genre.genre}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default GenreChart;
