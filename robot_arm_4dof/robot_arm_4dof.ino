#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <SoftwareSerial.h>

// Khai báo chân Bluetooth: RX = D2, TX = D3
SoftwareSerial BT(2, 3);

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

// Xung tối thiểu và tối đa cho MG996R (ở tần số 50Hz)
#define SERVOMIN  125 // ~0 độ
#define SERVOMAX  575 // ~180 độ
#define STEP_ARM    2 // Đế / vai / khuỷu: mỗi lần bấm quay 2 độ (nhỏ để căn chính xác; MG996R còn phân biệt được từ khoảng 1 độ)
#define STEP_GRIP   5 // Kẹp: mỗi lần bấm vẫn quay 5 độ

// === [CHỐNG NÓNG SERVO KẸP - KÊNH 3] ===
// Servo bị chặn cứng (kẹt vào vật, hoặc chạm chốt chặn cuối) vẫn bị ép về góc mục tiêu nên hút dòng lớn
// liên tục và nóng lên. Xung 575 (~2.8 ms) còn vượt dải 0.5-2.5 ms của MG996R, nên kẹp ở 175° là ép vào chốt chặn.
#define GRIP_CH              3
#define GRIP_OPEN_ANGLE     95      // Mở hết cỡ (giới hạn dưới của servo kẹp)
#define GRIP_CLOSE_LIMIT   160      // Kẹp sâu nhất (xung ~2.56 ms). Đo thực tế 2026-11-02: ở 150° khe giữa hai ngón chỉ bằng bề rộng cốc (~3.9 cm) nên không siết được, cần ~160°. Chủ máy đồng ý nâng từ 150 lên 160; trước đó 175 (~2.74 ms, vượt dải servo) làm servo nóng. Vẫn có tự nhả xung sau GRIP_HOLD_MAX_MS
#define GRIP_IDLE_RELAX_MS  5000UL  // Kẹp mở hết cỡ (đúng GRIP_OPEN_ANGLE) mà 5 giây không có lệnh kẹp: ngắt xung PWM cho servo nguội
#define GRIP_HOLD_MAX_MS   60000UL  // Đã khép kẹp (góc > GRIP_OPEN_ANGLE) quá 60 giây không có lệnh kẹp: nhả xung PWM (vật có thể tuột)

// Góc ban đầu khi mới khởi động (vị trí an toàn)
int angleBase     = 0; // Kênh 0: Đế (a: sang trái / d: sang phải). Home 0° = quay hết sang phải để cánh tay không che vật ở cam TRÊN
int angleShoulder = 90; // Kênh 1: Cánh tay (w / s)
int angleElbow    = 90; // Kênh 2: Khuỷu tay (i / k)
int angleGrip     = GRIP_OPEN_ANGLE; // Kênh 3: Kẹp (j: mở ra, l: kẹp vào)

// Biến thời gian để gửi góc servo định kỳ lên Laptop qua USB
unsigned long lastReportMs = 0;

// Trạng thái nghỉ của servo kẹp: true = đã ngắt xung PWM kênh 3 (servo không còn ép, đang nguội)
bool gripRelaxed = false;
unsigned long gripActiveMs = 0; // Lần cuối ra lệnh cho servo kẹp

// Hàm đổi góc sang xung PWM gửi đến PCA9685
void setServoAngle(uint8_t channel, int angle) {
  int pulse = map(angle, 0, 180, SERVOMIN, SERVOMAX);
  pwm.setPWM(channel, 0, pulse);
}

// Cấp xung cho servo kẹp tại góc hiện tại và tính lại thời gian chờ nghỉ
void driveGripper() {
  setServoAngle(GRIP_CH, angleGrip);
  gripRelaxed = false;
  gripActiveMs = millis();
}

// Ngắt hẳn xung PWM kênh kẹp (PCA9685: OFF = 4096 là "luôn tắt"), servo hết ép nên nguội dần
void relaxGripper() {
  pwm.setPWM(GRIP_CH, 0, 4096);
  gripRelaxed = true;
}

// Gửi gói JSON 4 góc servo qua cáp USB lên Laptop: {"servo":[đế,vai,khuỷu,kẹp]}
void sendServoState() {
  Serial.print("{\"servo\":[");
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
  driveGripper();

  sendServoState();
}

void loop() {
  // Nhận lệnh từ cả Bluetooth (BT) lẫn cáp USB (Serial)
  char cmd = 0;
  if (BT.available()) {
    cmd = BT.read();
  } else if (Serial.available()) {
    cmd = Serial.read();
  }

  if (cmd != 0) {
    bool validCmd = true;
    bool gripCmd = false; // true nếu lệnh này đổi góc kẹp -> cấp lại xung cho servo kẹp

    switch (cmd) {
      // --- 1. Đế xoay: a (Trái) / d (Phải) ---
      case 'a': case 'A':
        angleBase = constrain(angleBase + STEP_ARM, 0, 180);
        break;
      case 'd': case 'D':
        angleBase = constrain(angleBase - STEP_ARM, 0, 180);
        break;

      // --- 2. Cánh tay nâng hạ: w (Lên) / s (Xuống) ---
      case 'w': case 'W':
        angleShoulder = constrain(angleShoulder + STEP_ARM, 25, 155);
        break;
      case 's': case 'S':
        angleShoulder = constrain(angleShoulder - STEP_ARM, 25, 155);
        break;

      // --- 3. Khuỷu tay: i (Gập lên) / k (Gập xuống) ---
      case 'i': case 'I':
        angleElbow = constrain(angleElbow + STEP_ARM, 25, 155);
        break;
      case 'k': case 'K':
        angleElbow = constrain(angleElbow - STEP_ARM, 25, 155);
        break;

      // --- 4. Kẹp gắp: j (Mở ra) / l (Kẹp vào) ---
      case 'j': case 'J':
        angleGrip = constrain(angleGrip - STEP_GRIP, GRIP_OPEN_ANGLE, GRIP_CLOSE_LIMIT); // Mở rộng dần
        gripCmd = true;
        break;
      case 'l': case 'L':
        angleGrip = constrain(angleGrip + STEP_GRIP, GRIP_OPEN_ANGLE, GRIP_CLOSE_LIMIT); // Kẹp chặt dần
        gripCmd = true;
        break;

      // --- 5. Phím 'h' (Home): Đưa toàn bộ về vị trí an toàn ban đầu ---
      case 'h': case 'H':
        angleBase = 0; angleShoulder = 90; angleElbow = 90; angleGrip = GRIP_OPEN_ANGLE;  // Đế quay hết sang phải (0°): không che vật ở cam TRÊN
        gripCmd = true;
        break;

      default:
        validCmd = false;
        break;
    }

    if (validCmd) {
      // Cập nhật lại góc đến 3 servo đế, vai, khuỷu
      setServoAngle(0, angleBase);
      setServoAngle(1, angleShoulder);
      setServoAngle(2, angleElbow);
      // Servo kẹp đang nghỉ thì lệnh đế / vai / khuỷu không đánh thức nó
      if (gripCmd) {
        driveGripper();
      }

      // Gửi ngay góc mới lên Laptop
      sendServoState();
      lastReportMs = millis();
    }
  }

  // Tự nhả xung servo kẹp: mở hết cỡ thì sau 5 giây, đã khép (giữ vật) thì sau 60 giây không có lệnh kẹp.
  // Vật rộng 50-60 mm chỉ cần khép 5-10° nên "đang giữ" là MỌI góc lớn hơn góc mở hết cỡ, không dùng vùng đệm.
  if (!gripRelaxed) {
    bool holding = angleGrip > GRIP_OPEN_ANGLE;
    unsigned long limitMs = holding ? GRIP_HOLD_MAX_MS : GRIP_IDLE_RELAX_MS;
    if (millis() - gripActiveMs >= limitMs) {
      relaxGripper();
    }
  }

  // Định kỳ mỗi 200ms (5Hz) gửi trạng thái góc lên Laptop để đồng bộ giao diện
  if (millis() - lastReportMs >= 200) {
    lastReportMs = millis();
    sendServoState();
  }
}
