import { HomeAssistant } from 'custom-card-helpers';
import { METRIC_LABELS } from './model';

export type CardLanguage = 'da' | 'en';

const translations = {
  en: {
    measurements: 'Measurements',
    appearance: 'Appearance',
    entity: 'Entity',
    name: 'Display name',
    image: 'Plant photo URL',
    showMeasurements: 'Measurements to show',
    moistureMin: 'Minimum soil moisture',
    moistureMax: 'Maximum soil moisture',
    moistureMinSensor: 'Minimum moisture sensor',
    moistureMaxSensor: 'Maximum moisture sensor',
    fertilizerSensor: 'Fertilizer reminder sensor',
    minimum: 'Min',
    maximum: 'Max',
    displayType: 'Display type',
    textSize: 'Text size',
    small: 'Small',
    normal: 'Normal',
    large: 'Large',
    full: 'Full',
    compact: 'Compact',
    showHealth: 'Show health status',
    hideUnits: 'Hide units',
    barsPerRow: 'Bars per row',
    subtitle: 'DIY Plants',
    unavailableEntity: 'Entity not available',
    noMeasurements: 'No DIY Plants measurements are available.',
    statusOk: 'OK',
    statusAttention: 'Attention',
    statusUnavailable: 'Unavailable',
    statusNoSensors: 'No sensors',
    metrics: METRIC_LABELS,
  },
  da: {
    measurements: 'Målinger',
    appearance: 'Udseende',
    entity: 'Entitet',
    name: 'Visningsnavn',
    image: 'URL til plantefoto',
    showMeasurements: 'Målinger der vises',
    moistureMin: 'Minimum jordfugtighed',
    moistureMax: 'Maksimum jordfugtighed',
    moistureMinSensor: 'Sensor for minimum jordfugtighed',
    moistureMaxSensor: 'Sensor for maksimum jordfugtighed',
    fertilizerSensor: 'Gødningssensor',
    minimum: 'Min',
    maximum: 'Maks',
    displayType: 'Visningstype',
    textSize: 'Tekststørrelse',
    small: 'Lille',
    normal: 'Normal',
    large: 'Stor',
    full: 'Fuld',
    compact: 'Kompakt',
    showHealth: 'Vis sundhedsstatus',
    hideUnits: 'Skjul enheder',
    barsPerRow: 'Målinger pr. række',
    subtitle: 'DIY Plants',
    unavailableEntity: 'Entiteten er ikke tilgængelig',
    noMeasurements: 'Ingen DIY Plants-målinger er tilgængelige.',
    statusOk: 'OK',
    statusAttention: 'Bemærk',
    statusUnavailable: 'Ikke tilgængelig',
    statusNoSensors: 'Ingen sensorer',
    metrics: {
      moisture: 'Jordfugtighed',
      conductivity: 'Jordens ledningsevne',
      temperature: 'Jordtemperatur',
      air_temperature: 'Lufttemperatur',
      humidity: 'Luftfugtighed',
      illuminance: 'Belysning',
      dli: 'DLI',
    },
  },
} as const;

export function getCardLanguage(hass?: HomeAssistant): CardLanguage {
  const language = (hass as (HomeAssistant & { locale?: { language?: string } }) | undefined)?.locale?.language
    ?? (typeof document !== 'undefined' ? document.documentElement.lang : '');
  return language?.toLowerCase().startsWith('da') ? 'da' : 'en';
}

export function getTranslations(language: CardLanguage) {
  return translations[language];
}

export function translatedMetricLabel(metric: string, language: CardLanguage): string {
  const metrics = getTranslations(language).metrics as Record<string, string>;
  return metrics[metric]
    ?? metric.replaceAll('_', ' ');
}

export function translatedStatus(state: string, language: CardLanguage): string {
  const normalized = state.toLowerCase();
  const translation = getTranslations(language);
  if (normalized.includes('unavailable')) return translation.statusUnavailable;
  if (normalized === 'no_sensors' || normalized === 'no sensors') return translation.statusNoSensors;
  if (normalized.includes('attention')) return translation.statusAttention;
  if (normalized.includes('ok')) return translation.statusOk;
  return state;
}
