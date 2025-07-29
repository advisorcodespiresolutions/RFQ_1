import React from 'react';
import { useQuery } from 'react-query';
import {
  ChartBarIcon,
  CurrencyDollarIcon,
  ClockIcon,
  CheckCircleIcon,
  ArrowUpIcon,
  ArrowDownIcon,
} from '@heroicons/react/24/outline';

// Components
import KPICard from '../components/Dashboard/KPICard';
import QuotePipelineChart from '../components/Dashboard/QuotePipelineChart';
import RevenueChart from '../components/Dashboard/RevenueChart';
import ActivityFeed from '../components/Dashboard/ActivityFeed';
import AIInsights from '../components/Dashboard/AIInsights';

// Services
import { dashboardApi } from '../services/api';

const Dashboard: React.FC = () => {
  // Fetch dashboard data
  const { data: overview, isLoading } = useQuery(
    'dashboard-overview',
    () => dashboardApi.getOverview(),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  const { data: kpis } = useQuery(
    'dashboard-kpis',
    () => dashboardApi.getKPIs(),
    {
      refetchInterval: 60000, // Refresh every minute
    }
  );

  const { data: pipeline } = useQuery(
    'dashboard-pipeline',
    () => dashboardApi.getPipelineStats()
  );

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const kpiData = kpis || {
    quotes_generated: { current: 127, previous: 113, change_percentage: 12.4, is_positive: true },
    total_revenue: { current: 485230, previous: 447800, change_percentage: 8.2, is_positive: true },
    avg_processing_time: { current: 3.2, previous: 3.8, change_percentage: -15.8, is_positive: true },
    accuracy_rate: { current: 94.8, previous: 92.7, change_percentage: 2.1, is_positive: true },
    conversion_rate: { current: 68.5, previous: 65.2, change_percentage: 5.1, is_positive: true },
    active_quotes: 42,
    pending_quotes: 18,
    avg_quote_value: 3821.5,
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="py-6">
        {/* Header */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="md:flex md:items-center md:justify-between">
            <div className="flex-1 min-w-0">
              <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
                Dashboard
              </h2>
              <p className="mt-1 text-sm text-gray-500">
                Welcome back! Here's what's happening with your RFQ platform.
              </p>
            </div>
            <div className="mt-4 flex md:mt-0 md:ml-4">
              <button
                type="button"
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <ClockIcon className="-ml-1 mr-2 h-5 w-5 text-gray-500" />
                Last 30 days
              </button>
            </div>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            <KPICard
              title="Quotes Generated"
              value={kpiData.quotes_generated.current}
              change={kpiData.quotes_generated.change_percentage}
              isPositive={kpiData.quotes_generated.is_positive}
              icon={ChartBarIcon}
              color="blue"
            />
            <KPICard
              title="Total Revenue"
              value={`$${kpiData.total_revenue.current.toLocaleString()}`}
              change={kpiData.total_revenue.change_percentage}
              isPositive={kpiData.total_revenue.is_positive}
              icon={CurrencyDollarIcon}
              color="green"
            />
            <KPICard
              title="Avg. Processing Time"
              value={`${kpiData.avg_processing_time.current} min`}
              change={kpiData.avg_processing_time.change_percentage}
              isPositive={kpiData.avg_processing_time.is_positive}
              icon={ClockIcon}
              color="yellow"
            />
            <KPICard
              title="Accuracy Rate"
              value={`${kpiData.accuracy_rate.current}%`}
              change={kpiData.accuracy_rate.change_percentage}
              isPositive={kpiData.accuracy_rate.is_positive}
              icon={CheckCircleIcon}
              color="purple"
            />
          </div>
        </div>

        {/* Charts Row */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Quote Pipeline Chart */}
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Quote Pipeline
                  </h3>
                  <span className="text-sm text-gray-500">Current Status</span>
                </div>
                <div className="mt-6">
                  <QuotePipelineChart data={pipeline} />
                </div>
              </div>
            </div>

            {/* Revenue Trend Chart */}
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Revenue Trend
                  </h3>
                  <span className="text-sm text-gray-500">Last 30 days</span>
                </div>
                <div className="mt-6">
                  <RevenueChart />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Row */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            {/* Recent Activity */}
            <div className="lg:col-span-2 bg-white overflow-hidden shadow rounded-lg">
              <div className="p-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-6">
                  Recent Activity
                </h3>
                <ActivityFeed />
              </div>
            </div>

            {/* AI Insights */}
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-6">
                  AI Insights
                </h3>
                <AIInsights />
              </div>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-6">
                Quick Stats
              </h3>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary-600">
                    {kpiData.active_quotes}
                  </div>
                  <div className="text-sm text-gray-500">Active Quotes</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-warning-600">
                    {kpiData.pending_quotes}
                  </div>
                  <div className="text-sm text-gray-500">Pending Review</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-success-600">
                    ${kpiData.avg_quote_value.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-500">Avg Quote Value</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {kpiData.conversion_rate.current}%
                  </div>
                  <div className="text-sm text-gray-500">Conversion Rate</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;