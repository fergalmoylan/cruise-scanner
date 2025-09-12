import { describe, it, expect, vi, afterEach } from 'vitest';
import { readFileSync } from 'node:fs';
// @ts-ignore
import path from 'node:path';

import { fetchCsv, parseCsv } from '../src/lib/csv';
import { groupByCruiseId, groupBySailingId } from '../src/lib/parser';
import {
    getCheapestLatestSuites,
    getLatestSnapshot,
    groupByRoomType
} from "../src/lib/latest-snapshot";

const FIXTURE_PATH = path.resolve(__dirname, 'test_resources', 'cruise_prices_large.csv');
const csvText = readFileSync(FIXTURE_PATH, 'utf8');

afterEach(() => {
    vi.restoreAllMocks();
});

describe('fetchCsv', () => {
    it('returns text when fetch succeeds (200 OK)', async () => {
        const sample = 'a,b\n1,2\n';
        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            status: 200,
            text: () => Promise.resolve(sample),
        });

        const text = await fetchCsv('/fake.csv');
        expect(text).toBe(sample);
        expect(global.fetch).toHaveBeenCalledWith('/fake.csv', { cache: 'no-cache' });
    });

    it('throws when fetch is not ok', async () => {
        global.fetch = vi.fn().mockResolvedValue({
            ok: false,
            status: 404,
        });

        await expect(fetchCsv('/missing.csv')).rejects.toThrow(/Failed to fetch CSV: 404/);
    });
});

describe('parseCsv', () => {
    it('parses headered CSV into objects and casts numbers via dynamicTyping', () => {
        const rows = parseCsv(csvText);

        expect(Array.isArray(rows)).toBe(true);
        expect(rows.length).toBeGreaterThan(0);

        const row = rows[0] as Record<string, unknown>;
        expect(row).toHaveProperty('scrape_timestamp');
        expect(row).toHaveProperty('source_url');
        expect(row).toHaveProperty('cruise_id');
        expect(row).toHaveProperty('cruise_name');
        expect(row).toHaveProperty('nights');
        expect(row).toHaveProperty('ship_name');
        expect(row).toHaveProperty('ship_code');
        expect(row).toHaveProperty('departure');
        expect(row).toHaveProperty('destination_code');
        expect(row).toHaveProperty('sailing_id');
        expect(row).toHaveProperty('sailing_date');
        expect(row).toHaveProperty('room_type');
        expect(row).toHaveProperty('price');
        expect(typeof row.nights).toBe('number');
        expect(typeof row.price).toBe('number');
        expect(typeof row.cruise_name).toBe('string');
        expect(typeof row.sailing_date).toBe('string');
    });

    it('logs a warning when Papa reports parse errors (malformed CSV)', () => {
        const badCsv = `price,ship\n"999,Oasis of the Seas\n`;
        const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
        const rows = parseCsv(badCsv);
        expect(Array.isArray(rows)).toBe(true);
        expect(warnSpy).toHaveBeenCalled();

        warnSpy.mockRestore();
    });
});

describe('parseCsv', () => {
    it('parses headered CSV into objects and casts numbers via dynamicTyping', () => {
        const rows = parseCsv(csvText);
        // let cruises = groupByCruiseId(rows);
        // let sailings = groupBySailingId(rows);
        // let latest_snapshot = getLatestSnapshot(rows);
        // let room_types = groupByRoomType(latest_snapshot);
        console.log(getCheapestLatestSuites(rows));
        //console.log(room_types);
    });

});
