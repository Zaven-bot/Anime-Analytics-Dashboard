import React from 'react';
import OverviewCards from './components/OverviewCards';
import TopAnimeTable from './components/TopAnimeTable';
import GenreChart from './components/GenreChart';
import TrendsChart from './components/TrendsChart';
import { RefreshCw, Sparkles, Database, BarChart3 } from 'lucide-react';

function App() {
  const refreshPage = () => {
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Animated background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-anime-pink/5 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-3/4 right-1/4 w-96 h-96 bg-anime-blue/5 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-anime-purple/5 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      <div className="relative z-10">
        {/* Header */}
        <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
          <div className="container mx-auto px-4 py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <Sparkles className="h-8 w-8 text-anime-pink animate-pulse" />
                  <div className="absolute inset-0 animate-ping">
                    <Sparkles className="h-8 w-8 text-anime-pink opacity-30" />
                  </div>
                </div>
                <div>
                  <h1 className="text-3xl font-bold gradient-text">
                    Anime Analytics Dashboard
                  </h1>
                  <p className="text-slate-400 text-sm">
                    Real-time insights into the anime universe ✨
                  </p>
                </div>
              </div>
              
              <button
                onClick={refreshPage}
                className="flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-lg transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-anime-pink/20"
              >
                <RefreshCw className="h-4 w-4" />
                <span className="text-sm">Refresh</span>
              </button>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="container mx-auto px-4 py-8 space-y-8">
          {/* Welcome Section */}
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-white mb-2">
              Welcome to the Anime Data Universe! 🌟
            </h2>
            <p className="text-slate-400 max-w-2xl mx-auto">
              Dive into comprehensive analytics covering thousands of anime titles, 
              from top-rated classics to upcoming seasonal gems. All data is cached 
              and optimized for lightning-fast insights.
            </p>
          </div>

          {/* Overview Cards */}
          <section className="space-y-4">
            <div className="flex items-center space-x-2">
              <Database className="h-5 w-5 text-anime-blue" />
              <h3 className="text-xl font-semibold text-white">Database Overview</h3>
            </div>
            <OverviewCards />
          </section>

          {/* Charts Section */}
          <section className="space-y-8">
            <div className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5 text-anime-purple" />
              <h3 className="text-xl font-semibold text-white">Analytics & Trends</h3>
            </div>
            
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
              <GenreChart />
              <TrendsChart />
            </div>
          </section>

          {/* Top Anime Table */}
          <section className="space-y-4">
            <div className="flex items-center space-x-2">
              <Sparkles className="h-5 w-5 text-anime-pink" />
              <h3 className="text-xl font-semibold text-white">Top Anime Rankings</h3>
            </div>
            <TopAnimeTable />
          </section>
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-800 bg-slate-900/50 backdrop-blur-sm mt-16">
          <div className="container mx-auto px-4 py-8">
            <div className="text-center">
              <p className="text-slate-400 text-sm">
                Made for anime lovers • Data powered by MyAnimeList API
              </p>
              <p className="text-slate-500 text-xs mt-2">
                Dashboard features Redis caching, real-time analytics, and responsive design
              </p>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default App;
