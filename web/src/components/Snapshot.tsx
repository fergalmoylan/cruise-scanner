import { DataTable } from 'primereact/datatable';
import {Column} from "primereact/column";

type SnapshotRow = {
    price: number;
    ship: string;
    departure_port: string;
    nights: number;
};

const MOCK_SNAPSHOT_ROWS: SnapshotRow[] = [
    { price: 799,  ship: 'Oasis of the Seas',      departure_port: 'Cape Liberty, NJ',  nights: 7 },
    { price: 1049, ship: 'Symphony of the Seas',   departure_port: 'Miami, FL',         nights: 7 },
    { price: 699,  ship: 'Anthem of the Seas',     departure_port: 'Southampton, UK',   nights: 5 },
    { price: 1199, ship: 'Icon of the Seas',       departure_port: 'Miami, FL',         nights: 7 },
    { price: 899,  ship: 'Quantum of the Seas',    departure_port: 'Singapore',         nights: 5 },
];

export function Snapshot() {

    return (
        <div className="app-shell p-3 justify-content-center align-items-center ">
            <div className="mb-1 mb-1">
                <h3 className="text-left mt-0 mb-1 border-bottom-1">Latest Price Snapshots 📸</h3>
            </div>
            <div className="mb-1 mt-3 max-h-fit">
                <DataTable scrollable={true} value={MOCK_SNAPSHOT_ROWS}>
                    <Column field="price" header="Price"></Column>
                    <Column field="ship" header="Ship"></Column>
                    <Column field="departure_port" header="Departure"></Column>
                    <Column field="nights" header="Nights"></Column>
                </DataTable>
            </div>

        </div>
    );
}
