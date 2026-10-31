import { CSSResult, LitElement, TemplateResult, html } from 'lit';
import { property } from 'lit/decorators.js';
import { fireEvent, HomeAssistant } from 'custom-card-helpers';
import { styles } from './styles';
import { getCardLanguage, getTranslations, translatedMetricLabel, translatedStatus } from './localize';
import {
  DEFAULT_MEASUREMENTS,
  DiyPlantsCardConfig,
  METRIC_ICONS,
  METRIC_LABELS,
  HomeAssistantState,
  Measurement,
  formatValue,
  formatMeasurementValue,
  measurementPercent,
  measurementStatus,
  readMeasurements,
} from './model';

const CARD_TYPE = 'diy-plants-card';

const icon = (name: string): TemplateResult => html`<ha-icon .icon=${name}></ha-icon>`;

export class DiyPlantsCard extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;
  @property({ attribute: false }) public config?: DiyPlantsCardConfig;

  public setConfig(config: DiyPlantsCardConfig): void {
    if (!config.entity) throw new Error('You need to define the DIY Plants health entity');
    this.config = config;
  }

  public getCardSize(): number {
    return 3;
  }

  public static getStubConfig(): DiyPlantsCardConfig {
    return {
      type: `custom:${CARD_TYPE}`,
      entity: 'sensor.my_plant_health',
    };
  }

  public static getConfigForm() {
    const language = typeof document !== 'undefined' && document.documentElement.lang.toLowerCase().startsWith('da') ? 'da' : 'en';
    const text = getTranslations(language);
    return {
      schema: [
        {
          name: 'entity',
          required: true,
          selector: { entity: { domain: 'sensor' } },
        },
        {
          name: 'name',
          selector: { text: {} },
        },
        {
          name: 'subtitle',
          selector: { text: {} },
        },
        {
          name: 'image',
          selector: { text: {} },
        },
        {
          name: 'fertilizer_sensor',
          selector: { entity: { domain: 'sensor' } },
        },
        {
          type: 'expandable',
          name: '',
          title: text.measurements,
          schema: [
            {
              name: 'show_measurements',
              selector: {
                select: {
                  multiple: true,
                  options: Object.keys(METRIC_LABELS).map((value) => ({ value, label: translatedMetricLabel(value, language) })),
                },
              },
            },
            {
              name: 'moisture_min',
              selector: { number: { min: 0, max: 100, step: 1, mode: 'box' } },
            },
            {
              name: 'moisture_max',
              selector: { number: { min: 0, max: 100, step: 1, mode: 'box' } },
            },
            {
              name: 'moisture_min_sensor',
              selector: { entity: { domain: 'sensor' } },
            },
            {
              name: 'moisture_max_sensor',
              selector: { entity: { domain: 'sensor' } },
            },
          ],
        },
        {
          type: 'expandable',
          name: '',
          title: text.appearance,
          schema: [
            {
              name: 'display_type',
              selector: {
                select: {
                  options: [
                    { value: 'full', label: text.full },
                    { value: 'compact', label: text.compact },
                  ],
                },
              },
            },
            {
              name: 'show_health',
              selector: { boolean: {} },
            },
            {
              name: 'text_size',
              selector: {
                select: {
                  options: [
                    { value: 'small', label: text.small },
                    { value: 'medium', label: text.normal },
                    { value: 'large', label: text.large },
                  ],
                },
              },
            },
            {
              name: 'hide_units',
              selector: { boolean: {} },
            },
            {
              name: 'bars_per_row',
              selector: { number: { min: 1, max: 2, step: 1, mode: 'box' } },
            },
          ],
        },
      ],
      computeLabel: (schema: { name: string }) => ({
        entity: text.entity,
        name: text.name,
        subtitle: text.subtitle,
        image: text.image,
        fertilizer_sensor: text.fertilizerSensor,
        show_measurements: text.showMeasurements,
        moisture_min: text.moistureMin,
        moisture_max: text.moistureMax,
        moisture_min_sensor: text.moistureMinSensor,
        moisture_max_sensor: text.moistureMaxSensor,
        display_type: text.displayType,
        text_size: text.textSize,
        show_health: text.showHealth,
        hide_units: text.hideUnits,
        bars_per_row: text.barsPerRow,
      }[schema.name] ?? schema.name),
    };
  }

  private openMoreInfo(entityId = this.config?.entity): void {
    if (!entityId) return;
    fireEvent(this, 'hass-more-info', { entityId });
  }

  private renderMeasurement(metric: string, measurement: Measurement): TemplateResult {
    const language = getCardLanguage(this.hass);
    const minSensor = this.config?.moisture_min_sensor ? this.hass?.states[this.config.moisture_min_sensor] : undefined;
    const maxSensor = this.config?.moisture_max_sensor ? this.hass?.states[this.config.moisture_max_sensor] : undefined;
    const minSensorValue = minSensor ? Number(String(minSensor.state).replace(',', '.')) : Number.NaN;
    const maxSensorValue = maxSensor ? Number(String(maxSensor.state).replace(',', '.')) : Number.NaN;
    const configuredMeasurement = metric === 'moisture'
      ? {
        ...measurement,
        minimum: Number.isFinite(minSensorValue) ? minSensorValue : this.config?.moisture_min ?? measurement.minimum,
        maximum: Number.isFinite(maxSensorValue) ? maxSensorValue : this.config?.moisture_max ?? measurement.maximum,
      }
      : measurement;
    const status = measurementStatus(configuredMeasurement);
    const percent = measurementPercent(configuredMeasurement) ?? 0;
    const hideUnits = this.config?.hide_units ?? this.config?.display_type === 'compact';
    const unit = hideUnits ? '' : measurement.unit ?? '';
    const label = translatedMetricLabel(metric, language);
    const metricIcon = METRIC_ICONS[metric] ?? 'mdi:sprout';
    const entityId = this.config?.measurement_entities?.[metric]
      ?? configuredMeasurement.entity_id
      ?? configuredMeasurement.source_entity;

    return html`
      <div
        class="measurement${entityId ? ' clickable' : ''}"
        title=${entityId ? `${label}: ${entityId}` : label}
        role=${entityId ? 'button' : 'presentation'}
        tabindex=${entityId ? '0' : '-1'}
        @click=${entityId ? () => this.openMoreInfo(entityId) : undefined}
        @keydown=${entityId ? (event: KeyboardEvent) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            this.openMoreInfo(entityId);
          }
        } : undefined}
      >
        <div class="measurement-heading">${icon(metricIcon)}<span>${label}</span></div>
        <div class="value-line">
          <span class="value">${formatMeasurementValue(metric, configuredMeasurement.value)} <span class="unit">${unit}</span></span>
          <ha-icon class="${status}" .icon=${status === 'bad' ? 'mdi:alert-circle-outline' : status === 'unavailable' ? 'mdi:help-circle-outline' : 'mdi:check-circle-outline'}></ha-icon>
        </div>
        <div class="meter"><div class="meter-fill ${status}" style="width: ${percent}%"></div></div>
        ${typeof configuredMeasurement.minimum === 'number' && typeof configuredMeasurement.maximum === 'number'
          ? html`<div class="range"><span><b>${getTranslations(language).minimum}</b> ${formatMeasurementValue(metric, configuredMeasurement.minimum)}${unit}</span><span><b>${getTranslations(language).maximum}</b> ${formatMeasurementValue(metric, configuredMeasurement.maximum)}${unit}</span></div>`
          : ''}
      </div>
    `;
  }

  protected render(): TemplateResult {
    if (!this.config || !this.hass) return html``;
    const language = getCardLanguage(this.hass);
    const text = getTranslations(language);
    const state = this.hass.states[this.config.entity ?? ''] as HomeAssistantState | undefined;
    if (!state) return html`<ha-card><div class="warning">${text.unavailableEntity}: ${this.config.entity}</div></ha-card>`;

    const measurements = readMeasurements(state);
    const selected = this.config.show_measurements ?? DEFAULT_MEASUREMENTS;
    const visible = selected.filter((metric) => measurements[metric]);
    const name = this.config.name ?? String(state.attributes.friendly_name ?? state.entity_id);
    const subtitle = this.config.subtitle ?? text.subtitle;
    const image = this.config.image ?? (typeof state.attributes.entity_picture === 'string' ? state.attributes.entity_picture : undefined);
    const showHealth = this.config.show_health ?? true;
    const healthStatus = state.state.toLowerCase().includes('ok') ? 'good' : state.state.toLowerCase().includes('unavailable') ? 'unavailable' : 'bad';
    const fertilizer = this.config.fertilizer_sensor ? this.hass.states[this.config.fertilizer_sensor] : undefined;
    const fertilizerStatus = fertilizer
      ? fertilizer.state.toLowerCase().includes('ok') ? 'good' : fertilizer.state.toLowerCase().includes('unavailable') ? 'unavailable' : 'bad'
      : 'unavailable';
    const barsPerRow = this.config.bars_per_row ?? (this.config.display_type === 'compact' ? 1 : 2);
    const textSize = this.config.text_size ?? 'medium';

    return html`
      <ha-card class="text-size-${textSize}">
        <div class="header" @click=${() => this.openMoreInfo()}>
          ${image
            ? html`<img class="plant-image" src=${image} alt=${name}>`
            : html`<div class="header-icon">${icon('mdi:flower')}</div>`}
          <div class="heading">
            <div class="name">${name}</div>
            <div class="subtitle">${subtitle}</div>
            </div>
            ${showHealth ? html`<div class="health ${healthStatus}">${icon(healthStatus === 'good' ? 'mdi:heart-pulse' : 'mdi:alert-circle-outline')}<span>${translatedStatus(state.state, language)}</span></div>` : ''}
            ${fertilizer && fertilizerStatus !== 'good' ? html`<div class="health ${fertilizerStatus}">${icon('mdi:leaf')}<span>${translatedStatus(fertilizer.state, language)}</span></div>` : ''}
        </div>
        ${visible.length > 0
          ? html`<div class="measurements" style="--bars-per-row: ${barsPerRow}">${visible.map((metric) => this.renderMeasurement(metric, measurements[metric]))}</div>`
          : html`<div class="warning">${text.noMeasurements}</div>`}
      </ha-card>
    `;
  }

  public static get styles(): CSSResult {
    return styles;
  }
}

// The card can be loaded both by the integration and by an older standalone
// resource, so only register it once.
if (!customElements.get(CARD_TYPE)) {
  customElements.define(CARD_TYPE, DiyPlantsCard);
  (window as Window & { customCards?: unknown[] }).customCards ??= [];
  ((window as unknown) as Window & { customCards: unknown[] }).customCards.push({
    type: CARD_TYPE,
    name: 'DIY Plants Card',
    description: 'Display measurements from the DIY Plants Home Assistant integration',
    preview: true,
  });
}
