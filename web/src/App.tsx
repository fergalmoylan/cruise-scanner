import { useState } from 'react';
import { Button } from 'primereact/button';
import { Snapshot } from './components/Snapshot.tsx';

import './App.css';

type View = 'snapshot' | 'trends' | 'deals';

export default function App() {
    const [view, setView] = useState<View>('snapshot');

    return (
        <div className="app-shell p-3 justify-content-center align-items-center ">
            <div className="glass p-4 mb-4 mb-3">
                <h1 className="text-center">🚢 Cruise Price Scanner</h1>

                <div className="flex justify-content-center flex-wrap align-items-center gap-2">
                    <Button
                        label="Latest Snapshot"
                        onClick={() => setView('snapshot')}
                        className={`w-12rem nav-btn ${view === 'snapshot' ? 'p-button-raised' : 'button-inactive'}`}
                    />
                    <Button
                        label="Price Trends"
                        onClick={() => setView('trends')}
                        className={`w-12rem nav-btn ${view === 'snapshot' ? 'p-button-raised' : 'button-inactive'}`}
                    />
                    <Button
                        label="Best Deals"
                        onClick={() => setView('deals')}
                        className={`w-12rem nav-btn ${view === 'snapshot' ? 'p-button-raised' : 'button-inactive'}`}
                    />
                </div>
            </div>

            <div className="glass p-4 content-panel">
                {view === 'snapshot' && <Snapshot />}
                {view === 'trends' && <div>Trends view…</div>}
                {view === 'deals' && <div>Deals view…</div>}
            </div>
        </div>
    );
}
