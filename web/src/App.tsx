import { useState } from 'react';
import { Button } from 'primereact/button';
import { Snapshot } from './components/Snapshot.tsx';

import './App.css';
import type {RowData} from "./lib/csv.ts";

type View = 'rcc_snapshot' | 'msc_snapshot' | 'trends' | 'deals';

export default function App({ cruiseData }: { cruiseData: RowData[][] }) {
    const [view, setView] = useState<View>('rcc_snapshot');

    return (
        <div className="app-shell p-2 justify-content-center align-items-center ">
            <div className="glass p-3 mb-4">
                <h1 className="text-center">🚢 Cruise Price Scanner</h1>

                <div className="flex justify-content-center flex-wrap align-items-center gap-2">
                    <Button
                        label="Latest RCC Snapshot"
                        onClick={() => setView('rcc_snapshot')}
                        className={`w-16rem nav-btn ${view === 'rcc_snapshot' ? 'p-button-raised' : 'button-inactive'}`}
                    />
                    <Button
                        label="Latest MSC Snapshot"
                        onClick={() => setView('msc_snapshot')}
                        className={`w-16rem nav-btn ${view === 'msc_snapshot' ? 'p-button-raised' : 'button-inactive'}`}
                    />
                    <Button
                        label="Price Trends"
                        onClick={() => setView('trends')}
                        className={`w-16rem nav-btn ${view === 'trends' ? 'p-button-raised' : 'button-inactive'}`}
                    />
                    <Button
                        label="Best Deals"
                        onClick={() => setView('deals')}
                        className={`w-16rem nav-btn ${view === 'deals' ? 'p-button-raised' : 'button-inactive'}`}
                    />
                </div>
            </div>

            <div className="glass p-4 content-panel">
                {view === 'rcc_snapshot' && <Snapshot cruiseData={cruiseData[0]}/>}
                {view === 'msc_snapshot' && <Snapshot cruiseData={cruiseData[1]}/>}
                {view === 'trends' && <div>Trends view…</div>}
                {view === 'deals' && <div>Deals view…</div>}
            </div>
        </div>
    );
}
