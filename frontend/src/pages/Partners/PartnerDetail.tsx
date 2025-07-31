import React from 'react';
import { useParams } from 'react-router-dom';

const PartnerDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Partner Details</h1>
        <p className="text-gray-600">Partner ID: {id}</p>
      </div>
      
      <div className="bg-white shadow rounded-lg p-6">
        <p className="text-gray-500">Detailed partner information will be displayed here.</p>
        <p className="text-sm text-gray-400 mt-2">
          Features will include: company profile, capabilities, feedback history, and performance metrics.
        </p>
      </div>
    </div>
  );
};

export default PartnerDetail;