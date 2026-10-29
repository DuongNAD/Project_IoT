#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <SoftwareSerial.h>

// Khai báo chân Bluetooth: RX = D2, TX = D3
SoftwareSerial BT(2, 3); 

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

// Xung tối thiểu và tối đa cho MG996R (ở tần số 50Hz)
#define SERVOMIN  125 // ~0 độ
#define SERVOMAX  575 // ~180 độ
#define STEP        5 // Mỗi lần bấm phím quay 5 độ

// Góc ban đầu khi mới khởi động (vị trí an toàn)
int angleBase     = 90; // Kênh 0: Đế (a / d)
int angleShoulder = 90; // Kênh 1: Cánh tay (w / s)
int angleElbow    = 90; // Kênh 2: Khuỷu tay (i / k)
int angleGrip     = 95; // Kênh 3: Kẹp (j: mở ra, l: kẹp vào)

// === [THÊM MỚI 1/3] Biến thời gian để gửi góc servo định kỳ lên Laptop qua USB ===
unsigned long lastReportMs = 0;

// Hàm đổi góc sang xung PWM gửi đến PCA9685
void setServoAngle(uint8_t channel, int angle) {
  int pulse = map(angle, 0, 180, SERVOMIN, SERVOMAX);
  pwm.setPWM(channel, 0, pulse);
}

// === [THÊM MỚI 2/3] Hàm gửi gói JSON trạng thái 4 servo qua cáp USB lên Laptop ===
void sendServoState() {
  Serial.print("{\"t\":");
  Serial.print(millis());
  Serial.print(",\"servo\":[");
  Serial.print(angleBase);     Serial.print(",");
  Serial.print(angleShoulder); Serial.print(",");
  Serial.print(angleElbow);    Serial.print(",");
  Serial.print(angleGrip);
  Serial.println("]}");
}

void setup() {
  Serial.begin(9600);
  BT.begin(9600); // Tốc độ mặc định của HC-05

  pwm.begin();
  pwm.setPWMFreq(50); // Tần số 50Hz cho servo RC

  // Đưa toàn bộ cánh tay về góc mặc định
  setServoAngle(0, angleBase);
  setServoAngle(1, angleShoulder);
  setServoAngle(2, angleElbow);
  setServoAngle(3, angleGrip);

  delay(500);
  Serial.println("Robot Arm Ready! WASD + IK + JL");
  sendServoState();
}

void loop() {
  // === [THÊM MỚI 3/3] Nhận lệnh từ cả Bluetooth (BT) lẫn cáp USB (Serial) ===
  char cmd = 0;
  if (BT.available()) {
    cmd = BT.read();
  } else if (Serial.available()) {
    cmd = Serial.read();
  }

  if (cmd != 0 && cmd != '\n' && cmd != '\r') {
    Serial.print("Phím bấm: ");
    Serial.println(cmd);

    switch (cmd) {
      // --- 1. Đế xoay: a (Trái) / d (Phải) ---
      case 'a': case 'A': 
        angleBase = constrain(angleBase + STEP, 0, 180); 
        break;
      case 'd': case 'D': 
        angleBase = constrain(angleBase - STEP, 0, 180); 
        break;

      // --- 2. Cánh tay nâng hạ: w (Lên) / s (Xuống) ---
      case 'w': case 'W': 
        angleShoulder = constrain(angleShoulder + STEP, 25, 155); 
        break;
      case 's': case 'S': 
        angleShoulder = constrain(angleShoulder - STEP, 25, 155); 
        break;

      // --- 3. Khuỷu tay: i (Gập lên) / k (Gập xuống) ---
      case 'i': case 'I': 
        angleElbow = constrain(angleElbow + STEP, 25, 155); 
        break;
      case 'k': case 'K': 
        angleElbow = constrain(angleElbow - STEP, 25, 155); 
        break;

      // --- 4. Kẹp gắp: j (Mở ra) / l (Kẹp vào) ---
      case 'j': case 'J': 
        angleGrip = constrain(angleGrip - STEP, 95, 175); // Mở rộng dần
        break;
      case 'l': case 'L': 
        angleGrip = constrain(angleGrip + STEP, 95, 175); // Kẹp chặt dần
        break;

      // --- 5. Phím 'h' (Home): Đưa toàn bộ về vị trí an toàn ban đầu ---
      case 'h': case 'H':
        angleBase = 90; angleShoulder = 90; angleElbow = 90; angleGrip = 95;
        break;
    }

    // Cập nhật lại góc đến 4 servo
    setServoAngle(0, angleBase);
    setServoAngle(1, angleShoulder);
    setServoAngle(2, angleElbow);
    setServoAngle(3, angleGrip);

    // Gửi ngay góc mới lên Laptop
    sendServoState();
    lastReportMs = millis();
  }

  // Định kỳ mỗi 200ms (5Hz) gửi trạng thái góc lên Laptop để đồng bộ giao diện
  if (millis() - lastReportMs >= 200) {
    lastReportMs = millis();
    sendServoState();
  }
}
