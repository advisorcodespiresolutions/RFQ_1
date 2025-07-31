import React, { useState, useEffect } from 'react';
import { Clock, MapPin, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { format } from 'date-fns';
import axios from 'axios';
import toast from 'react-hot-toast';

interface TimeClockProps {
  employeeId: number;
  employeeName: string;
  locationName: string;
}

interface PunchData {
  employee_id: number;
  punch_type: 'clock_in' | 'clock_out';
  latitude?: number;
  longitude?: number;
  device_type: string;
}

const TimeClock: React.FC<TimeClockProps> = ({ employeeId, employeeName, locationName }) => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [isClockedIn, setIsClockedIn] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [location, setLocation] = useState<{ latitude: number; longitude: number } | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [lastPunch, setLastPunch] = useState<any>(null);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    // Get current location for geofencing
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          });
          setLocationError(null);
        },
        (error) => {
          setLocationError('Unable to get location. Please enable location services.');
          console.error('Location error:', error);
        }
      );
    } else {
      setLocationError('Geolocation is not supported by this browser.');
    }
  }, []);

  const handlePunch = async (punchType: 'clock_in' | 'clock_out') => {
    setIsLoading(true);
    
    try {
      const punchData: PunchData = {
        employee_id: employeeId,
        punch_type: punchType,
        device_type: 'web',
        ...(location && {
          latitude: location.latitude,
          longitude: location.longitude,
        }),
      };

      const response = await axios.post('/api/time-attendance/punch', punchData);
      
      if (response.data.success) {
        setIsClockedIn(punchType === 'clock_in');
        setLastPunch(response.data.time_entry);
        
        toast.success(response.data.message);
        
        // Show warnings if any
        if (response.data.warnings && response.data.warnings.length > 0) {
          response.data.warnings.forEach((warning: string) => {
            toast(warning, { icon: '⚠️' });
          });
        }
      }
    } catch (error: any) {
      console.error('Punch error:', error);
      toast.error(error.response?.data?.detail || 'Failed to record punch');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = () => {
    if (isClockedIn) {
      return 'text-green-600 bg-green-100';
    }
    return 'text-red-600 bg-red-100';
  };

  const getStatusIcon = () => {
    if (isClockedIn) {
      return <CheckCircle className="w-5 h-5" />;
    }
    return <XCircle className="w-5 h-5" />;
  };

  return (
    <div className="max-w-md mx-auto bg-white rounded-xl shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-white text-lg font-semibold">Time Clock</h2>
            <p className="text-blue-100 text-sm">{employeeName}</p>
          </div>
          <Clock className="w-8 h-8 text-white" />
        </div>
      </div>

      {/* Current Time */}
      <div className="px-6 py-4 bg-gray-50">
        <div className="text-center">
          <div className="text-3xl font-mono font-bold text-gray-800">
            {format(currentTime, 'HH:mm:ss')}
          </div>
          <div className="text-sm text-gray-600 mt-1">
            {format(currentTime, 'EEEE, MMMM do, yyyy')}
          </div>
        </div>
      </div>

      {/* Location Status */}
      <div className="px-6 py-3 border-b">
        <div className="flex items-center space-x-2">
          <MapPin className="w-4 h-4 text-gray-500" />
          <span className="text-sm text-gray-600">{locationName}</span>
          {locationError && (
            <AlertTriangle className="w-4 h-4 text-yellow-500" />
          )}
        </div>
        {locationError && (
          <p className="text-xs text-yellow-600 mt-1">{locationError}</p>
        )}
      </div>

      {/* Status */}
      <div className="px-6 py-4">
        <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor()}`}>
          {getStatusIcon()}
          <span className="ml-2">
            {isClockedIn ? 'Clocked In' : 'Clocked Out'}
          </span>
        </div>
      </div>

      {/* Punch Buttons */}
      <div className="px-6 py-4 space-y-3">
        <button
          onClick={() => handlePunch('clock_in')}
          disabled={isLoading || isClockedIn}
          className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
            isClockedIn
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-green-600 text-white hover:bg-green-700 focus:ring-2 focus:ring-green-500 focus:ring-offset-2'
          }`}
        >
          {isLoading ? 'Processing...' : 'Clock In'}
        </button>

        <button
          onClick={() => handlePunch('clock_out')}
          disabled={isLoading || !isClockedIn}
          className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
            !isClockedIn
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-red-600 text-white hover:bg-red-700 focus:ring-2 focus:ring-red-500 focus:ring-offset-2'
          }`}
        >
          {isLoading ? 'Processing...' : 'Clock Out'}
        </button>
      </div>

      {/* Last Punch Info */}
      {lastPunch && (
        <div className="px-6 py-4 bg-gray-50 border-t">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Last Punch</h4>
          <div className="text-sm text-gray-600">
            <div className="flex justify-between">
              <span>Time:</span>
              <span>{format(new Date(lastPunch.punch_time), 'HH:mm:ss')}</span>
            </div>
            <div className="flex justify-between">
              <span>Date:</span>
              <span>{format(new Date(lastPunch.punch_time), 'MMM dd, yyyy')}</span>
            </div>
            <div className="flex justify-between">
              <span>Type:</span>
              <span className="capitalize">{lastPunch.punch_type.replace('_', ' ')}</span>
            </div>
            {lastPunch.is_within_grace_period === false && (
              <div className="flex justify-between text-yellow-600">
                <span>Status:</span>
                <span>Outside Grace Period</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default TimeClock;