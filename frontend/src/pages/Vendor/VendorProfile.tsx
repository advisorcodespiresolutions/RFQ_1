import React from 'react';

const VendorProfile: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>
        <p className="text-gray-600">Manage your company profile and information</p>
      </div>
      
      <div className="bg-white shadow rounded-lg p-6">
        <p className="text-gray-500">Vendor profile management interface will be implemented here.</p>
        <p className="text-sm text-gray-400 mt-2">
          Features will include: company information, capabilities, regions, certifications, and profile completion tracking.
        </p>
      </div>
    </div>
  );
};

export default VendorProfile;