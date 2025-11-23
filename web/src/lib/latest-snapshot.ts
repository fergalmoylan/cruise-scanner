import type {RowData} from "./csv.ts";
import type {GroupedRecords} from "./parser.ts";

export function getLatestSnapshot(rows: RowData[] ) {
    let last_scrape_timestamp = rows[rows.length-1].scrape_timestamp
    let latest_snapshot: RowData[] = []
    for (let i = rows.length - 1; i >= 0; i--) {
        if (rows[i].scrape_timestamp == last_scrape_timestamp) {
            latest_snapshot.push(rows[i])
        } else {
            return latest_snapshot
        }
    }
    return latest_snapshot
}

export function groupByRoomType(rows: RowData[]) {
    let room_types: GroupedRecords = {}
    for (let i = rows.length - 1; i >= 0; i--) {
        (room_types[rows[i].room_type] ??=[]).push(rows[i]);
    }
    return room_types;
}

export function groupByShip(rows: RowData[]) {
    let sailings: GroupedRecords = {}
    for (let i = rows.length - 1; i >= 0; i--) {
        (sailings[rows[i].sailing_id] ??=[]).push(rows[i]);
    }
    return sailings;
}

export function getCheapestLatestSuites(rows: RowData[]): RowData[] {
    if (rows.length === 0) return [];

    const latestTimestamp = rows[rows.length - 1].scrape_timestamp;
    const excludedRooms = new Set(["Interior", "Ocean View", "Balcony"]);
    const cheapestByCruiseId = new Map<string, RowData>();

    for (let i = rows.length - 1; i >= 0; i--) {
        const row = rows[i];

        if (row.scrape_timestamp !== latestTimestamp) break;
        if (excludedRooms.has(row.room_type)) continue;

        const existing = cheapestByCruiseId.get(row.cruise_id);
        if (!existing || row.price < existing.price) {
            cheapestByCruiseId.set(row.cruise_id, row);
        }
    }
    return Array.from(cheapestByCruiseId.values()).sort(
        (a, b) => a.price - b.price
    );
}
