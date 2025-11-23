import { type RowData } from './csv.ts'

export type GroupedRecords = Record<string, RowData[]>;

export function groupByCruiseId(rows: RowData[]) {
    let cruises: GroupedRecords = {}
    for (let i = rows.length - 1; i >= 0; i--) {
        (cruises[rows[i].cruise_id] ??=[]).push(rows[i]);
    }
    return cruises;
}

export function groupBySailingId(rows: RowData[]) {
    let sailings: GroupedRecords = {}
    for (let i = rows.length - 1; i >= 0; i--) {
        (sailings[rows[i].sailing_id] ??=[]).push(rows[i]);
    }
    return sailings;
}
