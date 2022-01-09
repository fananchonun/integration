import {
  LitElement,
  customElement,
  CSSResultArray,
  TemplateResult,
  html,
  css,
  property
} from "lit-element";

import { HomeAssistant } from "custom-card-helpers";
import { HacsStyle } from "../style/hacs-style"

import "../misc/CustomRepositories"

import { Configuration, Repository } from "../types"

@customElement("hacs-panel-settings")
export class HacsPanelSettings extends LitElement {
  @property()
  public hass!: HomeAssistant;

  @property()
  public repositories!: Repository[]

  @property()
  public configuration!: Configuration

  @property()
  private ActiveSpinnerReload: boolean

  @property()
  private ActiveSpinnerUpgradeAll: boolean

  ResetSpinner() {
    this.ActiveSpinnerReload = false;
    this.ActiveSpinnerUpgradeAll = false;
  }

  render(): TemplateResult | void {
    return html`

    <ha-card header="${this.hass.localize("component.hacs.config.title")}">
      <div class="card-content">
        <p><b>${this.hass.localize("component.hacs.common.version")}:</b> ${this.configuration.version}</p>
        <p><b>${this.hass.localize("component.hacs.common.repositories")}:</b> ${this.repositories.length}</p>
        <div class="version-available">
        <paper-dropdown-menu label="${this.hass.localize(`component.hacs.settings.display`)}">
            <paper-listbox slot="dropdown-content" selected="-1">
              <paper-item .display="grid" @click="${this.SetFeStyleGrid}">
                ${this.hass.localize(`component.hacs.settings.grid`)}
              </paper-item>
              <paper-item .display="table" @click="${this.SetFeStyleTable}">
                ${this.hass.localize(`component.hacs.settings.table`)}
              </paper-item>
            </paper-listbox>
        </paper-dropdown-menu>
    </div>
      </div>
      <div class="card-actions">

      <mwc-button raised @click=${this.ReloadData}>
        ${(this.ActiveSpinnerReload ? html`<paper-spinner active></paper-spinner>` : html`
        ${this.hass.localize(`component.hacs.settings.reload_data`)}
        `)}
      </mwc-button>

      <mwc-button raised @click=${this.UpgradeAll}>
        ${(this.ActiveSpinnerUpgradeAll ? html`<paper-spinner active></paper-spinner>` : html`
        ${this.hass.localize(`component.hacs.settings.upgrade_all`)}
        `)}
      </mwc-button>

      <a href="https://github.com/custom-components/hacs" target="_blank" rel="noreferrer">
        <mwc-button raised>
          ${this.hass.localize(`component.hacs.settings.hacs_repo`)}
        </mwc-button>
      </a>

      <a href="https://github.com/custom-components/hacs/issues" target="_blank" rel="noreferrer">
        <mwc-button raised>
          ${this.hass.localize(`component.hacs.repository.open_issue`)}
        </mwc-button>
      </a>
      </div>
    </ha-card>
    <hacs-custom-repositories
      .hass=${this.hass}
      .configuration=${this.configuration}
      .repositories=${this.repositories}
    >
    </hacs-custom-repositories>
          `;
  }

  SetFeStyleGrid() {
    this.hass.connection.sendMessage({
      type: "hacs/settings",
      action: "set_fe_grid"
    });
  }

  SetFeStyleTable() {
    this.hass.connection.sendMessage({
      type: "hacs/settings",
      action: "set_fe_table"
    });
  }

  ReloadData() {
    this.ActiveSpinnerReload = true;
    console.log("This should reload data, but that is not added.")
  }

  UpgradeAll() {
    this.ActiveSpinnerReload = true;
    console.log("This should reload data, but that is not added.")
  }

  static get styles(): CSSResultArray {
    return [HacsStyle, css`
    ha-card {
      width: 90%;
      margin-left: 5%;
    }
    mwc-button {
      margin: 0 8px 0 8px;
    }
    `]
  }
}