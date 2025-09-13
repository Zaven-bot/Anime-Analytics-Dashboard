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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from './ui/table';
import AnimeAnalyticsAPI from '../lib/api';
import { Star, Trophy, TrendingUp, RefreshCw, AlertCircle } from 'lucide-react';

const TopAnimeTable = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedType, setSelectedType] = useState('top');

  const snapshotTypes = [
    { value: 'top', label: 'Top Rated', icon: Trophy },
    { value: 'seasonal_current', label: 'Currently Airing', icon: TrendingUp },
    { value: 'upcoming', label: 'Upcoming', icon: Star },
    { value: 'popular_movies', label: 'Popular Movies', icon: Star },
  ];

  const fetchData = useCallback(
    async (type = selectedType) => {
      try {
        setLoading(true);
        setError(null);
        const response = await AnimeAnalyticsAPI.getTopRatedAnime(15, type);
        setData(response);
      } catch (err) {
        setError('Failed to load anime data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    },
    [selectedType]
  );

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleTypeChange = (type) => {
    console.log('Changing anime type to:', type);
    setSelectedType(type);
  };

  const LoadingSkeleton = () => (
    <div className="space-y-2">
      {[...Array(10)].map((_, i) => (
        <div key={i} className="flex items-center space-x-4">
          <Skeleton className="h-4 w-8" />
          <Skeleton className="h-4 flex-1" />
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 w-20" />
        </div>
      ))}
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

  const getRankDisplay = (rank, index) => {
    if (rank) return `#${rank}`;
    return `#${index + 1}`;
  };

  const getScoreColor = (score) => {
    if (!score) return 'text-muted-foreground';
    if (score >= 9) return 'text-green-500 font-bold';
    if (score >= 8) return 'text-blue-500 font-semibold';
    if (score >= 7) return 'text-yellow-500';
    return 'text-gray-500';
  };

  return (
    <Card className="card-glow bg-gradient-to-br from-slate-900 to-slate-800 border-slate-700">
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <CardTitle className="gradient-text text-2xl font-bold">
              Top Anime Rankings
            </CardTitle>
            <CardDescription className="text-slate-400">
              Highest rated anime by category
            </CardDescription>
          </div>
          <div className="flex flex-wrap gap-2">
            {snapshotTypes.map((type) => {
              const Icon = type.icon;
              return (
                <Button
                  key={type.value}
                  variant={selectedType === type.value ? 'anime' : 'outline'}
                  size="sm"
                  onClick={() => handleTypeChange(type.value)}
                  className={`transition-all duration-300 ${
                    selectedType === type.value
                      ? 'scale-105 shadow-lg'
                      : 'hover:scale-105'
                  }`}
                >
                  <Icon className="h-4 w-4 mr-2" />
                  {type.label}
                </Button>
              );
            })}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {loading && <LoadingSkeleton />}
        {error && !loading && <ErrorState />}
        {data && !loading && !error && (
          <div className="rounded-lg border border-slate-700 overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-800/50 hover:bg-slate-800/50">
                  <TableHead className="text-slate-300 font-semibold w-16">
                    Rank
                  </TableHead>
                  <TableHead className="text-slate-300 font-semibold">
                    Title
                  </TableHead>
                  <TableHead className="text-slate-300 font-semibold w-20 text-center">
                    Score
                  </TableHead>
                  <TableHead className="text-slate-300 font-semibold w-32">
                    Genres
                  </TableHead>
                  <TableHead className="text-slate-300 font-semibold w-32">
                    Studios
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.data && data.data.length > 0 ? (
                  data.data.map((anime, index) => (
                    <TableRow
                      key={anime.mal_id}
                      className="hover:bg-slate-800/30 transition-colors duration-200 group"
                    >
                      <TableCell className="font-medium">
                        <div className="flex items-center">
                          {index < 3 && (
                            <Trophy
                              className={`h-4 w-4 mr-2 ${
                                index === 0
                                  ? 'text-yellow-500'
                                  : index === 1
                                    ? 'text-gray-400'
                                    : 'text-amber-600'
                              }`}
                            />
                          )}
                          <span className={index < 3 ? 'font-bold' : ''}>
                            {getRankDisplay(anime.rank, index)}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="group-hover:text-anime-blue transition-colors duration-200 font-medium">
                          {anime.title}
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        {anime.score ? (
                          <div className="flex items-center justify-center">
                            <Star className="h-3 w-3 mr-1 text-yellow-500" />
                            <span className={getScoreColor(anime.score)}>
                              {anime.score.toFixed(1)}
                            </span>
                          </div>
                        ) : (
                          <span className="text-muted-foreground">N/A</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1 max-w-32">
                          {anime.genres?.slice(0, 2).map((genre, idx) => (
                            <span
                              key={idx}
                              className="text-xs bg-anime-purple/20 text-anime-purple px-2 py-1 rounded-full"
                            >
                              {genre}
                            </span>
                          ))}
                          {anime.genres?.length > 2 && (
                            <span className="text-xs text-muted-foreground">
                              +{anime.genres.length - 2}
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm text-slate-400 truncate max-w-32">
                          {anime.studios?.slice(0, 1).join(', ') || 'Unknown'}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell
                      colSpan={5}
                      className="text-center py-8 text-muted-foreground"
                    >
                      No anime data available for this category
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        )}
        {data && data.total_results > 0 && (
          <div className="mt-4 text-sm text-slate-400 text-center">
            Showing {data.data?.length || 0} of {data.total_results} anime
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default TopAnimeTable;
