# Examples

Replace entity IDs with the entities Home Assistant created for your projector.

## Automations

### Turn Projector On

```yaml
automation:
  - alias: "Turn projector on for movie night"
    trigger:
      - trigger: time
        at: "19:00:00"
    action:
      - action: media_player.turn_on
        target:
          entity_id: media_player.vpl_vw285es_projector
```

### Select HDMI 1 After Startup

```yaml
automation:
  - alias: "Select projector HDMI 1 when on"
    trigger:
      - trigger: state
        entity_id: sensor.vpl_vw285es_power_status
        to: "on"
    action:
      - action: media_player.select_source
        target:
          entity_id: media_player.vpl_vw285es_projector
        data:
          source: hdmi1
```

### Notify If Projector Is Cooling

```yaml
automation:
  - alias: "Projector cooling notification"
    trigger:
      - trigger: state
        entity_id: sensor.vpl_vw285es_power_status
        to:
          - "cooling"
          - "cooling2"
    action:
      - action: notify.notify
        data:
          title: "Projector cooling"
          message: "The projector is cooling down. Avoid removing power."
```

### Turn Projector Off at Night

```yaml
automation:
  - alias: "Turn projector off late"
    trigger:
      - trigger: time
        at: "23:30:00"
    condition:
      - condition: state
        entity_id: media_player.vpl_vw285es_projector
        state: "on"
    action:
      - action: media_player.turn_off
        target:
          entity_id: media_player.vpl_vw285es_projector
```

## Dashboard Cards

### Projector Controls

```yaml
type: media-control
entity: media_player.vpl_vw285es_projector
```

### Projector Status

```yaml
type: entities
title: Sony Projector
entities:
  - entity: media_player.vpl_vw285es_projector
  - entity: sensor.vpl_vw285es_power_status
  - entity: sensor.vpl_vw285es_lamp_timer
```

### Power State History

```yaml
type: history-graph
title: Projector Power Status
entities:
  - entity: sensor.vpl_vw285es_power_status
hours_to_show: 24
```

## Related Documentation

- [Configuration Reference](./CONFIGURATION.md)
- [Getting Started](./GETTING_STARTED.md)
