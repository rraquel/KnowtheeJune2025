import React from 'react';
import { useEmployees } from '../hooks/useEmployees';

const TalentTable: React.FC = () => {
  const { data, isLoading, isError } = useEmployees();

  if (isLoading) return <div>Loading employees...</div>;
  if (isError) return <div>Error loading employees.</div>;

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full bg-white border border-gray-200 rounded-lg">
        <thead>
          <tr>
            <th className="px-4 py-2 border-b">Name</th>
            <th className="px-4 py-2 border-b">Email</th>
            <th className="px-4 py-2 border-b">Location</th>
            <th className="px-4 py-2 border-b">Position</th>
            <th className="px-4 py-2 border-b">Department</th>
          </tr>
        </thead>
        <tbody>
          {data && data.map((emp) => (
            <tr key={emp.id} className="hover:bg-gray-50">
              <td className="px-4 py-2 border-b">{emp.full_name}</td>
              <td className="px-4 py-2 border-b">{emp.email}</td>
              <td className="px-4 py-2 border-b">{emp.location}</td>
              <td className="px-4 py-2 border-b">{emp.current_position}</td>
              <td className="px-4 py-2 border-b">{emp.department}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TalentTable; 