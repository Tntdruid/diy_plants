import { describe, expect, it } from 'vitest';
import {
  formatValue,
  formatMeasurementValue,
  measurementPercent,
  measurementStatus,
  readMeasurements,
} from '../src/model';

describe('DIY Plants card model', () => {
  it('reads the health sensor measurements attribute', () => {
    const measurements = readMeasurements({
      entity_id: 'sensor.monstera_health',
      state: 'OK',
      attributes: {
        measurements: { moisture: { value: 42, minimum: 20, maximum: 70 } },
      },
    });

    expect(measurements.moisture.value).toBe(42);
  });

  it('maps a value to a clamped bar percentage', () => {
    expect(measurementPercent({ value: 45, minimum: 20, maximum: 70 })).toBe(50);
    expect(measurementPercent({ value: 100, minimum: 20, maximum: 70 })).toBe(100);
  });

  it('uses the integration status when available', () => {
    expect(measurementStatus({ value: 42, status: 'ok' })).toBe('good');
    expect(measurementStatus({ value: 42, status: 'high' })).toBe('bad');
    expect(measurementStatus({ value: null, status: 'unavailable' })).toBe('unavailable');
  });

  it('formats numeric values without unnecessary zeroes', () => {
    expect(formatValue(42)).toBe('42');
    expect(formatValue(42.5)).toBe('42.5');
    expect(formatValue('unknown')).toBe('Unavailable');
  });

  it('rounds percentage measurements to whole numbers', () => {
    expect(formatMeasurementValue('moisture', 56.5)).toBe('57');
    expect(formatMeasurementValue('humidity', 42.4)).toBe('42');
  });
});
