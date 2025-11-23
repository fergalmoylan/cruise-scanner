import { DataTable } from 'primereact/datatable';
import {Column} from "primereact/column";
import type {RowData} from "../lib/csv.ts";
import {getCheapestLatestSuites} from "../lib/latest-snapshot";

export function Snapshot({ cruiseData }: { cruiseData: RowData[] }) {
    const CHEAPEST_SUITES = getCheapestLatestSuites(cruiseData);
    return (
        <div className="app-shell p-3 justify-content-center align-items-center ">
            <div className="mb-1 mb-1">
                <h3 className="text-left mt-0 mb-1 border-bottom-1">Cheapest Suites Snapshot 📸</h3>
            </div>
            <div className="mb-1 mt-3 max-h-fit">
                <DataTable
                    value={CHEAPEST_SUITES}
                    paginator
                    rows={5}
                    rowsPerPageOptions={[5, 10, 20, 100]}
                    style={{ borderRadius: '0.5rem', overflow: 'hidden', fontSize: '0.875rem' }}
                >
                    <Column field="ship_name" header="Ship"></Column>
                    <Column field="sailing_date" header="Departure Date"></Column>
                    <Column field="nights" header="Nights"></Column>
                    <Column field="visiting_ports" header="Ports"></Column>
                    <Column field="room_type" header="Room Type"></Column>
                    <Column field="cruise_url" header="Link" body={(row) => (
                        <a href={row.cruise_url} target="_blank" rel="noreferrer">
                            View
                        </a>
                    )}></Column>
                    <Column field="price" header="Price" body={(row) =>
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
