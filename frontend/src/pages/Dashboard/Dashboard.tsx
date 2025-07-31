import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../../contexts/AuthContext';
import { UserRole } from '../../types/auth';
import { analyticsAPI, vendorsAPI } from '../../services/api';
import {
  UsersIcon,
  ChatBubbleLeftRightIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

const Dashboard: React.FC = () => {
  const { user } = useAuth();

  // Fetch dashboard data based on user role
  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ['dashboard-overview'],
    queryFn: analyticsAPI.getDashboardOverview,
    enabled: user?.role !== UserRole.VENDOR,
  });

  const { data: vendorData, isLoading: vendorLoading } = useQuery({
    queryKey: ['vendor-profile-status'],
    queryFn: vendorsAPI.getProfileCompletionStatus,
    enabled: user?.role === UserRole.VENDOR,
  });

  if (isLoading || vendorLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const renderAdminDashboard = () => (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard Overview</h1>
        <p className="text-gray-600">Welcome back, {user?.first_name}!</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <UsersIcon className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Partners
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {dashboardData?.partner_tiers?.reduce((sum: number, tier: any) => sum + tier.count, 0) || 0}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ChatBubbleLeftRightIcon className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Recent Feedback
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {dashboardData?.recent_activity?.feedback_submitted || 0}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CheckCircleIcon className="h-6 w-6 text-green-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Complete Profiles
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {dashboardData?.profile_completion?.complete || 0}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ClockIcon className="h-6 w-6 text-yellow-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Avg Rating
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {dashboardData?.average_ratings?.overall || 0}/10
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Partner Tiers */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Partners by Tier
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {dashboardData?.partner_tiers?.map((tier: any) => (
              <div key={tier.tier} className="text-center">
                <div className="text-2xl font-bold text-blue-600">{tier.count}</div>
                <div className="text-sm text-gray-500 capitalize">
                  {tier.tier.replace('_', ' ')}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Recent Activity
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Profile updates (30 days)</span>
              <span className="text-sm font-medium text-gray-900">
                {dashboardData?.recent_activity?.profiles_updated || 0}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Feedback submitted (30 days)</span>
              <span className="text-sm font-medium text-gray-900">
                {dashboardData?.recent_activity?.feedback_submitted || 0}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderVendorDashboard = () => (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Vendor Dashboard</h1>
        <p className="text-gray-600">Welcome back, {user?.first_name}!</p>
      </div>

      {/* Profile Completion Status */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Profile Completion Status
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Completion Rate</span>
              <span className="text-sm font-medium text-gray-900">
                {vendorData?.completion_percentage || 0}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${vendorData?.completion_percentage || 0}%` }}
              ></div>
            </div>
            {vendorData?.missing_fields && vendorData.missing_fields.length > 0 && (
              <div className="mt-4">
                <p className="text-sm text-gray-600 mb-2">Missing fields:</p>
                <ul className="text-sm text-red-600">
                  {vendorData.missing_fields.map((field: string) => (
                    <li key={field} className="capitalize">• {field.replace('_', ' ')}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white shadow rounded-lg">
          <div className="p-6">
            <div className="flex items-center">
              <DocumentTextIcon className="h-8 w-8 text-blue-500" />
              <div className="ml-4">
                <h3 className="text-lg font-medium text-gray-900">Update Profile</h3>
                <p className="text-sm text-gray-500">Keep your information current</p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg">
          <div className="p-6">
            <div className="flex items-center">
              <DocumentTextIcon className="h-8 w-8 text-green-500" />
              <div className="ml-4">
                <h3 className="text-lg font-medium text-gray-900">Upload Documents</h3>
                <p className="text-sm text-gray-500">Add case studies and certifications</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div>
      {user?.role === UserRole.VENDOR ? renderVendorDashboard() : renderAdminDashboard()}
    </div>
  );
};

export default Dashboard;