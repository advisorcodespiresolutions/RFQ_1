import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Clock, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  TrendingUp,
  Calendar,
  DollarSign,
  Shield
} from 'lucide-react';
import { format, startOfWeek, endOfWeek } from 'date-fns';
import axios from 'axios';
import toast from 'react-hot-toast';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

interface ManagerDashboardProps {
  managerId: number;
}

interface TimeEntry {
  id: number;
  employee_id: number;
  employee_name: string;
  punch_type: string;
  punch_time: string;
  status: string;
  is_within_grace_period: boolean;
}

interface OvertimeAlert {
  employee_id: number;
  employee_name: string;
  date: string;
  hours_worked: number;
  overtime_hours: number;
  overtime_type: string;
}

interface ComplianceViolation {
  id: number;
  employee_id: number;
  employee_name: string;
  violation_type: string;
  description: string;
  severity: string;
  audit_date: string;
  resolved: boolean;
}

const ManagerDashboard: React.FC<ManagerDashboardProps> = ({ managerId }) => {
  const [pendingApprovals, setPendingApprovals] = useState<TimeEntry[]>([]);
  const [overtimeAlerts, setOvertimeAlerts] = useState<OvertimeAlert[]>([]);
  const [complianceViolations, setComplianceViolations] = useState<ComplianceViolation[]>([]);
  const [weeklyStats, setWeeklyStats] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState('overview');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      const weekStart = startOfWeek(new Date());
      const weekEnd = endOfWeek(new Date());

      // Load pending approvals
      const approvalsResponse = await axios.get(`/api/time-attendance/time-entries/pending`);
      setPendingApprovals(approvalsResponse.data);

      // Load weekly summary
      const weeklyResponse = await axios.get(`/api/time-attendance/reports/weekly-summary?week_start=${format(weekStart, 'yyyy-MM-dd')}`);
      setWeeklyStats(weeklyResponse.data);

      // Load compliance violations
      const violationsResponse = await axios.get(`/api/time-attendance/compliance/violations`);
      setComplianceViolations(violationsResponse.data);

    } catch (error) {
      console.error('Error loading dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async (timeEntryId: number) => {
    try {
      await axios.post(`/api/time-attendance/approve/${timeEntryId}`);
      toast.success('Time entry approved');
      loadDashboardData();
    } catch (error) {
      toast.error('Failed to approve time entry');
    }
  };

  const handleReject = async (timeEntryId: number, reason: string) => {
    try {
      await axios.post(`/api/time-attendance/reject/${timeEntryId}`, { reason });
      toast.success('Time entry rejected');
      loadDashboardData();
    } catch (error) {
      toast.error('Failed to reject time entry');
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'rejected': return <XCircle className="w-4 h-4 text-red-500" />;
      case 'pending': return <Clock className="w-4 h-4 text-yellow-500" />;
      default: return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const chartData = weeklyStats ? [
    { name: 'Regular Hours', value: weeklyStats.total_regular_hours, color: '#3B82F6' },
    { name: 'Overtime Hours', value: weeklyStats.total_overtime_hours, color: '#EF4444' },
    { name: 'Holiday Hours', value: weeklyStats.total_holiday_hours, color: '#10B981' },
  ] : [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Manager Dashboard</h1>
        <p className="text-gray-600">Monitor time tracking, overtime, and compliance for your team</p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Users className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Team Members</p>
              <p className="text-2xl font-bold text-gray-900">{weeklyStats?.total_employees || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <Clock className="w-6 h-6 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Pending Approvals</p>
              <p className="text-2xl font-bold text-gray-900">{pendingApprovals.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 rounded-lg">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Overtime Alerts</p>
              <p className="text-2xl font-bold text-gray-900">{overtimeAlerts.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <Shield className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Compliance Score</p>
              <p className="text-2xl font-bold text-gray-900">98%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {[
              { id: 'overview', name: 'Overview', icon: TrendingUp },
              { id: 'approvals', name: 'Approvals', icon: CheckCircle },
              { id: 'overtime', name: 'Overtime', icon: Clock },
              { id: 'compliance', name: 'Compliance', icon: Shield },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setSelectedTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                  selectedTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                <span>{tab.name}</span>
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {/* Overview Tab */}
          {selectedTab === 'overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Hours Distribution Chart */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Weekly Hours Distribution</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={chartData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {chartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                {/* Recent Activity */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
                  <div className="space-y-3">
                    {pendingApprovals.slice(0, 5).map((entry) => (
                      <div key={entry.id} className="flex items-center justify-between p-3 bg-white rounded-lg">
                        <div>
                          <p className="text-sm font-medium text-gray-900">{entry.employee_name}</p>
                          <p className="text-xs text-gray-500">
                            {format(new Date(entry.punch_time), 'MMM dd, HH:mm')}
                          </p>
                        </div>
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(entry.status)}
                          <span className="text-xs text-gray-500 capitalize">
                            {entry.punch_type.replace('_', ' ')}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Approvals Tab */}
          {selectedTab === 'approvals' && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Pending Time Entry Approvals</h3>
              {pendingApprovals.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No pending approvals</p>
              ) : (
                <div className="space-y-3">
                  {pendingApprovals.map((entry) => (
                    <div key={entry.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-gray-900">{entry.employee_name}</p>
                          <p className="text-sm text-gray-500">
                            {format(new Date(entry.punch_time), 'MMM dd, yyyy HH:mm:ss')}
                          </p>
                          <p className="text-sm text-gray-500 capitalize">
                            {entry.punch_type.replace('_', ' ')}
                          </p>
                          {!entry.is_within_grace_period && (
                            <p className="text-sm text-yellow-600">Outside grace period</p>
                          )}
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleApprove(entry.id)}
                            className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => handleReject(entry.id, 'Manager rejection')}
                            className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
                          >
                            Reject
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Overtime Tab */}
          {selectedTab === 'overtime' && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Overtime Alerts</h3>
              {overtimeAlerts.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No overtime alerts</p>
              ) : (
                <div className="space-y-3">
                  {overtimeAlerts.map((alert, index) => (
                    <div key={index} className="border border-red-200 rounded-lg p-4 bg-red-50">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-gray-900">{alert.employee_name}</p>
                          <p className="text-sm text-gray-500">
                            {format(new Date(alert.date), 'MMM dd, yyyy')}
                          </p>
                          <p className="text-sm text-red-600">
                            {alert.hours_worked} hours worked, {alert.overtime_hours} overtime hours
                          </p>
                          <p className="text-xs text-gray-500 capitalize">
                            {alert.overtime_type.replace('_', ' ')}
                          </p>
                        </div>
                        <AlertTriangle className="w-6 h-6 text-red-500" />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Compliance Tab */}
          {selectedTab === 'compliance' && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Compliance Violations</h3>
              {complianceViolations.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No compliance violations</p>
              ) : (
                <div className="space-y-3">
                  {complianceViolations.map((violation) => (
                    <div key={violation.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-gray-900">{violation.employee_name}</p>
                          <p className="text-sm text-gray-500">
                            {format(new Date(violation.audit_date), 'MMM dd, yyyy')}
                          </p>
                          <p className="text-sm text-gray-700">{violation.description}</p>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(violation.severity)}`}>
                            {violation.severity}
                          </span>
                        </div>
                        <div className="flex items-center space-x-2">
                          {violation.resolved ? (
                            <CheckCircle className="w-5 h-5 text-green-500" />
                          ) : (
                            <AlertTriangle className="w-5 h-5 text-yellow-500" />
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ManagerDashboard;