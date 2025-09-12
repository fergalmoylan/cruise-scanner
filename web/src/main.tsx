import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import 'primereact/resources/themes/lara-dark-blue/theme.css'
import 'primereact/resources/primereact.min.css'
import 'primeicons/primeicons.css'
import 'primeflex/primeflex.css'
import {parseCsv, type RowData} from "./lib/csv.ts";


async function bootstrap() {
    const csvUrl = `${import.meta.env.BASE_URL}cruise_prices_v2.csv`;
    const response = await fetch(csvUrl);
    if (!response.ok) {
        return;
    }
    const csvText = await response.text();
    const cruiseData: RowData[] = parseCsv(csvText);

    createRoot(document.getElementById("root")!).render(
        <StrictMode>
            <App cruiseData={cruiseData} />
        </StrictMode>
    );
}

bootstrap();
