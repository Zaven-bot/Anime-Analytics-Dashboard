import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Skeleton } from './ui/skeleton';
import AnimeAnalyticsAPI from '../lib/api';
import {
  TrendingUp,
  Database,
  Star,
  Calendar,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';

const OverviewCards = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const overview = await AnimeAnalyticsAPI.getOverviewStats();
      setData(overview);
    } catch (err) {
      setError('Failed to load overview data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="card-glow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-4 rounded" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16 mb-2" />
              <Skeleton className="h-3 w-24" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="col-span-full border-destructive bg-destructive/10 error-shake">
          <CardContent className="flex items-center justify-center p-6">
            <div className="flex items-center space-x-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <span>{error}</span>
              <Button
                variant="outline"
                size="sm"
                onClick={fetchData}
                className="ml-4"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const cards = [
    {
      title: 'Total Snapshots',
      value: data.total_snapshots?.toLocaleString() || '0',
      description: 'Anime data points collected',
      icon: Database,
      gradient: 'from-anime-blue to-anime-cyan',
    },
    {
      title: 'Unique Anime',
      value: data.unique_anime?.toLocaleString() || '0',
      description: 'Distinct anime titles tracked',
      icon: Star,
      gradient: 'from-anime-pink to-anime-purple',
    },
    {
      title: 'Data Types',
      value: data.snapshot_types?.length || '0',
      description: 'Different snapshot categories',
      icon: TrendingUp,
      gradient: 'from-anime-purple to-anime-blue',
    },
    {
      title: 'Last Updated',
      value: data.latest_snapshot_date
        ? new Date(data.latest_snapshot_date).toLocaleDateString()
        : 'N/A',
      description: 'Most recent data collection',
      icon: Calendar,
      gradient: 'from-anime-orange to-anime-yellow',
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card, index) => (
        <Card
          key={card.title}
          className={`card-glow bg-gradient-to-br ${card.gradient} text-white border-none transform hover:scale-105 transition-all duration-300`}
          style={{ animationDelay: `${index * 0.1}s` }}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-white/90">
              {card.title}
            </CardTitle>
            <card.icon className="h-4 w-4 text-white/80 animate-float" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white mb-1">
              {card.value}
            </div>
            <p className="text-xs text-white/70">{card.description}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default OverviewCards;
