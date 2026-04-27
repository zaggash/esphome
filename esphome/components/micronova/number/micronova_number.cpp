#include "micronova_number.h"
#include <algorithm>
#include <cmath>

namespace esphome::micronova {

static const char *const TAG = "micronova.number";

void MicroNovaNumber::dump_config() {
  LOG_NUMBER("", "Micronova number", this);
  this->dump_base_config();
  if (this->multiply_ != 1.0f) {
    ESP_LOGCONFIG(TAG, "  Multiply: %.3f", this->multiply_);
  }
  if (this->offset_ != 0.0f) {
    ESP_LOGCONFIG(TAG, "  Offset: %.3f", this->offset_);
  }
}

void MicroNovaNumber::process_value_from_stove(int value_from_stove) {
  if (value_from_stove == -1) {
    this->publish_state(NAN);
    return;
  }

  float new_value = static_cast<float>(value_from_stove);
  if (this->use_step_scaling_) {
    new_value *= this->traits.get_step();
  } else {
    new_value = new_value * this->multiply_ + this->offset_;
  }
  this->publish_state(new_value);
}

void MicroNovaNumber::control(float value) {
  uint8_t new_number;
  if (this->use_step_scaling_) {
    new_number = static_cast<uint8_t>(value / this->traits.get_step());
  } else {
    float scaled = (value - this->offset_) / this->multiply_;
    long rounded = lroundf(scaled);
    long clamped = std::clamp(rounded, 0L, 255L);
    if (clamped != rounded) {
      ESP_LOGW(TAG, "Value %.3f out of byte range after transform; clamped to %ld", value, clamped);
    }
    new_number = static_cast<uint8_t>(clamped);
  }
  this->micronova_->queue_write_command(this->memory_location_, this->memory_address_, new_number);
}

}  // namespace esphome::micronova
