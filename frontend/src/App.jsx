import React, { useState } from 'react';
import Header from './components/Header';
import ChatBox from './components/ChatBox';
import SourcesDrawer from './components/SourcesDrawer';
import DisclaimerBanner from './components/DisclaimerBanner';

export default function App() {
  const [jurisdiction, setJurisdiction] = useState('Bengaluru');
  const [isSourcesOpen, setIsSourcesOpen] = useState(false);

  return (
    <div className="app-container">
      <Header
        jurisdiction={jurisdiction}
        onJurisdictionChange={setJurisdiction}
        onOpenSources={() => setIsSourcesOpen(true)}
      />

      <ChatBox jurisdiction={jurisdiction} />

      <DisclaimerBanner />

      <SourcesDrawer
        isOpen={isSourcesOpen}
        onClose={() => setIsSourcesOpen(false)}
      />
    </div>
  );
}
