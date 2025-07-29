import React from 'react';
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';

interface KPICardProps {
  title: string;
  value: string | number;
  change: number;
  isPositive: boolean;
  icon: React.ElementType;
  color: 'blue' | 'green' | 'yellow' | 'purple' | 'red';
}

const colorClasses = {
  blue: {
    bg: 'bg-blue-50',
    icon: 'text-blue-600',
    border: 'border-blue-200',
  },
  green: {
    bg: 'bg-green-50',
    icon: 'text-green-600',
    border: 'border-green-200',
  },
  yellow: {
    bg: 'bg-yellow-50',
    icon: 'text-yellow-600',
    border: 'border-yellow-200',
  },
  purple: {
    bg: 'bg-purple-50',
    icon: 'text-purple-600',
    border: 'border-purple-200',
  },
  red: {
    bg: 'bg-red-50',
    icon: 'text-red-600',
    border: 'border-red-200',
  },
};

const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  change,
  isPositive,
  icon: Icon,
  color,
}) => {
  const colorClass = colorClasses[color];

  return (
    <div className="bg-white overflow-hidden shadow rounded-lg border border-gray-200 hover:shadow-md transition-shadow duration-200">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className={clsx(
              'flex items-center justify-center h-8 w-8 rounded-md',
              colorClass.bg,
              colorClass.border,
              'border'
            )}>
              <Icon className={clsx('h-5 w-5', colorClass.icon)} />
            </div>
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">
                {title}
              </dt>
              <dd className="flex items-baseline">
                <div className="text-2xl font-semibold text-gray-900">
                  {value}
                </div>
                <div className={clsx(
                  'ml-2 flex items-baseline text-sm font-semibold',
                  isPositive ? 'text-green-600' : 'text-red-600'
                )}>
                  {isPositive ? (
                    <ArrowUpIcon className="self-center flex-shrink-0 h-4 w-4" />
                  ) : (
                    <ArrowDownIcon className="self-center flex-shrink-0 h-4 w-4" />
                  )}
                  <span className="sr-only">
                    {isPositive ? 'Increased' : 'Decreased'} by
                  </span>
                  {Math.abs(change).toFixed(1)}%
                </div>
              </dd>
            </dl>
          </div>
        </div>
      </div>
      <div className="bg-gray-50 px-5 py-3">
        <div className="text-sm">
          <a href="#" className="font-medium text-primary-700 hover:text-primary-900">
            View details
          </a>
        </div>
      </div>
    </div>
  );
};

export default KPICard;