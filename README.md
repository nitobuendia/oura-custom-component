# Oura - Custom Component for Home-Assisant

This project is a custom component for [Home-Assistant](https://home-assistant.io).

The component sensors with sleep data for previous days from [Oura Ring](https://ouraring.com/).

## Installation

1. Copy the files from the `custom_component/oura/` folder into the `custom_component/oura/` of your Home-Assistant installation.

1. Configure the sensors following the instructions in `Configuration`.
1. Restart the Home-Assitant instance.

1. If the code was installed and configured properly, you will get a permanent notification. See `Notifications` section on the Home-Assistant menu.
1. Follow the link to Authorize Home-Assistant to access your Oura data. You may need to sign in and allow the data.
1. You will be redirected to Home-Assistant where the code information will be captured and exchanged for the token. If the redirect fails:
    *  Verify that your [http integration](https://www.home-assistant.io/integrations/http/) and base url are configured correctly.
    *  Verify that you have added your Home-Assistant URL to your Oura Application in the Redirect URIs, and it contains not just the domain/base url, but the full path (i.e. including `/oura/oauth/setup`). See `Configuration` > `How to get client id and client secret`.

1. Oura component will exchange the code for a token and update on the next schedule. If you want, you can force a sync from `Developer Tools` > `Services` > Service: `homeassistant.update_entity` + Entity: the Oura sensor and calling the service once (or twice after a break).
    *  If the entity is not updating, check your logs for any potential errors.


## Configuration

### Schema
```yaml
- platform: oura
  name:
  client_id:
  client_secret:
  scan_interval:
  max_backfill:
  monitored_variables:
```

### Parameters
* `name`: Name of the sensor (e.g. sleep_quality).
* `client_id`: Oura client id. See `How to get client id and client secret` section for how to obtain this data.
* `client_secret`: Oura client secret. See `How to get client id and client secret` section for how to obtain this data.
* `scan_interval`: (Optional) Set how many seconds should pass in between refreshes. As the sleep data should only refresh once per day, we recommend to update every few hours (e.g. 7200 for 2h or 21600 for 6h).
* `max_backfill`: How many days before to backfill if a day of data is not available. See `Backfilling strategy` section to understand how this parameter works.
* `monitored_variables`: Days that you want to monitor. See `Monitored Days` section to understand what day values are supported.

### Example
```yaml
- platform: oura
  name: sleep_quality
  client_id: !secret oura_client_id
  client_secret: !secret oura_client_secret
  scan_interval: 7200 # 2h = 2h * 60min * 60 seconds
  max_backfill: 3
  monitored_variables:
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

### How to get client id and client secret
The parameters `client_id` and `client_secret` are provided by Oura.

Read [Getting Started with the Oura Cloud API](https://cloud.ouraring.com/docs/) for more information on how to get them. Once you have created your application, add your Home-Assistant to Redirect URIs as follows:

`https://<url>:<port>/oura/oauth/setup`

Where:
* `https://` is the protocol. Change to `http` if you are not supporting http.s
* `<url>` is the URL of your Home-Assistant (e.g. `something.duckdns.org` or an IP like `192.168.1.123`)
* `<port>` is the port where your Home-Assistant is configured (`8123` by default).
* `/oura/oauth/setup` is the path that has been created by the custom_component. Do not change it and make sure you include it on the Redirect URis.

### Monitored Days
This data can be retrieve for multiple days at once. The days supported are:
* `yesterday`: Previous day. This is the most recent data.
* `Xd_ago`: Number of days ago (e.g. 8d_ago ago to get the data of yesterday last week).
* `monday`, `tuesday`, ..., `sunday`: Previous days of the week.

### Backfilling strategy
#### What is Backfilling and why it is needed
Imagine you want to retrieve the previous day of data, but for some reason the data for that day does not exist. This would mean that the data would not be possible to be retrieved and will simply show unknown on the sensor.

This is frequent for `yesterday` as the data is not yet synced to the systems at midnight (you are still sleeping), but could happen for any day if you forgot to wear the ring. You may want this to stay like this or would prefer to backfill with the most relevant previous data. That process is called backfilling. This componenent allows to set a backfilling strategy:

#### Rule of thumb

The rule of thumb is that if backfilling is enabled, it will look for the previous day for `yesterday` and `Xd_ago` and for the previous week when using weekdays (e.g. `monday` or `thursday`).

#### Full backfilling logic
If you set the `max_backfill` value to `0`, there will never be backfill of data. If a day of data is not available, it will show unknown.

If you set the `max_backfill` value to any positive integer, then it will backfill like this:

* `Xd_ago`: If the data for X days ago is not available, looks for the day before. For example, if the setting is `8d_ago` and is not available, it will look for the data `9d_ago`. The number of previous days will depend on your backfill value. If the backfill is set to any value >1, it will check the value of previous day of data. If the data is found, then it will use this one. If not, it will continue as many times as the value of `max_backfill` (e.g. if the value is 3, it will check the 9d ago, then 10d ago, then 11d ago; it will stop as soon as one of these values is available (e.g. if 10d ago is available, it will not check 11d ago) and will return unknown if none of them has data).

* `yesterday`: Same as `Xd_ago`. If yesterday is not available, looks for previous day. The number of previous days will depend on your backfill value. If the backfill is set to any value >1, it will check the value of previous day of data (the day before yesterday). If the data is found, then it will use this one. If not, it will continue as many times as the value of `max_backfill` (e.g. if the value is 3, it will check the previous day, then the previous, then the previous; it will stop as soon as one of these values is available and will return unknown if none of them has data).

* `monday`, `tuesday`, ..., `sunday`: It works similar to `Xd_ago` except in that it looks for the previous week instead of previous day. For example, if last `monday` is not available, it will look for the `monday` of the previous week. If it's available, it will use it. If not, it will continue checking as many weeks back as the backfilling value.

## What Data Can Be Retrieved

### State and Attributes
The state of the sensor will show the **sleep quality score** for the first selected day (recommended: yesterday).

### Attributes per Day
The attributes will contain the daily data for the selected days. In particular:
* `date`: YYYY-MM-DD of the date of the data point.
* `bedtime_start_hour`: Time at which you went to bed.
* `bedtime_end_hour`: Time at which you woke up from bed.
* `breath_average`: Average breaths per minute.
* `temperature_delta`: Delta temperature from sleeping to day.
* `resting_heart_rate`: Beats per minute of your resting heart.
* `heart_rate_average`: Average beats per minute of your heart.
* `deep_sleep_duration`: Number of hours in deep sleep phase.
* `rem_sleep_duration`: Number of hours in REM sleep phase.
* `light_sleep_duration`: Number of hours in light sleep phase.
* `total_sleep_duration`: Total hours of sleep.
* `awake_duration`: Total hours awake during the night.
* `in_bed_duration`: Total hours in bed.

### Sample output

**State**: `48` (note: sleep score of yesterday, which was the first day configure on the example)

**Attributes**:
```json
yesterday: {
  "date": "2020-01-04",
  "bedtime_start_hour": "02:30",
  "bedtime_end_hour": "09:32",
  "breath_average": 14,
  "temperature_delta": 0.43,
  "resting_heart_rate": 44,
  "heart_rate_average": 47,
  "deep_sleep_duration": 0.72,
  "rem_sleep_duration": 0.32,
  "light_sleep_duration": 4.54,
  "total_sleep_duration": 5.58,
  "awake_duration": 1.45,
  "in_bed_duration": 7.03
}
monday: {
  "date": "2019-12-30",
  "bedtime_start_hour": "01:24",
  "bedtime_end_hour": "08:30",
  "breath_average": 14,
  "temperature_delta": -0.1,
  "resting_heart_rate": 44,
  "heart_rate_average": 46,
  "deep_sleep_duration": 1.33,
  "rem_sleep_duration": 0.62,
  "light_sleep_duration": 3.84,
  "total_sleep_duration": 5.8,
  "awake_duration": 1.3,
  "in_bed_duration": 7.1
}
tuesday: {
  "date": "2019-12-31",
  "bedtime_start_hour": "04:22",
  "bedtime_end_hour": "11:24",
  "breath_average": 14,
  "temperature_delta": -0.18,
  "resting_heart_rate": 44,
  "heart_rate_average": 48,
  "deep_sleep_duration": 1.79,
  "rem_sleep_duration": 0.93,
  "light_sleep_duration": 3.12,
  "total_sleep_duration": 5.83,
  "awake_duration": 1.2,
  "in_bed_duration": 7.03
}
wednesday: {
  "date": "2020-01-01",
  "bedtime_start_hour": "01:37",
  "bedtime_end_hour": "07:45",
  "breath_average": 14,
  "temperature_delta": -0.79,
  "resting_heart_rate": 40,
  "heart_rate_average": 44,
  "deep_sleep_duration": 2.09,
  "rem_sleep_duration": 0.32,
  "light_sleep_duration": 2.92,
  "total_sleep_duration": 5.33,
  "awake_duration": 0.8,
  "in_bed_duration": 6.13
}
thursday: {
  "date": "2020-01-02",
  "bedtime_start_hour": "02:00",
  "bedtime_end_hour": "08:15",
  "breath_average": 14,
  "temperature_delta": 0.01,
  "resting_heart_rate": 45,
  "heart_rate_average": 48,
  "deep_sleep_duration": 1.14,
  "rem_sleep_duration": 0.78,
  "light_sleep_duration": 3.38,
  "total_sleep_duration": 5.29,
  "awake_duration": 0.96,
  "in_bed_duration": 6.25
}
friday: {
  "date": "2020-01-03",
  "bedtime_start_hour": "00:43",
  "bedtime_end_hour": "11:32",
  "breath_average": 14,
  "temperature_delta": 0.49,
  "resting_heart_rate": 47,
  "heart_rate_average": 49,
  "deep_sleep_duration": 1.75,
  "rem_sleep_duration": 1.82,
  "light_sleep_duration": 4.96,
  "total_sleep_duration": 8.53,
  "awake_duration": 2.28,
  "in_bed_duration": 10.82
}
saturday: {
  "date": "2020-01-04",
  "bedtime_start_hour": "02:30",
  "bedtime_end_hour": "09:32",
  "breath_average": 14,
  "temperature_delta": 0.43,
  "resting_heart_rate": 44,
  "heart_rate_average": 47,
  "deep_sleep_duration": 0.72,
  "rem_sleep_duration": 0.32,
  "light_sleep_duration": 4.54,
  "total_sleep_duration": 5.58,
  "awake_duration": 1.45,
  "in_bed_duration": 7.03
}
sunday: {
  "date": "2019-12-29",
  "bedtime_start_hour": "01:18",
  "bedtime_end_hour": "08:35",
  "breath_average": 14,
  "temperature_delta": -0.34,
  "resting_heart_rate": 44,
  "heart_rate_average": 45,
  "deep_sleep_duration": 1.77,
  "rem_sleep_duration": 0.42,
  "light_sleep_duration": 3.63,
  "total_sleep_duration": 5.83,
  "awake_duration": 1.46,
  "in_bed_duration": 7.28
}
8d_ago: {
  "date": "2019-12-25",
  "bedtime_start_hour": "23:29",
  "bedtime_end_hour": "08:05",
  "breath_average": 14,
  "temperature_delta": -0.31,
  "resting_heart_rate": 44,
  "heart_rate_average": 48,
  "deep_sleep_duration": 2.05,
  "rem_sleep_duration": 0.82,
  "light_sleep_duration": 4.29,
  "total_sleep_duration": 7.16,
  "awake_duration": 1.44,
  "in_bed_duration": 8.6
}
```

### Derived sensors

While the component retrieves all the data for all the days in one same attribute data, you can re-use this data into template sensors. This is more efficient than creating multiple sensors with multiple API calls.


Example for breaking up yesterday's data into multiple sensors:
```yaml
- platform: template
  sensors:
    sleep_breath_average_yesterday:
      entity_id: sensor.sleep_quality
      friendly_name: "Sleep Breath Average Yesterday"
      unit_of_measurement: bpm
      value_template: >
        {{ states.sensor.sleep_quality.attributes.yesterday.breath_average }}
      icon_template: "mdi:lungs"

    sleep_temperature_delta_yesterday:
      entity_id: sensor.sleep_quality
      friendly_name: "Sleep Temperature Delta Yesterday"
      unit_of_measurement: "°C"
      value_template: >
        {{ states.sensor.sleep_quality.attributes.yesterday.temperature_delta }}
      icon_template: "mdi:thermometer-lines"

    sleep_resting_heart_rate_yesterday:
      entity_id: sensor.sleep_quality
      friendly_name: "Resting Heart Rate Yesterday"
      unit_of_measurement: "bpm"
      value_template: >
        {{ states.sensor.sleep_quality.attributes.yesterday.resting_heart_rate }}
      icon_template: "mdi:heart-pulse"

    resting_heart_rate_average_yesterday:
      entity_id: sensor.sleep_quality
      friendly_name: "Average Heart Rate Yesterday"
      unit_of_measurement: "bpm"
      value_template: >
        {{ states.sensor.sleep_quality.attributes.yesterday.heart_rate_average }}
      icon_template: "mdi:heart-pulse"

    bedtime_start_hour_yesterday:
      entity_id: sensor.sleep_quality
      friendly_name: "Bed Time Yesterday"
      value_template: >
        {{ states.sensor.sleep_quality.attributes.yesterday.bedtime_start_hour }}
      icon_template: "mdi:sleep"

    bedtime_end_hour_yesterday:
      entity_id: sensor.sleep_quality
      friendly_name: "Wake Time Yesterday"
      value_template: >
        {{ states.sensor.sleep_quality.attributes.yesterday.bedtime_end_hour }}
      icon_template: "mdi:sleep-off"

    deep_sleep_yesterday:
      entity_id: sensor.sleep_quality
      friendly_name: "Deep Sleep Yesterday"
      unit_of_measurement: h
      value_template: >
        {{ states.sensor.sleep_quality.attributes.yesterday.deep_sleep_duration }}
      icon_template: "mdi:hotel"

    rem_sleep_yesterday:
      entity_id: sensor.sleep_quality
      friendly_name: "Rem Sleep Yesterday"
      unit_of_measurement: h
      value_template: >
        {{ states.sensor.sleep_quality.attributes.yesterday.rem_sleep_duration }}
      icon_template: "mdi:hotel"

    light_sleep_yesterday:
      entity_id: sensor.sleep_quality
      friendly_name: "Light Sleep Yesterday"
      unit_of_measurement: h
      value_template: >
        {{ states.sensor.sleep_quality.attributes.yesterday.light_sleep_duration }}
      icon_template: "mdi:hotel"

    total_sleep_yesterday:
      entity_id: sensor.sleep_quality
      friendly_name: "Total Sleep Yesterday"
      unit_of_measurement: h
      value_template: >
        {{ states.sensor.sleep_quality.attributes.yesterday.total_sleep_duration }}
      icon_template: "mdi:sleep"

    time_awake_yesterday:
      entity_id: sensor.sleep_quality
      friendly_name: "Time Awake Yesterday"
      unit_of_measurement: h
      value_template: >
        {{ states.sensor.sleep_quality.attributes.yesterday.awake_duration }}
      icon_template: "mdi:sleep-off"

    time_in_bed_yesterday:
      entity_id: sensor.sleep_quality
      friendly_name: "Time In Bed Yesterday"
      unit_of_measurement: h
      value_template: >
        {{ states.sensor.sleep_quality.attributes.yesterday.in_bed_duration }}
      icon_template: "mdi:hotel"
```

## Sponsoring
If this is helpful, feel free to `Buy Me a Beer`; or check other options on the Github `❤️ Sponsor` link on the top of this page.


<a href="https://www.buymeacoffee.com/nitobuendia" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/arial-orange.png" alt="Buy Me A Coffee" style="height: 51px !important;width: 217px !important;" ></a>
