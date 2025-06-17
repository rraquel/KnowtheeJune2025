import React from 'react';
import TalentTable from '../components/TalentTable';

const TalentExplorer: React.FC = () => {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Talent Explorer</h1>
      <TalentTable />
    </div>
  );
};

export default TalentExplorer; 