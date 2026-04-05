from emoji import emojize
import random

co2_emissions = {'Sweden': 0.013, 'Lithuania': 0.018, 'France':	0.059, 'Austria': 0.085, 'Latvia': 0.105, 'Finland':	0.113, 'Slovakia':	0.132, 'Denmark':	0.166, 'Belgium': 0.17, 'Croatia':	0.21, 'Luxembourg': 0.219,
                 'Slovenia': 0.254, 'Italy':	0.256, 'Hungary': 0.26, 'Spain':	0.265, 'UnitedKingdom':	0.281, 'Romania':	0.306, 'Portugal':	0.325, 'Ireland': 0.425, 'Germany':	0.441, 'Bulgaria':	0.47, 'Netherlands':	0.505,
                 'Czechia':	0.513, 'Greece':	0.623, 'Malta':	0.648, 'Cyprus':	0.677, 'Poland':	0.773, 'Estonia':	0.819, 'Qatar': 0.596}
cost = {'Belgium': 0.28, 'Bulgaria': 0.10, 'Denmark': 0.30, 'Germany': 0.30, 'Estonia': 0.12, 'Finland': 0.16, 'France': 0.17, 'Greece': 0.19, 'Great Britain': 0.18, 'Ireland': 0.23, 'Italy': 0.21, 'Croatia': 0.12, 'Latvia': 0.16, 'Lithuania': 0.11, 'luxembourg': 0.16,
        'Malta': 0.13, 'Netherlands': 0.16, 'Norway': 0.16, 'Austria': 0.20, 'Poland': 0.15, 'Portugal': 0.23, 'Romania': 0.12, 'Sweden': 0.19, 'Slovakia': 14, 'Spain': 0.23, 'Czech Republic': 0.14, 'Hungary': 0.11, 'Cyprus': 0.19, 'Qatar': 0.115}

symbols = {'euro': '€', 'riyal': 'ر.ق'}


iconlist = {'runner_icon': emojize(":person_running:"),
            'bulb_icon': emojize(":light_bulb:"),
            'ac_icon': emojize(":snowflake:"),
            'sun_icon': emojize(":sun:"),
            'moneybag_icon': emojize(":money_bag:"),
            'seedling_icon': emojize(":seedling:"),
            'earth_africa_icon': emojize(":globe_showing_Europe-Africa:"),
            'car_icon': emojize(":automobile:"),
            'airplane_icon': emojize(":airplane:"),
            'bus_icon': emojize(":bus:"),
            'cyclone_icon': emojize(":cyclone:"),
            'electric_plug_icon': emojize(":electric_plug:"),
            'house_with_garden': emojize(":house_with_garden:")}

question_list = ['Do you want to turn off the Smart Plug? {icon_type}',
                 'Shall I turn off the Smart Plug for you? {icon_type}']


# Define MM Class Recommendations
MM_CLASS_RECOMMENDATIONS = {
    0: f"Energy saving mode is active. Keep doing the good work! {emojize(':sparkles:')} {emojize(':thumbs_up:')}",
    1: f"A device has been turned on. Keep an eye on usage! {emojize(':electric_plug:')} {emojize(':eyes:')}",
    2: f"A device has been turned off. Well done! {emojize(':check_mark_button:')} {emojize(':clapping_hands:')}",
    3: f"High power usage detected! Immediate action is recommended. {emojize(':warning:')} {emojize(':high_voltage:')}",
    4: f"It seems that you are out of the room and you forgot to turn off the Smart Plug. {emojize(':person_running:')} {emojize(':house_with_garden:')} {emojize(':alarm_clock:')}"
}


def get_mm_recommendation(mm_class):
    """
    Fetches the recommendation based on the MM class.
    """
    return MM_CLASS_RECOMMENDATIONS.get(mm_class, "No specific recommendation available.")


def generate_mm_message(mm_class, power_watt_per_sec, dev_name='Smart Plug', country='Qatar'):
    # Get class-based recommendation
    m1 = get_mm_recommendation(mm_class)

    # Get electricity cost per kWh and CO₂ per kWh
    price_per_kwh = cost.get(country, 0.2)  # fallback default
    co2_per_kwh = co2_emissions.get(country, 0.5)  # fallback default
    symbol = symbols['riyal'] if country == "Qatar" else symbols['euro']

    # Convert total energy to kWh
    power_kwh = (power_watt_per_sec * 3600) / 3600000  # W·s → kWh

    # Economic message
    total_cost = round(power_kwh * price_per_kwh, 4)
    m2 = f"That’s about an hourly cost of {total_cost}{symbol} for running the {dev_name}. {iconlist['moneybag_icon']}"

    # Environmental message
    total_co2 = round(power_kwh * co2_per_kwh, 3)
    km_equivalent = int(total_co2 / 0.04 * 100)  # car emits 4kg/100km

    m3 = f"The total hourly CO2 emissions from the {dev_name} is {total_co2}kg which corresponds to {km_equivalent}km by a car {iconlist['car_icon']}! {iconlist['seedling_icon']}{iconlist['earth_africa_icon']}"
    # m3 = f"That’s like driving {km_equivalent}km in a car in an hour — {total_co2}kg CO₂ released. {iconlist['car_icon']} {iconlist['seedling_icon']}"

    if mm_class == 3 or mm_class == 4:
        m4 = random.choice(question_list).format(
            icon_type=iconlist['electric_plug_icon'])
        # Combine the full message
        return f"{m1} {m4} {m2} {m3} "

    else:

        m4 = f"Keep using the plug to get energy saving recommendations! {emojize(':sparkles:')} {emojize(':thumbs_up:')}"
        # Combine the full message
        return f"{m1} {m2} {m3} {m4}"
