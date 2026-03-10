import { DataTable } from 'primereact/datatable';
import {Column} from "primereact/column";
import type {RowData} from "../lib/csv.ts";
import {getCheapestLatestSuites, formatScrapeTimestamp} from "../lib/latest-snapshot";

export function Snapshot({ cruiseData }: { cruiseData: RowData[] }) {
    const CHEAPEST_SUITES = getCheapestLatestSuites(cruiseData);
    const latestTimestamp = cruiseData[cruiseData.length - 1].scrape_timestamp;
    const latestTimestampLabel = formatScrapeTimestamp(latestTimestamp, {
        timeZone: "Europe/Dublin",
        assumeUtc: true,
    });
    return (
        <div className="app-shell justify-content-center align-items-center ">
            <div className="mb-1 mb-1">
                <h3 className="text-left mt-0 mb-1 border-bottom-1">Latest Suite Price Snapshot - {latestTimestampLabel}</h3>
            </div>
            <div className="mb-1 mt-3 max-h-fit">
                <DataTable
                    value={CHEAPEST_SUITES}
                    className="navy-table"
                    paginator
                    scrollable
                    scrollHeight="60vh"
                    rows={10}
                    rowsPerPageOptions={[5, 10, 20, 100]}
                    style={{ borderRadius: '0.5rem', overflow: 'hidden', fontSize: '0.875rem' }}
                >
                    <Column field="ship_name" header="Ship" style={{ width: '12.75%' }}></Column>
                    <Column field="sailing_date" header="Departure Date" sortable style={{ width: '6.25%' }}></Column>
                    <Column field="nights" header="Nights" sortable style={{ width: '6.25%' }}></Column>
                    <Column field="visiting_ports" header="Ports" style={{ width: '49.75%' }}></Column>
                    <Column field="room_type" header="Room Type" style={{ width: '12.5%' }}></Column>
                    <Column field="cruise_url" header="Link" style={{ width: '6.25%' }} body={(row) => (
                        <a href={row.cruise_url} target="_blank" rel="noreferrer">
                            View
                        </a>
                    )}></Column>
                    <Column field="price" sortable style={{ width: '12.5%' }} header="Price" body={(row) =>
                        row.price.toLocaleString("en-IE", {
                            style: "currency",
                            currency: "EUR",
                            minimumFractionDigits: 0,
                        })
                    }></Column>
                </DataTable>
            </div>

        </div>
    );
}
