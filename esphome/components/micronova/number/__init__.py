import esphome.codegen as cg
from esphome.components import number
import esphome.config_validation as cv
from esphome.const import (
    CONF_MAX_VALUE,
    CONF_MIN_VALUE,
    CONF_MULTIPLY,
    CONF_OFFSET,
    CONF_STEP,
    DEVICE_CLASS_TEMPERATURE,
    UNIT_CELSIUS,
)

from .. import (
    CONF_MICRONOVA_ID,
    MICRONOVA_ADDRESS_SCHEMA,
    MicroNova,
    MicroNovaListener,
    micronova_ns,
    register_micronova_writer,
    to_code_micronova_listener,
)

ICON_FLASH = "mdi:flash"

CONF_THERMOSTAT_TEMPERATURE = "thermostat_temperature"
CONF_POWER_LEVEL = "power_level"
CONF_MEMORY_ADDRESS_NUMBER = "memory_address_number"

MicroNovaNumber = micronova_ns.class_(
    "MicroNovaNumber", number.Number, MicroNovaListener
)


def _validate_memory_address_number_entry(config):
    if config[CONF_MAX_VALUE] <= config[CONF_MIN_VALUE]:
        raise cv.Invalid("max_value must be greater than min_value")
    if config[CONF_MULTIPLY] == 0.0:
        raise cv.Invalid(
            "multiply must be non-zero — use offset alone for additive-only transforms"
        )
    return config


_MEMORY_ADDRESS_NUMBER_SCHEMA = cv.All(
    number.number_schema(MicroNovaNumber)
    .extend(MICRONOVA_ADDRESS_SCHEMA(is_polling_component=True))
    .extend(
        {
            cv.Required(CONF_MIN_VALUE): cv.float_,
            cv.Required(CONF_MAX_VALUE): cv.float_,
            cv.Required(CONF_STEP): cv.positive_float,
            cv.Optional(CONF_MULTIPLY, default=1.0): cv.float_,
            cv.Optional(CONF_OFFSET, default=0.0): cv.float_,
        }
    ),
    _validate_memory_address_number_entry,
)

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_MICRONOVA_ID): cv.use_id(MicroNova),
        cv.Optional(CONF_THERMOSTAT_TEMPERATURE): number.number_schema(
            MicroNovaNumber,
            unit_of_measurement=UNIT_CELSIUS,
            device_class=DEVICE_CLASS_TEMPERATURE,
        )
        .extend(
            MICRONOVA_ADDRESS_SCHEMA(
                default_memory_location=0x20,
                default_memory_address=0x7D,
                is_polling_component=True,
            )
        )
        .extend(
            {
                cv.Optional(CONF_STEP, default=1.0): cv.float_range(min=0.1, max=10.0),
            }
        ),
        cv.Optional(CONF_POWER_LEVEL): number.number_schema(
            MicroNovaNumber,
            icon=ICON_FLASH,
        ).extend(
            MICRONOVA_ADDRESS_SCHEMA(
                default_memory_location=0x20,
                default_memory_address=0x7F,
                is_polling_component=True,
            )
        ),
        cv.Optional(CONF_MEMORY_ADDRESS_NUMBER): cv.ensure_list(
            _MEMORY_ADDRESS_NUMBER_SCHEMA
        ),
    }
)


async def to_code(config):
    mv = await cg.get_variable(config[CONF_MICRONOVA_ID])

    if thermostat_temperature_config := config.get(CONF_THERMOSTAT_TEMPERATURE):
        register_micronova_writer()
        numb = await number.new_number(
            thermostat_temperature_config,
            mv,
            min_value=0,
            max_value=40,
            step=thermostat_temperature_config.get(CONF_STEP),
        )
        await to_code_micronova_listener(mv, numb, thermostat_temperature_config)
        cg.add(numb.set_use_step_scaling(True))

    if power_level_config := config.get(CONF_POWER_LEVEL):
        register_micronova_writer()
        numb = await number.new_number(
            power_level_config,
            mv,
            min_value=1,
            max_value=5,
            step=1,
        )
        await to_code_micronova_listener(mv, numb, power_level_config)
