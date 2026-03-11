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
    const csvUrlRcc = `${import.meta.env.BASE_URL}cruise_prices_rcc.csv`;
    const csvUrlMsc = `${import.meta.env.BASE_URL}cruise_prices_msc.csv`;
    const rcc_response = await fetch(csvUrlRcc);
    const msc_response = await fetch(csvUrlMsc)
    if (!rcc_response.ok || !msc_response.ok) {
        return;
    }
    const csvTextRcc = await rcc_response.text();
    const csvTextMsc = await msc_response.text();
    const cruiseDataRcc: RowData[] = parseCsv(csvTextRcc);
    const cruiseDataMsc: RowData[] = parseCsv(csvTextMsc);
    const cruiseCsvs: RowData[][] = [cruiseDataRcc, cruiseDataMsc]

    createRoot(document.getElementById("root")!).render(
        <StrictMode>
            <App cruiseData={cruiseCsvs} />
        </StrictMode>
    );
}

bootstrap();
