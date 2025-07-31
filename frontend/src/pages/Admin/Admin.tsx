import React from 'react';

const Admin: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">System Administration</h1>
        <p className="text-gray-600">Manage system settings and user access</p>
      </div>
      
      <div className="bg-white shadow rounded-lg p-6">
        <p className="text-gray-500">Administration interface will be implemented here.</p>
        <p className="text-sm text-gray-400 mt-2">
          Features will include: user management, system configuration, audit logs, and maintenance tools.
        </p>
      </div>
    </div>
  );
};

export default Admin;