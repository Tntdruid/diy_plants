import { css } from 'lit';

export const styles = css`
  :host {
    display: block;
  }

  ha-card {
    overflow: hidden;
    border: 1px solid color-mix(in srgb, var(--primary-text-color) 10%, transparent);
    background: linear-gradient(145deg, color-mix(in srgb, #6c9a72 8%, var(--card-background-color)), var(--card-background-color));
  }

  .header {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px;
    min-height: 76px;
    padding: 14px 16px;
    border-bottom: 1px solid color-mix(in srgb, var(--primary-text-color) 9%, transparent);
    background: linear-gradient(100deg, color-mix(in srgb, #6c9a72 14%, transparent), transparent 58%);
    cursor: pointer;
  }

  .header-icon {
    display: grid;
    place-items: center;
    width: 42px;
    height: 42px;
    border-radius: 50%;
    color: #47734e;
    background: color-mix(in srgb, #6c9a72 20%, var(--card-background-color));
    box-shadow: inset 0 0 0 1px color-mix(in srgb, #6c9a72 28%, transparent);
  }

  .plant-image {
    flex: 0 0 50px;
    width: 50px;
    height: 50px;
    border: 3px solid color-mix(in srgb, var(--primary-color) 34%, var(--card-background-color));
    border-radius: 50%;
    object-fit: cover;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.18);
  }

  .heading {
    min-width: 0;
    flex: 1 1 160px;
  }

  ha-card.text-size-small { --card-text-scale: 0.92; }
  ha-card.text-size-medium { --card-text-scale: 1; }
  ha-card.text-size-large { --card-text-scale: 1.12; }

  .name {
    overflow: hidden;
    color: var(--primary-text-color);
    font-size: calc(1.16rem * var(--card-text-scale, 1));
    font-weight: 700;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .subtitle {
    margin-top: 3px;
    color: var(--secondary-text-color);
    font-size: calc(0.86rem * var(--card-text-scale, 1));
    overflow-wrap: anywhere;
    word-break: break-word;
  }

  .health {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 5px;
    padding: 5px 8px;
    border: 1px solid color-mix(in srgb, currentColor 22%, transparent);
    border-radius: 999px;
    background: color-mix(in srgb, currentColor 8%, transparent);
    color: var(--secondary-text-color);
    font-size: calc(0.88rem * var(--card-text-scale, 1));
  }

  .health.good { color: var(--success-color, #43a047); }
  .health.bad { color: var(--error-color, #db4437); }
  .health.unavailable { color: var(--disabled-text-color); }

  .measurements {
    display: grid;
    grid-template-columns: repeat(var(--bars-per-row), minmax(0, 1fr));
    gap: 2px;
    padding: 8px;
  }

  .measurement {
    min-width: 0;
    margin: 3px;
    padding: 11px 10px 9px;
    border: 1px solid color-mix(in srgb, var(--primary-text-color) 8%, transparent);
    border-radius: 8px;
    background: color-mix(in srgb, var(--card-background-color) 86%, var(--primary-background-color));
  }

  .measurement.clickable {
    cursor: pointer;
  }

  .measurement.clickable:hover,
  .measurement.clickable:focus-visible {
    border-color: color-mix(in srgb, var(--primary-color) 45%, transparent);
    outline: none;
  }

  .measurement-heading,
  .value-line {
    display: flex;
    align-items: center;
    gap: 7px;
  }

  .measurement-heading {
    color: var(--secondary-text-color);
    font-size: calc(0.9rem * var(--card-text-scale, 1));
  }

  .measurement-heading ha-icon {
    color: #5f9168;
    --mdc-icon-size: 19px;
  }

  .measurement-heading span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .value-line {
    justify-content: space-between;
    margin-top: 8px;
  }

  .value {
    color: var(--primary-text-color);
    font-size: calc(1.1rem * var(--card-text-scale, 1));
    font-weight: 600;
  }

  .unit {
    color: var(--secondary-text-color);
    font-size: calc(0.84rem * var(--card-text-scale, 1));
    font-weight: 400;
  }

  .value-line > ha-icon {
    --mdc-icon-size: 18px;
  }

  .value-line > ha-icon.good { color: var(--success-color, #43a047); }
  .value-line > ha-icon.bad { color: var(--error-color, #db4437); }
  .value-line > ha-icon.unavailable { color: var(--disabled-text-color); }

  .meter {
    height: 7px;
    margin-top: 8px;
    overflow: hidden;
    border-radius: 3px;
    background: color-mix(in srgb, var(--divider-color) 72%, transparent);
  }

  .meter-fill {
    height: 100%;
    border-radius: inherit;
    transition: width 220ms ease;
  }

  .meter-fill.good { background: var(--success-color, #43a047); }
  .meter-fill.bad { background: var(--error-color, #db4437); }
  .meter-fill.unavailable { background: var(--disabled-text-color); }

  .range {
    display: flex;
    justify-content: space-between;
    margin-top: 5px;
    color: var(--secondary-text-color);
    font-size: calc(0.76rem * var(--card-text-scale, 1));
    opacity: 0.82;
  }

  .range b {
    margin-right: 2px;
    color: var(--primary-text-color);
    font-weight: 500;
  }

  .warning {
    padding: 16px;
    color: var(--secondary-text-color);
  }

  @media (max-width: 420px) {
    .measurements { grid-template-columns: 1fr; }
  }

  @media (max-width: 600px) {
    ha-card.text-size-small { --card-text-scale: 0.86; }
    ha-card.text-size-medium { --card-text-scale: 0.92; }
    ha-card.text-size-large { --card-text-scale: 1.02; }

    .header {
      gap: 9px;
      padding: 12px;
    }

    .heading {
      flex-basis: 100%;
    }

    .name {
      white-space: normal;
      overflow-wrap: anywhere;
    }

    .measurement {
      margin: 2px;
      padding: 9px 8px 8px;
    }

    .measurements {
      gap: 1px;
      padding: 6px;
    }
  }
`;
