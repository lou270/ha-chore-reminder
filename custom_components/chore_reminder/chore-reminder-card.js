/**
 * Chore Reminder Card
 * Custom Lovelace card for Home Assistant
 * Displays chores sorted by urgency with inline completion buttons.
 */

class ChoreReminderCard extends HTMLElement {

    static get properties() {
        return {
            hass: {},
            config: {},
        };
    }

    setConfig(config) {
        this.config = {
            title: config.title || "📋 Mes Corvées",
            max_items: config.max_items || 20,
            show_completed: config.show_completed !== undefined ? config.show_completed : false,
            ...config,
        };
        this._render();
    }

    set hass(hass) {
        this._hass = hass;
        this._render();
    }

    _getChores() {
        if (!this._hass) return [];

        const entities = Object.keys(this._hass.states);
        const sensors = entities.filter(
            (e) =>
                e.startsWith("sensor.") &&
                this._hass.states[e].attributes &&
                this._hass.states[e].attributes.last_completed !== undefined &&
                this._hass.states[e].attributes.next_due !== undefined
        );

        const chores = sensors.map((sensorId) => {
            const state = this._hass.states[sensorId];
            const daysRemaining = parseInt(state.state, 10);

            // Find matching button via device registry
            const deviceId = this._getDeviceId(sensorId);
            const buttonId = deviceId ? this._findButtonForDevice(deviceId) : null;

            // Get entity picture or icon
            const entityPicture = state.attributes.entity_picture || null;
            const icon = state.attributes.icon || "mdi:broom";

            return {
                sensorId,
                buttonId,
                name: state.attributes.friendly_name || sensorId,
                daysRemaining: isNaN(daysRemaining) ? 999 : daysRemaining,
                lastCompleted: state.attributes.last_completed,
                nextDue: state.attributes.next_due,
                entityPicture,
                icon,
            };
        });

        // Sort by days remaining (most urgent first)
        chores.sort((a, b) => a.daysRemaining - b.daysRemaining);

        // Filter out completed if needed
        const filtered = this.config.show_completed
            ? chores
            : chores;

        return filtered.slice(0, this.config.max_items);
    }

    _getDeviceId(entityId) {
        // Access the entity registry to find the device_id
        if (this._hass && this._hass.entities && this._hass.entities[entityId]) {
            return this._hass.entities[entityId].device_id;
        }
        return null;
    }

    _findButtonForDevice(deviceId) {
        if (!this._hass || !this._hass.entities) return null;

        for (const [entityId, entity] of Object.entries(this._hass.entities)) {
            if (
                entityId.startsWith("button.") &&
                entity.device_id === deviceId
            ) {
                return entityId;
            }
        }
        return null;
    }

    _getStatusColor(daysRemaining) {
        if (daysRemaining <= 0) return "var(--error-color, #db4437)";
        if (daysRemaining <= 2) return "var(--warning-color, #ffa726)";
        return "var(--success-color, #43a047)";
    }

    _getStatusLabel(daysRemaining) {
        if (daysRemaining < 0) return `${Math.abs(daysRemaining)}j de retard`;
        if (daysRemaining === 0) return "Aujourd'hui";
        if (daysRemaining === 1) return "Demain";
        return `${daysRemaining}j`;
    }

    _completeChore(buttonId) {
        if (!this._hass || !buttonId) return;
        this._hass.callService("button", "press", {
            entity_id: buttonId,
        });
    }

    _render() {
        if (!this.config) return;

        const chores = this._getChores();

        this.innerHTML = `
      <ha-card>
        <style>
          .card-header-custom {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 16px 8px;
            font-size: 1.1em;
            font-weight: 500;
            color: var(--primary-text-color);
          }
          .card-header-custom .count {
            font-size: 0.75em;
            color: var(--secondary-text-color);
            font-weight: 400;
          }
          .chore-list {
            padding: 0 8px 8px;
          }
          .chore-item {
            display: flex;
            align-items: center;
            padding: 10px 8px;
            border-radius: 12px;
            margin-bottom: 4px;
            transition: background-color 0.2s ease;
            gap: 12px;
          }
          .chore-item:hover {
            background-color: var(--secondary-background-color, rgba(0,0,0,0.05));
          }
          .chore-icon-wrapper {
            flex-shrink: 0;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
          }
          .chore-icon-wrapper img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 50%;
          }
          .chore-icon-wrapper ha-icon {
            --mdc-icon-size: 22px;
          }
          .chore-info {
            flex: 1;
            min-width: 0;
          }
          .chore-name {
            font-size: 0.95em;
            font-weight: 500;
            color: var(--primary-text-color);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
          .chore-due {
            font-size: 0.8em;
            color: var(--secondary-text-color);
            margin-top: 2px;
          }
          .chore-badge {
            flex-shrink: 0;
            padding: 4px 10px;
            border-radius: 16px;
            font-size: 0.78em;
            font-weight: 600;
            color: white;
            min-width: 40px;
            text-align: center;
          }
          .chore-complete-btn {
            flex-shrink: 0;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            border: 2px solid var(--divider-color, #e0e0e0);
            background: transparent;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            color: var(--secondary-text-color);
          }
          .chore-complete-btn:hover {
            border-color: var(--success-color, #43a047);
            background: var(--success-color, #43a047);
            color: white;
            transform: scale(1.1);
          }
          .chore-complete-btn ha-icon {
            --mdc-icon-size: 20px;
          }
          .empty-state {
            padding: 32px 16px;
            text-align: center;
            color: var(--secondary-text-color);
            font-size: 0.9em;
          }
          .empty-state ha-icon {
            --mdc-icon-size: 48px;
            margin-bottom: 8px;
            display: block;
            opacity: 0.5;
          }
          .overdue .chore-name {
            color: var(--error-color, #db4437);
          }
        </style>

        <div class="card-header-custom">
          <span>${this.config.title}</span>
          <span class="count">${chores.length} tâche${chores.length !== 1 ? "s" : ""}</span>
        </div>

        <div class="chore-list">
          ${chores.length === 0
                ? `
            <div class="empty-state">
              <ha-icon icon="mdi:check-all"></ha-icon>
              Toutes les tâches sont à jour !
            </div>
          `
                : chores
                    .map(
                        (chore, index) => `
              <div class="chore-item ${chore.daysRemaining <= 0 ? "overdue" : ""}" data-index="${index}">
                <div class="chore-icon-wrapper" style="background-color: ${this._getStatusColor(chore.daysRemaining)}22;">
                  ${chore.entityPicture
                                ? `<img src="${chore.entityPicture}" alt="" />`
                                : `<ha-icon icon="${chore.icon}" style="color: ${this._getStatusColor(chore.daysRemaining)};"></ha-icon>`
                            }
                </div>
                <div class="chore-info">
                  <div class="chore-name">${chore.name}</div>
                  <div class="chore-due">Prochaine échéance</div>
                </div>
                <div class="chore-badge" style="background-color: ${this._getStatusColor(chore.daysRemaining)};">
                  ${this._getStatusLabel(chore.daysRemaining)}
                </div>
                ${chore.buttonId
                                ? `<button class="chore-complete-btn" data-button-id="${chore.buttonId}" title="Marquer comme fait">
                        <ha-icon icon="mdi:check"></ha-icon>
                       </button>`
                                : ""
                            }
              </div>
            `
                    )
                    .join("")
            }
        </div>
      </ha-card>
    `;

        // Attach click listeners
        this.querySelectorAll(".chore-complete-btn").forEach((btn) => {
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                const buttonId = btn.getAttribute("data-button-id");
                this._completeChore(buttonId);

                // Visual feedback
                btn.style.borderColor = "var(--success-color, #43a047)";
                btn.style.background = "var(--success-color, #43a047)";
                btn.style.color = "white";
                btn.innerHTML = '<ha-icon icon="mdi:check-bold"></ha-icon>';
            });
        });
    }

    getCardSize() {
        const chores = this._getChores();
        return 1 + chores.length;
    }

    static getStubConfig() {
        return {
            title: "📋 Mes Corvées",
            max_items: 10,
        };
    }
}

customElements.define("chore-reminder-card", ChoreReminderCard);

// Register card in the Lovelace card picker
window.customCards = window.customCards || [];
window.customCards.push({
    type: "chore-reminder-card",
    name: "Chore Reminder Card",
    description: "Affiche vos corvées triées par urgence avec bouton de validation.",
    preview: true,
});

console.info(
    "%c CHORE-REMINDER-CARD %c Loaded ",
    "color: white; background: #43a047; font-weight: bold; padding: 2px 6px; border-radius: 4px 0 0 4px;",
    "color: #43a047; background: #e8f5e9; font-weight: bold; padding: 2px 6px; border-radius: 0 4px 4px 0;"
);
