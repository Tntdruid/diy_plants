export interface HomeAssistantState {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
}

export interface Measurement {
  entity_id?: string;
  source_entity?: string;
  value: number | null;
  raw?: string | null;
  unit?: string;
  minimum?: number;
  maximum?: number;
  status?: string;
  error?: string | null;
}

export interface Measurements {
  [metric: string]: Measurement;
}

export interface DiyPlantsCardConfig {
  type: string;
  entity?: string;
  name?: string;
  subtitle?: string;
  image?: string;
  show_measurements?: string[];
  moisture_min?: number;
  moisture_max?: number;
  moisture_min_sensor?: string;
  moisture_max_sensor?: string;
  fertilizer_sensor?: string;
  display_type?: 'full' | 'compact';
  text_size?: 'small' | 'medium' | 'large';
  hide_units?: boolean;
  show_health?: boolean;
  bars_per_row?: 1 | 2;
  measurement_entities?: Record<string, string>;
}

export const DEFAULT_MEASUREMENTS = [
  'moisture',
  'conductivity',
  'temperature',
  'air_temperature',
  'humidity',
  'illuminance',
  'dli',
];

export const METRIC_LABELS: Record<string, string> = {
  moisture: 'Soil moisture',
  conductivity: 'Soil conductivity',
  temperature: 'Soil temperature',
  air_temperature: 'Air temperature',
  humidity: 'Air humidity',
  illuminance: 'Illuminance',
  dli: 'DLI',
};

export const METRIC_ICONS: Record<string, string> = {
  moisture: 'mdi:water-percent',
  conductivity: 'mdi:leaf',
  temperature: 'mdi:thermometer',
  air_temperature: 'mdi:thermometer-lines',
  humidity: 'mdi:water-percent',
  illuminance: 'mdi:brightness-5',
  dli: 'mdi:weather-sunny',
};

export function readMeasurements(state: HomeAssistantState | undefined): Measurements {
  const measurements = state?.attributes.measurements;
  if (!measurements || typeof measurements !== 'object' || Array.isArray(measurements)) {
    return {};
  }

  return measurements as Measurements;
}

export function measurementPercent(measurement: Measurement): number | null {
  if (typeof measurement.value !== 'number' || !Number.isFinite(measurement.value)) {
    return null;
  }
  if (typeof measurement.minimum !== 'number' || typeof measurement.maximum !== 'number') {
    return null;
  }
  if (measurement.minimum === measurement.maximum) return 100;
  const percent = ((measurement.value - measurement.minimum) / (measurement.maximum - measurement.minimum)) * 100;
  return Math.max(0, Math.min(100, percent));
}

export function measurementStatus(measurement: Measurement): 'good' | 'bad' | 'unavailable' {
  if (measurement.status === 'unavailable' || typeof measurement.value !== 'number' || !Number.isFinite(measurement.value)) {
    return 'unavailable';
  }
  if (measurement.status === 'low' || measurement.status === 'high') return 'bad';
  return 'good';
}

export function formatValue(value: unknown): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return 'Unavailable';
  return Number.isInteger(value) ? String(value) : value.toFixed(1).replace(/\.0$/, '');
}

export function formatMeasurementValue(metric: string, value: unknown): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return 'Unavailable';
  if (metric === 'moisture' || metric === 'humidity') return String(Math.round(value));
  return formatValue(value);
}
