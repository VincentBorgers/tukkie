import SectionCard from "./SectionCard";

function groupDevices(devices) {
  return {
    lights: devices.filter((device) => device.type === "light"),
    climate: devices.filter((device) => device.type === "thermostat"),
    access: devices.filter((device) => device.type === "doorbell" || device.type === "intercom")
  };
}

export default function DeviceControls({ devices = [], onRunTool, busyAction }) {
  const grouped = groupDevices(devices);

  return (
    <SectionCard title="Apparaatbediening" kicker="Veilige tools">
      <div className="space-y-5">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-ink/40">Verlichting</p>
          <div className="mt-3 space-y-3">
            {grouped.lights.map((device) => (
              <div key={device.id} className="rounded-[24px] bg-white/70 p-4 shadow-sm">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <h3 className="text-sm font-semibold text-ink">{device.name}</h3>
                    <p className="text-xs text-ink/60">
                      {device.state.power === "on" ? "Aan" : "Uit"} · helderheid {device.state.brightness ?? "-"}%
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      className="soft-button"
                      disabled={busyAction === `${device.id}-on`}
                      onClick={() => onRunTool("lights_control", { device_id: device.id, action: "on" }, `${device.id}-on`)}
                    >
                      Aan
                    </button>
                    <button
                      type="button"
                      className="soft-button"
                      disabled={busyAction === `${device.id}-dim`}
                      onClick={() =>
                        onRunTool(
                          "lights_control",
                          { device_id: device.id, action: "brightness", brightness: 20 },
                          `${device.id}-dim`
                        )
                      }
                    >
                      Dim 20%
                    </button>
                    <button
                      type="button"
                      className="soft-button"
                      disabled={busyAction === `${device.id}-off`}
                      onClick={() => onRunTool("lights_control", { device_id: device.id, action: "off" }, `${device.id}-off`)}
                    >
                      Uit
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-ink/40">Klimaat</p>
          <div className="mt-3 space-y-3">
            {grouped.climate.map((device) => (
              <div key={device.id} className="rounded-[24px] bg-white/70 p-4 shadow-sm">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <h3 className="text-sm font-semibold text-ink">{device.name}</h3>
                    <p className="text-xs text-ink/60">Doeltemperatuur {device.state.target_celsius ?? "-"}°C</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      className="soft-button"
                      onClick={() =>
                        onRunTool(
                          "temperature_control",
                          { device_id: device.id, target_celsius: 22 },
                          `${device.id}-22`
                        )
                      }
                    >
                      22°C
                    </button>
                    <button
                      type="button"
                      className="soft-button"
                      onClick={() =>
                        onRunTool(
                          "temperature_control",
                          { device_id: device.id, target_celsius: 19 },
                          `${device.id}-19`
                        )
                      }
                    >
                      19°C
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-[24px] bg-ink/5 p-4">
          <p className="text-xs uppercase tracking-[0.3em] text-ink/40">Toegang en status</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {grouped.access.map((device) => (
              <span key={device.id} className="rounded-full bg-white px-3 py-2 text-sm text-ink/80">
                {device.name}
              </span>
            ))}
            <button
              type="button"
              className="primary-button !py-3"
              onClick={() => onRunTool("network_monitor", { include_anomaly_detection: true }, "network-monitor")}
            >
              Scan netwerk
            </button>
          </div>
        </div>
      </div>
    </SectionCard>
  );
}
