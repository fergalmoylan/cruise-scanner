import Papa from 'papaparse';


export type RowData = {
    "scrape_timestamp": string;
    "source_url": string;
    "cruise_url": string;
    "cruise_id": string;
    "cruise_name": string;
    "nights": number;
    "ship_name": string;
    "ship_code": string;
    "departure": string;
    "destination_code": string;
    "visiting_ports": string;
    "sailing_id": string;
    "sailing_date": string;
    "room_type": string;
    "price": number;
}


export async function fetchCsv(url: string): Promise<string> {
    const csv = await fetch(url, { cache: 'no-cache' });
    if (!csv.ok) throw new Error(`Failed to fetch CSV: ${csv.status}`);
    return csv.text();
}

export function parseCsv(text: string) {
    const parsedCSV = Papa.parse<RowData>(text, {
        header: true,
        skipEmptyLines: true,
        dynamicTyping: {nights: true, price: true}
    });

    if (parsedCSV.errors.length) {
        console.warn("CSV parse errors: " + parsedCSV.errors);
    }
    return parsedCSV.data as RowData[];
}
