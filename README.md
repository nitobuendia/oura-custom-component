# Oura - Custom Component for Home-Assisant

This project is a custom component for [Home-Assistant](https://home-assistant.io).

The component sensors with sleep data for previous days from [Oura Ring](https://ouraring.com/).

## Installation

1. Copy the files from the `custom_component/oura/` folder into the `custom_component/oura/` of your Home-Assistant installation.

1. Configure the sensors following the instructions in `Configuration`.
1. Restart the Home-Assistant instance.

## Configuration

### Schema

```yaml
- platform: oura
  access_token:
  scan_interval:
  sensors:
    sleep:
      name:
      max_backfill:
      monitored_dates:
      monitored_variables:
```

### Parameters

* `access_token`: Personal Oura token. See `How to get personal Oura token` section for how to obtain this data.
* `scan_interval`: (Optional) Set how many seconds should pass in between refreshes. As the sleep data should only refresh once per day, we recommend to update every few hours (e.g. 7200 for 2h or 21600 for 6h).
* `sensors`: (Optional) Determines which sensors to import and its configuration.
  * `sleep`: (Optional) Configures sleep sensor. Default: sleep sensor is configured.
    * `name`: (Optional) Name of the sensor (e.g. sleep_quality). Default: oura_sleep.
    * `max_backfill`: How many days before to backfill if a day of data is not available. See `Backfilling strategy` section to understand how this parameter works. Default: 0.
    * `monitored_dates`: Days that you want to monitor. See `Monitored days` section under `Sleep Sensor` to understand what day values are supported. Default: yesterday.
    * `monitored_variables`: Variables that you want to monitor. See `Monitored attributes` section under `Sleep Sensor` to understand what variables are supported. Default: 'average_breath', 'average_heart_rate', 'awake_duration', 'bedtime_start_hour', 'bedtime_end_hour', 'day', 'deep_sleep_duration', 'in_bed_duration', 'light_sleep_duration', 'lowest_heart_rate', 'rem_sleep_duration', 'total_sleep_duration'.

### Example

```yaml
- platform: oura
  access_token: !secret oura_api_token
  scan_interval: 7200 # 2h = 2h * 60min * 60 seconds
  sensors:
    sleep:
      name: sleep_data
      max_backfill: 3
      monitored_dates:
        - yesterday
        - monday
        - tuesday
        - wednesday
        - thursday
        - friday
        - saturday
        - sunday
        - 8d_ago # Last week, +1 to compare to yesterday.
```

### How to get personal Oura token

The parameter `access_token` is provided by Oura. Read [this Oura documentation](https://cloud.ouraring.com/docs/authentication#personal-access-tokens) for more information on how to get
them.

This token is only valid for your personal data. If you need to access data from multiple users, you will need to configure multiple sensors.

## Sensors

### Sleep Sensor

#### State

The state of the sensor will show the **sleep efficiency** for the first selected day (recommended: yesterday).

#### Monitored days

This data can be retrieve for multiple days at once. The days supported are:

* `yesterday`: Previous day. This is the most recent data.
* `Xd_ago`: Number of days ago (e.g. 8d_ago ago to get the data of yesterday last week).
* `monday`, `tuesday`, ..., `sunday`: Previous days of the week.

#### Backfilling

##### What is Backfilling and why it is needed

Imagine you want to retrieve the previous day of data, but for some reason the data for that day does not exist. This would mean that the data would not be possible to be retrieved and will simply show unknown on the sensor.

This is frequent for `yesterday` as the data is not yet synced to the systems at midnight (you are still sleeping), but could happen for any day if you forgot to wear the ring. You may want this to stay like this or would prefer to backfill with the most relevant previous data. That process is called backfilling. This componenent allows to set a backfilling strategy:

##### Rule of thumb

The rule of thumb is that if backfilling is enabled, it will look for the previous day for `yesterday` and `Xd_ago` and for the previous week when using weekdays (e.g. `monday` or `thursday`).

##### Full backfilling logic

If you set the `max_backfill` value to `0`, there will never be backfill of data. If a day of data is not available, it will show unknown.

If you set the `max_backfill` value to any positive integer, then it will backfill like this:

* `Xd_ago`: If the data for X days ago is not available, looks for the day before. For example, if the setting is `8d_ago` and is not available, it will look for the data `9d_ago`. The number of previous days will depend on your backfill value. If the backfill is set to any value >1, it will check the value of previous day of data. If the data is found, then it will use this one. If not, it will continue as many times as the value of `max_backfill` (e.g. if the value is 3, it will check the 9d ago, then 10d ago, then 11d ago; it will stop as soon as one of these values is available (e.g. if 10d ago is available, it will not check 11d ago) and will return unknown if none of them has data).

* `yesterday`: Same as `Xd_ago`. If yesterday is not available, looks for previous day. The number of previous days will depend on your backfill value. If the backfill is set to any value >1, it will check the value of previous day of data (the day before yesterday). If the data is found, then it will use this one. If not, it will continue as many times as the value of `max_backfill` (e.g. if the value is 3, it will check the previous day, then the previous, then the previous; it will stop as soon as one of these values is available and will return unknown if none of them has data).

* `monday`, `tuesday`, ..., `sunday`: It works similar to `Xd_ago` except in that it looks for the previous week instead of previous day. For example, if last `monday` is not available, it will look for the `monday` of the previous week. If it's available, it will use it. If not, it will continue checking as many weeks back as the backfilling value.

#### Monitored attributes

The attributes will contain the daily data for the selected days and monitored variables.

The sleep sensor supports all the following monitored attributes:

* `day`: YYYY-MM-DD of the date of the data point.
* `average_breath`: Average breaths per minute (f.k.a `breath_average`).
* `average_heart_rate`: Average beats per minute of your heart (f.k.a `heart_rate_average`).
* `average_hrv`
* `awake_time`: Time awake in seconds.
* `awake_duration`: Time awake in hours. Derived from `awake_time`.
* `bedtime_end`: Timestamp at which you woke up from bed.
* `bedtime_end_hour`: Time (HH:MM) at which you woke up from bed.
* `bedtime_start`: Timestamp at which you went to bed.
* `bedtime_start_hour`: Time (HH:MM) at which you went to bed.
* `deep_sleep_duration`: Number of hours in deep sleep phase.
* `efficiency`: Sleep efficiency. Used as the state.
* `heart_rate`
* `hrv`
* `in_bed_duration`: Total hours in bed.
* `latency`
* `light_sleep_duration`: Number of hours in light sleep phase.
* `low_battery_alert`
* `lowest_heart_rate`: Beats per minute of your resting heart (f.k.a `resting_heart_rate`).
* `movement_30_sec`
* `period`
* `readiness_score_delta`
* `rem_sleep_duration`: Number of hours in REM sleep phase.
* `restless_periods`
* `sleep_phase_5_min`
* `sleep_score_delta`
* `time_in_bed`
* `total_sleep_duration`: Total hours of sleep.
* `type`: Type of sleep.

For a definition of all these variables, check [Oura's API](https://cloud.ouraring.com/v2/docs#operation/sleep_route_sleep_get).

Formerly supported variables that are no longe part of the API (i.e. not supported):

* `temperature_delta`: Delta temperature from sleeping to day.

#### Sample output

**State**: `48` (note: efficiency of yesterday, which was the first day configure on the example)

**Attributes**:

```json
yesterday: {
  "day": "2022-07-14",
  "bedtime_start_hour": "02:30",
  "bedtime_end_hour": "09:32",
  "average_breath": 14,
  "lowest_heart_rate": 44,
  "average_heart_rate": 47,
  "deep_sleep_duration": 0.72,
  "rem_sleep_duration": 0.32,
  "light_sleep_duration": 4.54,
  "total_sleep_duration": 5.58,
  "awake_duration": 1.45,
  "in_bed_duration": 7.03
}
8d_ago: {
  "day": "2022-07-07",
  "bedtime_start_hour": "23:29",
  "bedtime_end_hour": "08:05",
  "average_breath": 14,
  "lowest_heart_rate": 44,
  "average_heart_rate": 48,
  "deep_sleep_duration": 2.05,
  "rem_sleep_duration": 0.82,
  "light_sleep_duration": 4.29,
  "total_sleep_duration": 7.16,
  "awake_duration": 1.44,
  "in_bed_duration": 8.6
}
```

For full details on the exact schema of each variable, check [Oura API documentation](https://cloud.ouraring.com/v2/docs#operation/sleep_route_sleep_get).

### Derived sensors

While the component retrieves all the data for all the days in one same attribute data, you can re-use this data into template sensors. This is more efficient than creating multiple sensors with multiple API calls.

Example for breaking up yesterday's data into multiple sensors:

```yaml
- platform: template
  sensors:
    - name: "Sleep Breath Average Yesterday"
      unique_id: sleep_breath_average_yesterday
      unit_of_measurement: bpm
      state: >
        {{ states.sensor.sleep_quality.attributes.yesterday.average_breath }}
      icon: "mdi:lungs"

    - name: "Sleep Resting Heart Rate Yesterday"
      unique_id: sleep_resting_heart_rate_yesterday
      unit_of_measurement: "bpm"
      state: >
        {{ states.sensor.sleep_quality.attributes.yesterday.lowest_heart_rate }}
      icon: "mdi:heart-pulse"

    - name: "Resting Average Heart Rate Yesterday"
      unique_id: resting_heart_rate_average_yesterday
      unit_of_measurement: "bpm"
      state: >
        {{ states.sensor.sleep_quality.attributes.yesterday.average_heart_rate }}
      icon: "mdi:heart-pulse"

    - name: "Bed Time Yesterday"
      unique_id: bed_time_yesterday
      state: >
        {{ states.sensor.sleep_quality.attributes.yesterday.bedtime_start_hour }}
      icon: "mdi:sleep"

    - name: "Wake Time Yesterday"
      unique_id: wake_time_yesterday
      state: >
        {{ states.sensor.sleep_quality.attributes.yesterday.bedtime_end_hour }}
      icon: "mdi:sleep-off"

    - name: "Deep Sleep Yesterday"
      unique_id: deep_sleep_yesterday
      unit_of_measurement: h
      state: >
        {{ states.sensor.sleep_quality.attributes.yesterday.deep_sleep_duration }}
      icon: "mdi:bed"

    - name: "Rem Sleep Yesterday"
      unique_id: rem_sleep_yesterday
      unit_of_measurement: h
      state: >
        {{ states.sensor.sleep_quality.attributes.yesterday.rem_sleep_duration }}
      icon: "mdi:bed"

    - name: "Light Sleep Yesterday"
      unique_id: light_sleep_yesterday
      unit_of_measurement: h
      state: >
        {{ states.sensor.sleep_quality.attributes.yesterday.light_sleep_duration }}
      icon: "mdi:bed"

    - name: "Total Sleep Yesterday"
      unique_id: total_sleep_yesterday
      unit_of_measurement: h
      state: >
        {{ states.sensor.sleep_quality.attributes.yesterday.total_sleep_duration }}
      icon: "mdi:sleep"

    - name: "Time Awake Yesterday"
      unique_id: time_awake_yesterday
      unit_of_measurement: h
      state: >
        {{ states.sensor.sleep_quality.attributes.yesterday.awake_duration }}
      icon: "mdi:sleep-off"

    - name: "Time In Bed Yesterday"
      unique_id: time_in_bed_yesterday
      unit_of_measurement: h
      state: >
        {{ states.sensor.sleep_quality.attributes.yesterday.in_bed_duration }}
      icon: "mdi:bed"
```

## Sponsoring

If this is helpful, feel free to `Buy Me a Beer`; or check other options on the Github `❤️ Sponsor` link on the top of this page.

<a href="https://www.buymeacoffee.com/nitobuendia" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/arial-orange.png" alt="Buy Me A Coffee" style="height: 51px !important;width: 217px !important;" ></a>
